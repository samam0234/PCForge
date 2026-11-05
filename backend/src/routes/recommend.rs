use axum::{Json, extract::State, http::HeaderMap};
use serde::Deserialize;
use serde_json::{Value, json};

use crate::{
    AppState,
    catalog::{GUEST_SHORTLIST, MEMBER_ONLY, MEMBER_SHORTLIST},
    error::AppError,
    identity,
    services::ai_client,
};

#[derive(Deserialize)]
struct SavedRec {
    product_name: String,
    price: i64,
    site: String,
    url: Option<String>,
    #[serde(default)]
    reason: String,
    #[serde(default)]
    specs: Value,
    #[serde(default)]
    is_used: bool,
    score: Option<f64>,
}

/// 요구사항을 AI 서버로 전달한다. 회원 여부는 토큰으로 정하고, 회원 추천만 기록한다.
pub async fn recommend(
    State(state): State<AppState>,
    headers: HeaderMap,
    Json(mut requirements): Json<Value>,
) -> Result<Json<Value>, AppError> {
    let user = identity::resolve_user(&state.pool, &headers).await?;
    let member = user.is_some();
    if let Some(obj) = requirements.as_object_mut() {
        obj.insert(
            "access_tier".into(),
            json!(if member { "member" } else { "guest" }),
        );
        if !member {
            for key in MEMBER_ONLY {
                obj.remove(*key);
            }
            obj.remove("notes");
            obj.remove("priorities");
        }
        let cap = if member { MEMBER_SHORTLIST } else { GUEST_SHORTLIST };
        if let Some(ids) = obj.get_mut("selected_ids").and_then(Value::as_array_mut) {
            ids.truncate(cap);
        }
    }

    let mut body = ai_client::run_agent(&state, &requirements).await?;
    body["tier"] = json!(if member { "member" } else { "guest" });
    if let Some(user) = user {
        let session_id = save_session(&state, &user.id, &requirements, &body).await?;
        body["session_id"] = json!(session_id);
    }
    Ok(Json(body))
}

async fn save_session(
    state: &AppState,
    user_id: &str,
    requirements: &Value,
    body: &Value,
) -> Result<String, AppError> {
    let mut stored = requirements.clone();
    if let (Some(obj), Some(explanation)) = (stored.as_object_mut(), body.get("explanation")) {
        obj.insert("_explanation".into(), explanation.clone());
    }
    let mut tx = state.pool.begin().await?;
    let session_id: String = sqlx::query_scalar(
        "INSERT INTO search_sessions (user_id, requirements_json, status)
         VALUES ($1::uuid, $2, 'done') RETURNING id::text",
    )
    .bind(user_id)
    .bind(&stored)
    .fetch_one(&mut *tx)
    .await?;

    let recs: Vec<SavedRec> = serde_json::from_value(
        body.get("recommendations").cloned().unwrap_or_else(|| json!([])),
    )
    .unwrap_or_default();
    for rec in recs {
        let specs = if rec.specs.is_object() { rec.specs } else { json!({}) };
        sqlx::query(
            "INSERT INTO recommendations
                (session_id, product_name, price, site, url, reason, specs_json, is_used, score)
             VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, $8, $9)",
        )
        .bind(&session_id)
        .bind(&rec.product_name)
        .bind(rec.price)
        .bind(&rec.site)
        .bind(&rec.url)
        .bind(&rec.reason)
        .bind(&specs)
        .bind(rec.is_used)
        .bind(rec.score)
        .execute(&mut *tx)
        .await?;
    }
    tx.commit().await?;
    Ok(session_id)
}
