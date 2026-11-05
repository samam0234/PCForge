use axum::{Json, extract::State, http::HeaderMap};
use serde::Deserialize;
use serde_json::{Map, Value, json};

use crate::{
    AppState,
    catalog::{GUEST_SHORTLIST, MEMBER_ONLY, MEMBER_SHORTLIST},
    error::AppError,
    identity,
    services::ai_client,
};

const PRIORITIES: &[&str] = &["가격", "성능", "소음", "전력"];
const MAX_BUDGET: i64 = 500_000_000;
const MAX_NOTE: usize = 400;

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
    let dropped = if let Some(obj) = requirements.as_object_mut() {
        prepare_requirements(obj, member, &state)?
    } else {
        return Err(AppError::BadRequest("추천 조건을 확인해 주세요".into()));
    };

    let mut body = ai_client::run_agent(&state, &requirements).await?;
    body["tier"] = json!(if member { "member" } else { "guest" });
    if dropped > 0 {
        let message = json!(format!("목록에 없거나 판매가 끝난 후보 {dropped}건은 추천에서 뺐습니다."));
        if let Some(items) = body.get_mut("warnings").and_then(Value::as_array_mut) {
            items.insert(0, message);
        } else {
            body["warnings"] = json!([message]);
        }
    }
    if let Some(user) = user {
        let session_id = save_session(&state, &user.id, &requirements, &body).await?;
        body["session_id"] = json!(session_id);
    }
    Ok(Json(body))
}

fn prepare_requirements(obj: &mut Map<String, Value>, member: bool, state: &AppState) -> Result<usize, AppError> {
    let purpose = obj.get("purpose").and_then(Value::as_str).unwrap_or("").trim();
    let purpose: String = purpose.chars().take(40).collect();
    if purpose.is_empty() {
        return Err(AppError::BadRequest("용도를 입력해 주세요".into()));
    }
    obj.insert("purpose".into(), json!(purpose));

    let budget = obj.get("budget_krw").and_then(Value::as_i64).unwrap_or(0);
    if budget <= 0 {
        return Err(AppError::BadRequest("예산은 1원 이상이어야 합니다".into()));
    }
    obj.insert("budget_krw".into(), json!(budget.min(MAX_BUDGET)));

    let condition = obj.get("condition").and_then(Value::as_str).unwrap_or("mixed");
    if !matches!(condition, "new" | "used" | "mixed") {
        obj.insert("condition".into(), json!("mixed"));
    }
    obj.insert("access_tier".into(), json!(if member { "member" } else { "guest" }));

    if !member {
        for key in MEMBER_ONLY {
            obj.remove(*key);
        }
        obj.remove("notes");
        obj.remove("priorities");
    } else {
        let note = obj.get("notes").and_then(Value::as_str).unwrap_or("").trim();
        let note: String = note.chars().take(MAX_NOTE).collect();
        obj.insert("notes".into(), json!(note));
        let mut kept = Vec::new();
        if let Some(list) = obj.get("priorities").and_then(Value::as_array) {
            for item in list {
                let Some(text) = item.as_str() else { continue };
                if PRIORITIES.contains(&text) && !kept.iter().any(|saved: &String| saved == text) {
                    kept.push(text.to_string());
                }
            }
        }
        obj.insert("priorities".into(), json!(kept));
    }

    let cap = if member { MEMBER_SHORTLIST } else { GUEST_SHORTLIST };
    let mut ids = Vec::new();
    if let Some(list) = obj.get("selected_ids").and_then(Value::as_array) {
        for item in list {
            let Some(text) = item.as_str().map(str::trim) else { continue };
            if text.is_empty() || ids.iter().any(|saved: &String| saved == text) {
                continue;
            }
            ids.push(text.to_string());
            if ids.len() == cap {
                break;
            }
        }
    }
    let kept = state.catalog.selling_ids(&ids);
    let dropped = ids.len().saturating_sub(kept.len());
    obj.insert("selected_ids".into(), json!(kept));
    Ok(dropped)
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
