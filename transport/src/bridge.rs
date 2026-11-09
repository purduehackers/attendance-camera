use crate::{namespace, protocol::*, redis_client, secret};
use anyhow::{Result, ensure};
use axum::{
    Router, body::Body, extract::State, http::header, response::IntoResponse, routing::get,
};
use base64::{Engine, engine::general_purpose::STANDARD};
use bytes::Bytes;
use futures_util::StreamExt;
use redis::{Client, aio::ConnectionManager};
use std::{collections::VecDeque, convert::Infallible, net::SocketAddr, time::Duration};
use tokio::{
    sync::broadcast,
    time::{sleep, timeout},
};

#[derive(Clone)]
enum Video {
    Data(Bytes),
    Reset,
}

pub async fn run() -> Result<()> {
    let client = redis_client()?;
    let prefix = namespace()?;
    let token = secret("ATTENDANCE_TOKEN")?;
    let address: SocketAddr = std::env::var("BRIDGE_BIND")
        .unwrap_or_else(|_| "127.0.0.1:18555".into())
        .parse()?;
    ensure!(address.ip().is_loopback(), "Bridge must listen on loopback");
    let backend =
        std::env::var("ATTENDANCE_BACKEND").unwrap_or_else(|_| "http://127.0.0.1:8000".into());
    let url = url::Url::parse(&backend)?;
    ensure!(
        url.scheme() == "http"
            && matches!(url.host_str(), Some("127.0.0.1" | "[::1]"))
            && url.path() == "/"
            && url.query().is_none(),
        "Backend must be a loopback HTTP origin"
    );
    let (video, _) = broadcast::channel(128);
    let app = Router::new()
        .route("/cam.ts", get(camera))
        .route("/healthz", get(|| async { "ok" }))
        .with_state(video.clone());
    let listener = tokio::net::TcpListener::bind(address).await?;
    let video_task = tokio::spawn(video_loop(client.clone(), prefix.clone(), video));
    let rpc_task = tokio::spawn(request_loop(client, prefix, backend, token));
    tokio::select! {
        result = axum::serve(listener, app) => { result?; },
        result = video_task => { result??; },
        result = rpc_task => { result??; },
        _ = tokio::signal::ctrl_c() => {},
    }
    Ok(())
}

async fn camera(State(video): State<broadcast::Sender<Video>>) -> impl IntoResponse {
    let mut receiver = video.subscribe();
    let stream = async_stream::stream! {
        while let Ok(Ok(Video::Data(data))) = timeout(Duration::from_secs(3), receiver.recv()).await {
            yield Ok::<_, Infallible>(data);
        }
        // Missing bytes, slow decoder, or outage closes this response. PyAV reconnects
        // and increments its generation, so occupancy is marked as needing reconciliation.
    };
    (
        [
            (header::CONTENT_TYPE, "video/mp2t"),
            (header::CACHE_CONTROL, "no-store"),
        ],
        Body::from_stream(stream),
    )
}

async fn video_loop(client: Client, prefix: String, video: broadcast::Sender<Video>) -> Result<()> {
    let mut sequence = Sequence::default();
    loop {
        let result: Result<()> = async {
            let mut subscriber = client.get_async_pubsub().await?;
            subscriber.subscribe(format!("{prefix}:video")).await?;
            let mut connection = ConnectionManager::new(client.clone()).await?;
            let mut messages = subscriber.on_message();
            while let Some(message) = messages.next().await {
                let data = message.get_payload_bytes();
                let Ok((ack, created)) = decode(data) else {
                    continue;
                };
                if now_ms().abs_diff(created) > 3_000 {
                    let _ = video.send(Video::Reset);
                    continue;
                }
                match sequence.accept(ack) {
                    Delivery::Retired => continue,
                    Delivery::Duplicate => {}
                    delivery => {
                        if delivery == Delivery::Reset {
                            let _ = video.send(Video::Reset);
                        }
                        let _ = video.send(Video::Data(Bytes::copy_from_slice(&data[HEADER..])));
                    }
                }
                let _: usize = timeout(
                    Duration::from_secs(2),
                    redis::cmd("PUBLISH")
                        .arg(format!("{prefix}:ack"))
                        .arg(serde_json::to_vec(&ack)?)
                        .query_async(&mut connection),
                )
                .await??;
            }
            anyhow::bail!("Redis subscription ended");
        }
        .await;
        if result.is_err() {
            let _ = video.send(Video::Reset);
            eprintln!("video subscription disconnected; reconnecting");
            sleep(Duration::from_secs(1)).await;
        }
    }
}

