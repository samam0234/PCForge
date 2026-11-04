use axum::{Json, extract::State};
use serde_json::Value;

use crate::{AppState, error::AppError, services::ai_client};

/// 요구사항을 AI 서버로 전달한다. 입력 검증은 현재 FastAPI 스키마가 담당한다.
// TODO(Phase 2): 사용자 인증, SearchSessions / Recommendations 저장
pub async fn recommend(
    State(state): State<AppState>,
    Json(requirements): Json<Value>,
) -> Result<Json<Value>, AppError> {
    ai_client::run_agent(&state, &requirements).await.map(Json)
}
