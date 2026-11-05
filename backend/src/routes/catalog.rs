use axum::{Json, extract::{Query, State}, http::HeaderMap};
use serde_json::Value;

use crate::{AppState, catalog::CatalogQuery, error::AppError, identity};

pub async fn list_catalog(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<CatalogQuery>,
) -> Result<Json<Value>, AppError> {
    let member = match identity::resolve_user(&state.pool, &headers).await {
        Ok(user) => user.is_some(),
        Err(err) => {
            tracing::error!("catalog auth: {err}");
            false
        }
    };
    state
        .catalog
        .query(member, &query)
        .map(Json)
        .map_err(|err| {
            tracing::error!("catalog: {err}");
            AppError::Internal("카탈로그를 읽지 못했습니다")
        })
}
