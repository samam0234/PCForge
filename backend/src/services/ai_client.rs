use std::time::Duration;

use serde_json::Value;

use crate::{AppState, error::AppError};

/// 상담 응답은 여러 번의 도구 호출과 답변 생성을 포함한다. AI 서버의 상한(240초)보다 길게 둔다.
const CHAT_TIMEOUT: Duration = Duration::from_secs(300);

/// FastAPI `POST /agent/run` 호출.
pub async fn run_agent(state: &AppState, requirements: &Value) -> Result<Value, AppError> {
    let response = state
        .http
        .post(format!("{}/agent/run", state.ai_server_url))
        .json(requirements)
        .send()
        .await
        .map_err(|e| AppError::AiServerUnavailable(e.to_string()))?;

    let status = response.status();
    let body: Value = response
        .json()
        .await
        .map_err(|e| AppError::AiServerUnavailable(e.to_string()))?;

    if status.is_success() {
        Ok(body)
    } else if status.is_client_error() {
        Err(AppError::AiServerRejected(status, body))
    } else {
        Err(AppError::AiServerUnavailable(format!("status {status}")))
    }
}

/// FastAPI `POST /agent/chat`을 열고, 본문은 읽지 않은 채 응답을 돌려준다.
pub async fn open_chat(state: &AppState, payload: &Value) -> Result<reqwest::Response, AppError> {
    let response = state
        .http
        .post(format!("{}/agent/chat", state.ai_server_url))
        .timeout(CHAT_TIMEOUT)
        .json(payload)
        .send()
        .await
        .map_err(|e| AppError::AiServerUnavailable(e.to_string()))?;

    let status = response.status();
    if status.is_success() {
        return Ok(response);
    }
    if status.is_client_error() {
        let body = response
            .json()
            .await
            .map_err(|e| AppError::AiServerUnavailable(e.to_string()))?;
        return Err(AppError::AiServerRejected(status, body));
    }
    Err(AppError::AiServerUnavailable(format!("status {status}")))
}
