use crate::{
    auth::{Auth, Callback},
    namespace,
    protocol::*,
    redis_client, secret,
};
use anyhow::Result;
use axum::{
    Router,
    body::{Body, Bytes, to_bytes},
    extract::{
        Query, Request as HttpRequest, State, WebSocketUpgrade,
        ws::{Message, WebSocket},
    },
    http::{HeaderMap, StatusCode, header},
    middleware::{self, Next},
    response::{IntoResponse, Redirect, Response},
    routing::{get, post},
};
use base64::{Engine, engine::general_purpose::STANDARD};
use futures_util::{SinkExt, StreamExt};
use redis::{Client, aio::ConnectionManager};
use std::{sync::Arc, time::Duration};
use subtle::ConstantTimeEq;
use tokio::{
    sync::Semaphore,
    time::{Instant, timeout},
};
use uuid::Uuid;

#[derive(Clone)]
struct Relay {
    client: Client,
    connection: ConnectionManager,
    namespace: String,
    ingest_auth: String,
    auth: Auth,
    origin: String,
    lifetime: Duration,
    requests: Arc<Semaphore>,
}

pub async fn router() -> Result<Router> {
    let client = redis_client()?;
    let connection = ConnectionManager::new(client.clone()).await?;
    let origin = std::env::var("PUBLIC_ORIGIN")?;
    let parsed = url::Url::parse(&origin)?;
    anyhow::ensure!(
        parsed.origin().ascii_serialization() == origin,
        "PUBLIC_ORIGIN must be an origin without a trailing slash"
    );
    let state = Relay {
        client,
        connection,
        namespace: namespace()?,
        ingest_auth: format!("Bearer {}", secret("CAMERA_TOKEN")?),
        auth: Auth::new(&origin, &namespace()?)?,
        origin,
        lifetime: Duration::from_secs(
            std::env::var("RELAY_SESSION_SECONDS")
                .ok()
                .and_then(|v| v.parse().ok())
                .unwrap_or(240)
                .clamp(2, 240),
        ),
        requests: Arc::new(Semaphore::new(16)),
    };
    Ok(Router::new()
        .route("/healthz", get(|| async { "ok" }))
        .route("/ingest", get(ingest))
        .route("/api/auth/login", get(login))
        .route("/api/auth/callback/purduehackers", get(callback))
        .route("/api/auth/logout", post(logout))
        .fallback(api)
        .layer(middleware::from_fn_with_state(state.clone(), access))
        .with_state(state))
}

fn error(status: StatusCode, message: &'static str) -> Response {
    (status, axum::Json(serde_json::json!({"detail": message}))).into_response()
}

async fn access(State(state): State<Relay>, request: HttpRequest, next: Next) -> Response {
    let mut response = authorize(state, request, next).await;
    for (name, value) in [
        ("cache-control", "no-store"),
        ("x-content-type-options", "nosniff"),
        ("referrer-policy", "no-referrer"),
        (
            "content-security-policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; style-src-attr 'unsafe-inline'; font-src 'self' https://components.purduehackers.com; img-src 'self' blob:; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'self'",
        ),
    ] {
        response.headers_mut().insert(
            axum::http::HeaderName::from_static(name),
            value.parse().unwrap(),
        );
    }
    response
}

async fn authorize(mut state: Relay, request: HttpRequest, next: Next) -> Response {
    let path = request.uri().path();
    let mutation = !matches!(request.method().as_str(), "GET" | "HEAD");
    // Browser mutations require our exact origin. The publisher is a token-authenticated client.
    if (mutation
        && request
            .headers()
            .get(header::ORIGIN)
            .is_none_or(|v| v != state.origin.as_str()))
        || ((mutation || path == "/ingest")
            && (request
                .headers()
                .get(header::ORIGIN)
                .is_some_and(|v| v != state.origin.as_str())
                || request
                    .headers()
                    .get("sec-fetch-site")
                    .is_some_and(|v| v == "cross-site")))
    {
        return error(
            StatusCode::FORBIDDEN,
            "Cross-origin changes are not allowed.",
        );
    }
    let public = matches!(
        path,
        "/healthz" | "/login" | "/api/auth/login" | "/api/auth/callback/purduehackers"
    ) || path.starts_with("/_astro/");
    if path == "/ingest" {
        let supplied = request
            .headers()
            .get(header::AUTHORIZATION)
            .map(|v| v.as_bytes())
            .unwrap_or_default();
        if !bool::from(state.ingest_auth.as_bytes().ct_eq(supplied)) {
            return error(StatusCode::UNAUTHORIZED, "Authentication required.");
        }
    } else if !public {
        match state
            .auth
            .authenticated(request.headers(), &mut state.connection)
            .await
        {
            Ok(true) => {}
            Ok(false) if path == "/" => return Redirect::to("/login").into_response(),
            Ok(false) => return error(StatusCode::UNAUTHORIZED, "Sign in with Purdue Hackers ID."),
            Err(_) => {
                return error(
                    StatusCode::SERVICE_UNAVAILABLE,
                    "Sign-in service is temporarily unavailable.",
                );
            }
        }
    }
    next.run(request).await
}

