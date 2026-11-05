//! PCForge 메인 백엔드: API 게이트웨이, 인증, DB, AI 서버 호출 오케스트레이션.

mod catalog;
mod db;
mod error;
mod identity;
mod routes;
mod services;

use std::{sync::Arc, time::Duration};

use axum::http::{HeaderValue, Method, header};
use sqlx::PgPool;
use tower_http::{cors::CorsLayer, trace::TraceLayer};

#[derive(Clone)]
pub struct AppState {
    pub pool: PgPool,
    pub http: reqwest::Client,
    pub ai_server_url: String,
    pub catalog: Arc<catalog::CatalogStore>,
}

fn env_or(key: &str, default: &str) -> String {
    std::env::var(key).unwrap_or_else(|_| default.to_string())
}

#[tokio::main]
async fn main() {
    dotenvy::dotenv().ok();
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info,tower_http=debug".into()),
        )
        .init();

    let database_url = std::env::var("DATABASE_URL").expect("DATABASE_URL 환경 변수가 필요합니다");
    let origin = env_or("FRONTEND_ORIGIN", "http://localhost:5173");
    let port = env_or("BACKEND_PORT", "3000");

    let state = AppState {
        pool: db::create_pool(&database_url).expect("DATABASE_URL 형식이 올바르지 않습니다"),
        http: reqwest::Client::builder()
            .timeout(Duration::from_secs(160))
            .build()
            .expect("HTTP 클라이언트를 만들지 못했습니다"),
        ai_server_url: env_or("AI_SERVER_URL", "http://localhost:8000"),
        catalog: Arc::new(catalog::CatalogStore::open()),
    };

    let cors = CorsLayer::new()
        .allow_origin(
            origin
                .parse::<HeaderValue>()
                .expect("FRONTEND_ORIGIN 형식이 올바르지 않습니다"),
        )
        .allow_methods([Method::GET, Method::POST])
        .allow_headers([header::CONTENT_TYPE, header::AUTHORIZATION]);

    let app = routes::router(state)
        .layer(cors)
        .layer(TraceLayer::new_for_http());

    let listener = tokio::net::TcpListener::bind(format!("0.0.0.0:{port}"))
        .await
        .expect("포트 바인딩 실패");
    tracing::info!("PCForge backend listening on :{port}");
    axum::serve(listener, app).await.expect("서버 실행 실패");
}
