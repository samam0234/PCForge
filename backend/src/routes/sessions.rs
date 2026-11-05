use std::collections::BTreeMap;

use axum::{Json, extract::State, http::HeaderMap};
use serde_json::{Value, json};

use crate::{AppState, error::AppError, identity};

pub async fn list_sessions(
    State(state): State<AppState>,
    headers: HeaderMap,
) -> Result<Json<Value>, AppError> {
    let user = identity::resolve_user(&state.pool, &headers)
        .await?
        .ok_or_else(|| AppError::Unauthorized("로그인이 필요합니다".into()))?;
    let sessions = sqlx::query_as::<_, (String, String, String, Value)>(
        "SELECT id::text, created_at::text, status, requirements_json
         FROM search_sessions
         WHERE user_id = $1::uuid
         ORDER BY created_at DESC
         LIMIT 20",
    )
    .bind(&user.id)
    .fetch_all(&state.pool)
    .await?;

    let ids: Vec<String> = sessions.iter().map(|(id, _, _, _)| id.clone()).collect();
    let recs = if ids.is_empty() {
        Vec::new()
    } else {
        sqlx::query_as::<_, (String, String, i64, String, String)>(
            "SELECT session_id::text, product_name, price, site, COALESCE(reason, '')
             FROM recommendations
             WHERE session_id::text = ANY($1)
             ORDER BY score DESC NULLS LAST",
        )
        .bind(&ids)
        .fetch_all(&state.pool)
        .await?
    };

    let mut grouped: BTreeMap<String, Vec<Value>> = BTreeMap::new();
    for (session_id, product_name, price, site, reason) in recs {
        grouped.entry(session_id).or_default().push(json!({
            "product_name": product_name,
            "price": price,
            "site": site,
            "reason": reason,
        }));
    }

    let body = sessions
        .into_iter()
        .map(|(id, created_at, status, requirements)| {
            json!({
                "id": id,
                "created_at": created_at,
                "status": status,
                "purpose": requirements.get("purpose").and_then(Value::as_str).unwrap_or(""),
                "budget_krw": requirements.get("budget_krw").and_then(Value::as_i64).unwrap_or(0),
                "explanation": requirements.get("_explanation").and_then(Value::as_str).unwrap_or(""),
                "recommendations": grouped.remove(&id).unwrap_or_default(),
            })
        })
        .collect::<Vec<_>>();

    Ok(Json(json!({ "sessions": body })))
}