async fn login(State(mut state): State<Relay>) -> Response {
    match state.auth.login(&mut state.connection).await {
        Ok(response) => response,
        Err(_) => Redirect::to("/login?reason=unavailable").into_response(),
    }
}

async fn callback(
    State(mut state): State<Relay>,
    Query(query): Query<Callback>,
    headers: HeaderMap,
) -> Response {
    state
        .auth
        .callback(query, &headers, &mut state.connection)
        .await
}

async fn logout(State(mut state): State<Relay>, headers: HeaderMap) -> Response {
    match state.auth.logout(&headers, &mut state.connection).await {
        Ok(response) => response,
        Err(_) => error(
            StatusCode::SERVICE_UNAVAILABLE,
            "Sign-out failed. Please try again.",
        ),
    }
}

static WEB: include_dir::Dir<'_> = include_dir::include_dir!("$CARGO_MANIFEST_DIR/web/built");

async fn ingest(State(state): State<Relay>, ws: WebSocketUpgrade) -> Response {
    ws.max_message_size(MAX_FRAME)
        .max_frame_size(MAX_FRAME)
        .on_upgrade(move |socket| async move {
            if ingest_connection(state, socket).await.is_err() {
                // Errors may contain credentials or video bytes; log neither.
                eprintln!("camera connection ended; publisher will reconnect");
            }
        })
}

async fn ingest_connection(state: Relay, mut socket: WebSocket) -> Result<()> {
    let mut subscriber = state.client.get_async_pubsub().await?;
    subscriber
        .subscribe(format!("{}:ack", state.namespace))
        .await?;
    let mut messages = subscriber.on_message();
    let mut connection = state.connection;
    let end = tokio::time::sleep(state.lifetime);
    tokio::pin!(end);
    let mut ping = tokio::time::interval(Duration::from_secs(10));
    let mut seen = Instant::now();
    let mut stream = None;
    // Allow a short replay burst, while bounding a faulty publisher to 32 Mbit/s.
    let mut window = Instant::now();
    let mut window_bytes = 0;
    loop {
        tokio::select! {
            _ = &mut end => { let _ = socket.close().await; return Ok(()); },
            _ = ping.tick() => {
                anyhow::ensure!(seen.elapsed() < Duration::from_secs(30), "Publisher timed out");
                timeout(Duration::from_secs(3), socket.send(Message::Ping(Bytes::new()))).await??;
            },
            incoming = socket.recv() => match incoming {
                Some(Ok(Message::Binary(data))) => {
                    seen = Instant::now();
                    let (ack, _) = decode(&data)?;
                    stream = Some(ack.stream);
                    if window.elapsed() >= Duration::from_secs(1) { window = Instant::now(); window_bytes = 0; }
                    window_bytes += data.len();
                    anyhow::ensure!(window_bytes <= 4 * 1024 * 1024, "Publisher rate exceeded");
                    let _: usize = timeout(Duration::from_secs(2), redis::cmd("PUBLISH")
                        .arg(format!("{}:video", state.namespace)).arg(data.as_ref())
                        .query_async(&mut connection)).await??;
                },
                Some(Ok(Message::Pong(_))) | Some(Ok(Message::Ping(_))) => seen = Instant::now(),
                Some(Ok(Message::Close(_))) | None => return Ok(()),
                _ => anyhow::bail!("Invalid publisher message"),
            },
            message = messages.next() => {
                let message = message.ok_or_else(|| anyhow::anyhow!("Redis subscription ended"))?;
                let bytes = message.get_payload_bytes();
                anyhow::ensure!(bytes.len() <= 256, "Invalid acknowledgement");
                if let Ok(ack) = serde_json::from_slice::<Ack>(bytes)
                    && Some(ack.stream) == stream {
                    timeout(Duration::from_secs(3), socket.send(Message::Text(serde_json::to_string(&ack)?.into()))).await??;
                }
            }
        }
    }
}

