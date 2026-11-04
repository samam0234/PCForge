use axum::{Json, extract::State};
use serde_json::{Value, json};

use crate::AppState;

pub async fn health(State(state): State<AppState>) -> Json<Value> {
    let db_up = sqlx::query("SELECT 1").execute(&state.pool).await.is_ok();
    Json(json!({
        "status": "ok",
        "database": if db_up { "up" } else { "down" },
    }))
}
