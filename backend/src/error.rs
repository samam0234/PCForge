use axum::{
    Json,
    http::StatusCode,
    response::{IntoResponse, Response},
};
use serde_json::{Value, json};

pub enum AppError {
    /// 아직 구현되지 않은 엔드포인트
    #[allow(dead_code)]
    NotImplemented,
    /// AI 서버에 연결하지 못했거나 서버 오류를 반환함
    AiServerUnavailable(String),
    /// AI 서버가 4xx로 거절한 요청 (상태 코드와 본문을 그대로 전달)
    AiServerRejected(StatusCode, Value),
    BadRequest(String),
    Unauthorized(String),
    Conflict(String),
    Internal(&'static str),
}

impl From<sqlx::Error> for AppError {
    fn from(err: sqlx::Error) -> Self {
        tracing::error!("database: {err}");
        if let sqlx::Error::Database(db) = &err {
            if db.constraint() == Some("users_email_key") {
                return AppError::Conflict("이미 가입한 이메일입니다".into());
            }
        }
        AppError::Internal("요청을 처리하지 못했습니다")
    }
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, message) = match self {
            AppError::NotImplemented => (StatusCode::NOT_IMPLEMENTED, "아직 구현되지 않았습니다".into()),
            AppError::AiServerUnavailable(detail) => {
                tracing::error!("AI 서버 호출 실패: {detail}");
                (StatusCode::BAD_GATEWAY, "AI 서버를 사용할 수 없습니다".into())
            }
            AppError::AiServerRejected(status, body) => return (status, Json(body)).into_response(),
            AppError::BadRequest(message) => (StatusCode::BAD_REQUEST, message),
            AppError::Unauthorized(message) => (StatusCode::UNAUTHORIZED, message),
            AppError::Conflict(message) => (StatusCode::CONFLICT, message),
            AppError::Internal(message) => (StatusCode::INTERNAL_SERVER_ERROR, message.into()),
        };
        (status, Json(json!({ "error": message }))).into_response()
    }
}
