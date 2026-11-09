#[tokio::main]
async fn main() {
    if attendance_transport::bridge::run().await.is_err() {
        eprintln!("Attendance bridge stopped; check configuration and connectivity.");
        std::process::exit(1);
    }
}
