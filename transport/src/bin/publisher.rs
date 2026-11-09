#[tokio::main]
async fn main() {
    if attendance_transport::publisher::run().await.is_err() {
        eprintln!("Camera publisher stopped; check configuration and camera connectivity.");
        std::process::exit(1);
    }
}
