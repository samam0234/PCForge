mod auth;
mod catalog;
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
        .route("/api/catalog", get(catalog::list_catalog))
        .route("/api/recommend", post(recommend::recommend))
        .route("/api/sessions", get(sessions::list_sessions))
        .route("/api/auth/register", post(auth::register))
        .route("/api/auth/login", post(auth::login))
        .route("/api/auth/logout", post(auth::logout))
        .route("/api/auth/me", get(auth::me))
        .with_state(state)
}