async fn request_loop(
    client: Client,
    prefix: String,
    backend: String,
    token: String,
) -> Result<()> {
    let http = reqwest::Client::builder()
        .timeout(Duration::from_secs(4))
        .redirect(reqwest::redirect::Policy::none())
        .build()?;
    let mut cache: VecDeque<(uuid::Uuid, u64, Reply)> = VecDeque::new();
    loop {
        let result: Result<()> = async {
            let mut subscriber = client.get_async_pubsub().await?;
            subscriber.subscribe(format!("{prefix}:requests")).await?;
            let mut connection = ConnectionManager::new(client.clone()).await?;
            let mut messages = subscriber.on_message();
            while let Some(message) = messages.next().await {
                if message.get_payload_bytes().len() > MAX_REQUEST * 2 {
                    continue;
                }
                let Ok(request) = serde_json::from_slice::<Request>(message.get_payload_bytes())
                else {
                    continue;
                };
                if !allowed(&request.method, &request.path) {
                    continue;
                }
                while cache
                    .front()
                    .is_some_and(|(_, time, _)| now_ms().saturating_sub(*time) > 60_000)
                    || cache.len() >= 128
                {
                    cache.pop_front();
                }
                let reply = if let Some((_, _, reply)) =
                    cache.iter().find(|(id, _, _)| *id == request.id)
                {
                    reply.clone()
                } else {
                    let reply = if now_ms().abs_diff(request.created) > 8_000 {
                        unavailable("Request expired before execution.")
                    } else {
                        forward(&http, &backend, &token, &request)
                            .await
                            .unwrap_or_else(|_| unavailable("Attendance worker is unavailable."))
                    };
                    cache.push_back((request.id, now_ms(), reply.clone()));
                    reply
                };
                let _: usize = timeout(
                    Duration::from_secs(2),
                    redis::cmd("PUBLISH")
                        .arg(format!("{prefix}:reply:{}", request.id))
                        .arg(serde_json::to_vec(&reply)?)
                        .query_async(&mut connection),
                )
                .await??;
            }
            anyhow::bail!("Redis subscription ended");
        }
        .await;
        if result.is_err() {
            eprintln!("control subscription disconnected; reconnecting");
            sleep(Duration::from_secs(1)).await;
        }
    }
}

fn unavailable(message: &str) -> Reply {
    Reply {
        status: 503,
        content_type: "application/json".into(),
        body: STANDARD.encode(serde_json::json!({"detail": message}).to_string()),
    }
}

async fn forward(
    http: &reqwest::Client,
    backend: &str,
    token: &str,
    request: &Request,
) -> Result<Reply> {
    let body = STANDARD.decode(&request.body)?;
    ensure!(body.len() <= MAX_REQUEST, "Request too large");
    let response = http
        .request(
            request.method.parse()?,
            format!("{backend}{}", request.path),
        )
        .basic_auth("organizer", Some(token))
        .header("content-type", "application/json")
        .body(body)
        .send()
        .await?;
    let status = response.status().as_u16();
    let content_type = response
        .headers()
        .get("content-type")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("text/plain")
        .to_owned();
    let mut stream = response.bytes_stream();
    let mut bytes = Vec::new();
    while let Some(chunk) = stream.next().await {
        let chunk = chunk?;
        ensure!(
            bytes.len() + chunk.len() <= MAX_RESPONSE,
            "Response too large"
        );
        bytes.extend_from_slice(&chunk);
    }
    Ok(Reply {
        status,
        content_type,
        body: STANDARD.encode(bytes),
    })
}
