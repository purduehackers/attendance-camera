use anyhow::{Result, ensure};
use bytes::{BufMut, Bytes, BytesMut};
use serde::{Deserialize, Serialize};
use std::time::{SystemTime, UNIX_EPOCH};
use uuid::Uuid;

pub const HEADER: usize = 36;
pub const CHUNK: usize = 32 * 1024;
pub const MAX_FRAME: usize = HEADER + CHUNK;
pub const MAX_REQUEST: usize = 16 * 1024;
pub const MAX_RESPONSE: usize = 1024 * 1024;
pub const REPLAY_MS: u64 = 2_000;

pub fn now_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Ack {
    pub stream: Uuid,
    pub sequence: u64,
}

pub fn encode(stream: Uuid, sequence: u64, payload: &[u8]) -> Bytes {
    let mut out = BytesMut::with_capacity(HEADER + payload.len());
    out.extend_from_slice(b"PHC1");
    out.extend_from_slice(stream.as_bytes());
    out.put_u64(sequence);
    out.put_u64(now_ms());
    out.extend_from_slice(payload);
    out.freeze()
}

pub fn decode(data: &[u8]) -> Result<(Ack, u64)> {
    ensure!(
        (HEADER + 1..=MAX_FRAME).contains(&data.len()) && &data[..4] == b"PHC1",
        "Invalid video packet"
    );
    let stream = Uuid::from_slice(&data[4..20])?;
    let sequence = u64::from_be_bytes(data[20..28].try_into()?);
    let created = u64::from_be_bytes(data[28..36].try_into()?);
    ensure!(sequence > 0, "Invalid video sequence");
    Ok((Ack { stream, sequence }, created))
}

#[derive(Deserialize, Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Request {
    pub id: Uuid,
    pub method: String,
    pub path: String,
    pub body: String,
    pub created: u64,
}

#[derive(Deserialize, Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Reply {
    pub status: u16,
    pub content_type: String,
    pub body: String,
}

pub fn allowed(method: &str, path: &str) -> bool {
    match (method, path) {
        ("GET", "/api/status" | "/api/preview.jpg" | "/api/sessions" | "/readyz")
        | ("PUT", "/api/calibration")
        | ("POST", "/api/sessions" | "/api/session/end" | "/api/session/reconcile") => true,
        ("GET", p) => p
            .strip_prefix("/api/sessions/")
            .and_then(|p| p.strip_suffix("/counts.csv"))
            .is_some_and(|id| Uuid::parse_str(id).is_ok() && id.len() == 36),
        _ => false,
    }
}

#[derive(Default)]
pub struct Sequence {
    last: Option<Ack>,
    retired: std::collections::VecDeque<Uuid>,
}

#[derive(Debug, PartialEq)]
pub enum Delivery {
    Next,
    Duplicate,
    Reset,
    Retired,
}

impl Sequence {
    pub fn accept(&mut self, ack: Ack) -> Delivery {
        if self.retired.contains(&ack.stream) {
            return Delivery::Retired;
        }
        let delivery = match self.last {
            Some(last) if last.stream == ack.stream && ack.sequence <= last.sequence => {
                return Delivery::Duplicate;
            }
            Some(last) if last.stream == ack.stream && ack.sequence == last.sequence + 1 => {
                Delivery::Next
            }
            Some(last) => {
                if last.stream != ack.stream {
                    self.retired.push_back(last.stream);
                    if self.retired.len() > 8 {
                        self.retired.pop_front();
                    }
                }
                Delivery::Reset
            }
            None => Delivery::Next,
        };
        self.last = Some(ack);
        delivery
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn packets_reject_bad_headers_and_oversized_payloads() {
        let stream = Uuid::new_v4();
        let packet = encode(stream, 2, &[0x47; 188]);
        assert_eq!(
            decode(&packet).unwrap().0,
            Ack {
                stream,
                sequence: 2
            }
        );
        for end in 0..=HEADER {
            assert!(decode(&packet[..end]).is_err());
        }
        assert!(decode(&encode(stream, 0, &[1])).is_err());
        assert!(decode(&encode(stream, 1, &vec![1; CHUNK + 1])).is_err());
    }
    #[test]
    fn proxy_is_a_fixed_api_not_an_open_tunnel() {
        assert!(allowed(
            "GET",
            &format!("/api/sessions/{}/counts.csv", Uuid::new_v4())
        ));
        assert!(allowed("POST", "/api/session/reconcile"));
        for path in [
            "http://169.254.169.254/",
            "//localhost/",
            "/api/../healthz",
            "/api/status?x=1",
            "/api/sessions/../../counts.csv",
        ] {
            assert!(!allowed("GET", path));
        }
        assert!(!allowed("DELETE", "/api/sessions"));
    }
    #[test]
    fn reconnect_deduplicates_and_missing_data_forces_reset() {
        let mut sequence = Sequence::default();
        let a = Uuid::new_v4();
        let b = Uuid::new_v4();
        let ack = |stream, sequence| Ack { stream, sequence };
        assert_eq!(sequence.accept(ack(a, 1)), Delivery::Next);
        assert_eq!(sequence.accept(ack(a, 1)), Delivery::Duplicate);
        assert_eq!(sequence.accept(ack(a, 2)), Delivery::Next);
        assert_eq!(sequence.accept(ack(a, 4)), Delivery::Reset);
        assert_eq!(sequence.accept(ack(b, 1)), Delivery::Reset);
        assert_eq!(sequence.accept(ack(a, 5)), Delivery::Retired);
        assert_eq!(sequence.accept(ack(b, 2)), Delivery::Next);
    }
}
