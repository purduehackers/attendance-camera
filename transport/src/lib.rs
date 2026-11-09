mod auth;
pub mod bridge;
pub mod protocol;
pub mod publisher;
pub mod relay;

use anyhow::{Context, Result, ensure};

pub fn secret(name: &str) -> Result<String> {
    let value = std::env::var(name).with_context(|| format!("{name} is required"))?;
    ensure!(
        value.len() >= 32,
        "{name} must contain at least 32 characters"
    );
    Ok(value)
}

pub fn redis_client() -> Result<redis::Client> {
    let value = std::env::var("REDIS_URL").context("REDIS_URL is required")?;
    let parsed = url::Url::parse(&value).map_err(|_| anyhow::anyhow!("Invalid REDIS_URL"))?;
    let local = matches!(parsed.host_str(), Some("127.0.0.1" | "localhost" | "[::1]"));
    ensure!(
        parsed.scheme() == "rediss" || (parsed.scheme() == "redis" && local),
        "Remote Redis requires TLS (rediss://)"
    );
    ensure!(
        parsed.fragment().is_none(),
        "Redis TLS verification must stay enabled"
    );
    redis::Client::open(value).map_err(|_| anyhow::anyhow!("Invalid Redis configuration"))
}

pub fn namespace() -> Result<String> {
    let value = std::env::var("REDIS_NAMESPACE").unwrap_or_else(|_| "attendance:v1".into());
    ensure!(
        value.len() <= 80
            && value.starts_with("attendance:")
            && value
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || b == b':' || b == b'-'),
        "Invalid Redis namespace"
    );
    Ok(value)
}
