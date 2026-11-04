use sqlx::{PgPool, postgres::PgPoolOptions};
use std::time::Duration;

/// 지연 연결 풀을 만든다. DB가 꺼져 있어도 서버는 뜨고, `/health`에서 상태를 알 수 있다.
pub fn create_pool(database_url: &str) -> Result<PgPool, sqlx::Error> {
    PgPoolOptions::new()
        .max_connections(5)
        .acquire_timeout(Duration::from_secs(2))
        .connect_lazy(database_url)
}
