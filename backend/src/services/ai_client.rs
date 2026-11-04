use serde_json::Value;

use crate::{AppState, error::AppError};

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
