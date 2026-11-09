use tower::Layer;

#[tokio::main]
async fn main() -> Result<(), vercel_runtime::Error> {
    let app = attendance_transport::relay::router()
        .await
        .map_err(|_| "Relay configuration or Redis connection failed")?;
    if std::env::var_os("VERCEL").is_some() {
        vercel_runtime::run(vercel_runtime::axum::VercelLayer::new().layer(app)).await
    } else {
        let address = std::env::var("RELAY_BIND").unwrap_or_else(|_| "127.0.0.1:3000".into());
        let listener = tokio::net::TcpListener::bind(address).await?;
        axum::serve(listener, app).await?;
        Ok(())
    }
}
