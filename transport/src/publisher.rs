use crate::{protocol::*, secret};
use anyhow::{Result, ensure};
use bytes::Bytes;
use futures_util::{SinkExt, StreamExt};
use std::{collections::VecDeque, process::Stdio, sync::Arc, time::Duration};
use tokio::{
    io::AsyncReadExt,
    process::Command,
    sync::Mutex,
    time::{Instant, sleep, timeout},
};
use tokio_tungstenite::{
    connect_async,
    tungstenite::{Message, client::IntoClientRequest},
};
use uuid::Uuid;

const MAX_BUFFER: usize = 4 * 1024 * 1024;

#[derive(Default)]
struct Replay {
    frames: VecDeque<(Ack, Instant, Bytes)>,
    bytes: usize,
}

impl Replay {
    fn push(&mut self, data: Bytes) {
        let ack = decode(&data).expect("locally encoded packet").0;
        self.bytes += data.len();
        self.frames.push_back((ack, Instant::now(), data));
        self.expire();
    }
    fn expire(&mut self) {
        while self.bytes > MAX_BUFFER
            || self
                .frames
                .front()
                .is_some_and(|(_, time, _)| time.elapsed().as_millis() > u128::from(REPLAY_MS))
        {
            self.remove_front();
        }
    }
    fn remove_front(&mut self) {
        if let Some((_, _, bytes)) = self.frames.pop_front() {
            self.bytes -= bytes.len();
        }
    }
    fn acknowledge(&mut self, ack: Ack) {
        while self.frames.front().is_some_and(|(frame, _, _)| {
            frame.stream == ack.stream && frame.sequence <= ack.sequence
        }) {
            self.remove_front();
        }
    }
    fn next(&mut self, last: Option<Ack>) -> Vec<(Ack, Bytes)> {
        self.expire();
        self.frames
            .iter()
            .filter(|(frame, _, _)| {
                last.is_none_or(|last| {
                    last.stream != frame.stream || frame.sequence > last.sequence
                })
            })
            .take(4)
            .map(|(ack, _, bytes)| (*ack, bytes.clone()))
            .collect()
    }
}

pub async fn run() -> Result<()> {
    let endpoint = std::env::var("CAMERA_RELAY_URL")?;
    let url = url::Url::parse(&endpoint)?;
    ensure!(
        url.scheme() == "wss"
            || (url.scheme() == "ws" && matches!(url.host_str(), Some("127.0.0.1" | "localhost"))),
        "Remote relay requires wss://"
    );
    ensure!(
        url.path() == "/ingest"
            && url.query().is_none()
            && url.username().is_empty()
            && url.password().is_none(),
        "Use /ingest and a separate CAMERA_TOKEN"
    );
    let token = secret("CAMERA_TOKEN")?;
    let source =
        std::env::var("CAMERA_SOURCE").unwrap_or_else(|_| "rtsp://127.0.0.1:8554/cam".into());
    ensure!(
        matches!(url::Url::parse(&source)?.scheme(), "rtsp" | "rtsps"),
        "Camera source must be RTSP"
    );
    let replay = Arc::new(Mutex::new(Replay::default()));
    let capture_task = tokio::spawn(capture(source, replay.clone()));
    tokio::select! {
        result = capture_task => { result??; },
        result = network(endpoint, token, replay) => { result?; },
        _ = tokio::signal::ctrl_c() => {},
    }
    Ok(())
}