async fn api(State(state): State<Relay>, request: HttpRequest) -> Response {
    let method = request.method().as_str().to_owned();
    let path = request.uri().path().to_owned();
    if method == "GET" || method == "HEAD" {
        let asset = match path.as_str() {
            "/" => "index.html",
            "/login" => "login/index.html",
            other if other.starts_with("/_astro/") => &other[1..],
            _ => "",
        };
        if let Some(file) = WEB.get_file(asset) {
            let kind = if asset.ends_with(".html") {
                "text/html; charset=utf-8"
            } else if asset.ends_with(".css") {
                "text/css; charset=utf-8"
            } else if asset.ends_with(".js") {
                "text/javascript; charset=utf-8"
            } else {
                "application/octet-stream"
            };
            let body = if method == "HEAD" {
                &[][..]
            } else {
                file.contents()
            };
            return ([(header::CONTENT_TYPE, kind)], body).into_response();
        }
    }
    if !allowed(&method, &path) || request.uri().query().is_some() {
        return error(StatusCode::NOT_FOUND, "Endpoint not found.");
    }
    let Ok(_permit) = state.requests.clone().try_acquire_owned() else {
        return error(StatusCode::TOO_MANY_REQUESTS, "Too many requests.");
    };
    let Ok(body) = to_bytes(request.into_body(), MAX_REQUEST).await else {
        return error(StatusCode::PAYLOAD_TOO_LARGE, "Request too large.");
    };
    let request = Request {
        id: Uuid::new_v4(),
        method,
        path,
        body: STANDARD.encode(body),
        created: now_ms(),
    };
    match timeout(Duration::from_secs(8), rpc(&state, &request)).await {
        Ok(Ok(reply)) => {
            let Ok(body) = STANDARD.decode(reply.body) else {
                return error(StatusCode::BAD_GATEWAY, "Invalid worker response.");
            };
            if body.len() > MAX_RESPONSE {
                return error(StatusCode::BAD_GATEWAY, "Worker response too large.");
            }
            let status = StatusCode::from_u16(reply.status).unwrap_or(StatusCode::BAD_GATEWAY);
            let mut headers = HeaderMap::new();
            let kind = match reply.content_type.split(';').next() {
                Some("application/json") => "application/json",
                Some("image/jpeg") => "image/jpeg",
                Some("text/csv") => "text/csv; charset=utf-8",
                _ => "text/plain; charset=utf-8",
            };
            headers.insert(header::CONTENT_TYPE, kind.parse().unwrap());
            if kind.starts_with("text/csv") {
                headers.insert(
                    header::CONTENT_DISPOSITION,
                    "attachment; filename=\"attendance-counts.csv\""
                        .parse()
                        .unwrap(),
                );
            }
            (status, headers, Body::from(body)).into_response()
        }
        _ => error(
            StatusCode::SERVICE_UNAVAILABLE,
            "Attendance server is disconnected. Try again shortly.",
        ),
    }
}

async fn rpc(state: &Relay, request: &Request) -> Result<Reply> {
    let mut subscriber = state.client.get_async_pubsub().await?;
    subscriber
        .subscribe(format!("{}:reply:{}", state.namespace, request.id))
        .await?;
    let listeners: usize = redis::cmd("PUBLISH")
        .arg(format!("{}:requests", state.namespace))
        .arg(serde_json::to_vec(request)?)
        .query_async(&mut state.connection.clone())
        .await?;
    anyhow::ensure!(listeners > 0, "Worker offline");
    let message = subscriber
        .on_message()
        .next()
        .await
        .ok_or_else(|| anyhow::anyhow!("Redis disconnected"))?;
    anyhow::ensure!(
        message.get_payload_bytes().len() < MAX_RESPONSE * 2,
        "Reply too large"
    );
    Ok(serde_json::from_slice(message.get_payload_bytes())?)
}
