mod auth;
mod health;
mod recommend;
mod sessions;

use axum::{
    Router,
    routing::{get, post},
};

use crate::AppState;

pub fn router(state: AppState) -> Router {
    Router::new()
        .route("/health", get(health::health))
        .route("/api/recommend", post(recommend::recommend))
        .route("/api/sessions", get(sessions::list_sessions))
        .route("/api/auth/login", post(auth::login))
        .with_state(state)
}