async fn capture(source: String, replay: Arc<Mutex<Replay>>) -> Result<()> {
    loop {
        let mut child = Command::new(std::env::var("FFMPEG").unwrap_or_else(|_| "ffmpeg".into()))
            .args([
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-rtsp_transport",
                "tcp",
                "-timeout",
                "5000000",
                "-i",
                &source,
                "-map",
                "0:v:0",
                "-an",
                "-c:v",
                "copy",
                "-bsf:v",
                "h264_mp4toannexb",
                "-mpegts_flags",
                "+resend_headers",
                "-muxdelay",
                "0",
                "-muxpreload",
                "0",
                "-flush_packets",
                "1",
                "-f",
                "mpegts",
                "pipe:1",
            ])
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .kill_on_drop(true)
            .spawn()?;
        let mut output = child.stdout.take().unwrap();
        let stream = Uuid::new_v4();
        let mut sequence = 0;
        *replay.lock().await = Replay::default();
        let mut bytes = vec![0; CHUNK];
        while let Ok(Ok(size)) = timeout(Duration::from_secs(8), output.read(&mut bytes)).await {
            if size == 0 {
                break;
            }
            sequence += 1;
            replay
                .lock()
                .await
                .push(encode(stream, sequence, &bytes[..size]));
        }
        let _ = child.kill().await;
        let _ = child.wait().await;
        eprintln!("camera source disconnected; restarting stream copy");
        sleep(Duration::from_secs(1)).await;
    }
}

async fn network(endpoint: String, token: String, replay: Arc<Mutex<Replay>>) -> Result<()> {
    let mut backoff = 250_u64;
    loop {
        let started = Instant::now();
        let result: Result<()> = async {
            let mut request = endpoint.as_str().into_client_request()?;
            request.headers_mut().insert("authorization", format!("Bearer {token}").parse()?);
            let (mut socket, _) = timeout(Duration::from_secs(10), connect_async(request)).await??;
            eprintln!("relay connected");
            let mut tick = tokio::time::interval(Duration::from_millis(10));
            tick.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
            let mut last = None;
            let mut heard = Instant::now();
            loop {
                tokio::select! {
                    _ = tick.tick() => {
                        ensure!(heard.elapsed() < Duration::from_secs(30), "Relay timed out");
                        let batch = replay.lock().await.next(last);
                        for (ack, packet) in batch {
                            timeout(Duration::from_secs(2), socket.send(Message::Binary(packet))).await??;
                            last = Some(ack);
                        }
                    },
                    response = socket.next() => match response {
                        Some(Ok(Message::Text(text))) => {
                            ensure!(text.len() <= 256, "Invalid acknowledgement");
                            let ack: Ack = serde_json::from_str(&text)?;
                            // The relay may have acknowledged a duplicate from a previous socket.
                            if last.is_some_and(|sent| ack.stream == sent.stream && ack.sequence <= sent.sequence) {
                                replay.lock().await.acknowledge(ack);
                            }
                            heard = Instant::now();
                        },
                        Some(Ok(Message::Ping(bytes))) => {
                            timeout(Duration::from_secs(2), socket.send(Message::Pong(bytes))).await??;
                            heard = Instant::now();
                        },
                        Some(Ok(Message::Pong(_))) => heard = Instant::now(),
                        Some(Ok(Message::Close(_))) | None => return Ok(()),
                        _ => anyhow::bail!("Relay disconnected"),
                    }
                }
            }
        }.await;
        if started.elapsed() > Duration::from_secs(10) {
            backoff = 250;
        }
        if result.is_err() {
            eprintln!("relay unavailable; reconnecting with bounded RAM buffer");
        }
        // Small independent jitter prevents synchronized reconnects after an outage.
        sleep(Duration::from_millis(backoff + (now_ms() % 100))).await;
        backoff = (backoff * 2).min(5_000);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn replay_is_bounded_and_acknowledged_data_is_discarded() {
        let mut replay = Replay::default();
        let stream = Uuid::new_v4();
        for sequence in 1..500 {
            replay.push(encode(stream, sequence, &vec![0; CHUNK]));
        }
        assert!(replay.bytes <= MAX_BUFFER);
        assert!(replay.frames.front().unwrap().0.sequence > 1);
        replay.acknowledge(Ack {
            stream,
            sequence: 499,
        });
        assert_eq!(replay.bytes, 0);
        assert!(replay.frames.is_empty());
    }
    #[test]
    fn expiry_preserves_realtime_instead_of_replaying_old_footage() {
        let mut replay = Replay::default();
        replay.push(encode(Uuid::new_v4(), 1, &[1]));
        replay.frames.front_mut().unwrap().1 = Instant::now() - Duration::from_secs(3);
        assert!(replay.next(None).is_empty());
        assert_eq!(replay.bytes, 0);
    }
}
