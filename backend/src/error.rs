use axum::{
    Json,
    http::StatusCode,
    response::{IntoResponse, Response},
};
use serde_json::{Value, json};

pub enum AppError {
    /// 아직 구현되지 않은 엔드포인트 (Phase 2 예정)
    NotImplemented,
    /// AI 서버에 연결하지 못했거나 서버 오류를 반환함
    AiServerUnavailable(String),
    /// AI 서버가 4xx로 거절한 요청 (상태 코드와 본문을 그대로 전달)
    AiServerRejected(StatusCode, Value),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        match self {
            AppError::NotImplemented => (
                StatusCode::NOT_IMPLEMENTED,
                Json(json!({ "error": "아직 구현되지 않았습니다" })),
            )
                .into_response(),
            AppError::AiServerUnavailable(detail) => {
                tracing::error!("AI 서버 호출 실패: {detail}");
                (
                    StatusCode::BAD_GATEWAY,
                    Json(json!({ "error": "AI 서버를 사용할 수 없습니다" })),
                )
                    .into_response()
            }
            AppError::AiServerRejected(status, body) => (status, Json(body)).into_response(),
        }
    }
}
