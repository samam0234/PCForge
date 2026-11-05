use argon2::{
    Argon2,
    password_hash::{PasswordHash, PasswordHasher, PasswordVerifier, SaltString},
};
use axum::{Json, extract::State, http::HeaderMap};
use serde::Deserialize;
use serde_json::{Value, json};

use crate::{AppState, error::AppError, identity};

#[derive(Deserialize)]
pub struct RegisterBody {
    email: String,
    password: String,
    name: String,
}

#[derive(Deserialize)]
pub struct LoginBody {
    email: String,
    password: String,
}

struct Identity {
    id: String,
    email: String,
    name: String,
}

pub async fn register(
    State(state): State<AppState>,
    Json(body): Json<RegisterBody>,
) -> Result<Json<Value>, AppError> {
    let email = normalize_email(&body.email)?;
    let name = clean_name(&body.name)?;
    validate_password(&body.password)?;
    let password_hash = hash_password(&body.password)?;
    let id: String = sqlx::query_scalar(
        "INSERT INTO users (email, name, password_hash) VALUES ($1, $2, $3) RETURNING id::text",
    )
    .bind(&email)
    .bind(&name)
    .bind(&password_hash)
    .fetch_one(&state.pool)
    .await?;
    let token = issue_token(&state, &id).await?;
    Ok(Json(auth_body(token, &Identity { id, email, name })))
}

pub async fn login(
    State(state): State<AppState>,
    Json(body): Json<LoginBody>,
) -> Result<Json<Value>, AppError> {
    let email = normalize_email(&body.email)?;
    let row = sqlx::query_as::<_, (String, String, String, String)>(
        "SELECT id::text, email, name, password_hash FROM users WHERE email = $1",
    )
    .bind(&email)
    .fetch_optional(&state.pool)
    .await?;
    let Some((id, email, name, password_hash)) = row else {
        return Err(AppError::Unauthorized("이메일 또는 비밀번호가 올바르지 않습니다".into()));
    };
    if !verify_password(&body.password, &password_hash) {
        return Err(AppError::Unauthorized("이메일 또는 비밀번호가 올바르지 않습니다".into()));
    }
    let token = issue_token(&state, &id).await?;
    Ok(Json(auth_body(token, &Identity { id, email, name })))
}

pub async fn me(State(state): State<AppState>, headers: HeaderMap) -> Result<Json<Value>, AppError> {
    let user = identity::resolve_user(&state.pool, &headers)
        .await?
        .ok_or_else(|| AppError::Unauthorized("로그인이 필요합니다".into()))?;
    Ok(Json(json!({ "id": user.id, "email": user.email, "name": user.name })))
}

pub async fn logout(State(state): State<AppState>, headers: HeaderMap) -> Result<Json<Value>, AppError> {
    let token = identity::bearer(&headers).ok_or_else(|| AppError::Unauthorized("로그인이 필요합니다".into()))?;
    sqlx::query("DELETE FROM auth_tokens WHERE token_hash = $1")
        .bind(identity::hash_token(&token))
        .execute(&state.pool)
        .await?;
    Ok(Json(json!({ "ok": true })))
}

fn auth_body(token: String, user: &Identity) -> Value {
    json!({
        "token": token,
        "user": { "id": user.id, "email": user.email, "name": user.name }
    })
}

async fn issue_token(state: &AppState, user_id: &str) -> Result<String, AppError> {
    let token = identity::new_token().map_err(|err| {
        tracing::error!("token: {err}");
        AppError::Internal("로그인 토큰을 만들지 못했습니다")
    })?;
    sqlx::query(
        "INSERT INTO auth_tokens (token_hash, user_id, expires_at)
         VALUES ($1, $2::uuid, now() + interval '14 days')",
    )
    .bind(identity::hash_token(&token))
    .bind(user_id)
    .execute(&state.pool)
    .await?;
    Ok(token)
}

fn normalize_email(email: &str) -> Result<String, AppError> {
    let email = email.trim().to_lowercase();
    let Some((name, domain)) = email.split_once('@') else {
        return Err(AppError::BadRequest("이메일 형식을 확인해 주세요".into()));
    };
    if name.is_empty() || !domain.contains('.') || email.len() > 120 {
        return Err(AppError::BadRequest("이메일 형식을 확인해 주세요".into()));
    }
    Ok(email)
}

fn clean_name(name: &str) -> Result<String, AppError> {
    let name = name.trim();
    if name.is_empty() || name.chars().count() > 40 {
        return Err(AppError::BadRequest("이름은 1자에서 40자까지입니다".into()));
    }
    Ok(name.to_string())
}

fn validate_password(password: &str) -> Result<(), AppError> {
    if password.chars().count() < 8 || password.len() > 128 {
        return Err(AppError::BadRequest("비밀번호는 8자 이상이어야 합니다".into()));
    }
    Ok(())
}

fn hash_password(password: &str) -> Result<String, AppError> {
    let mut salt_bytes = [0u8; 16];
    getrandom::fill(&mut salt_bytes).map_err(|err| {
        tracing::error!("salt: {err}");
        AppError::Internal("비밀번호를 저장하지 못했습니다")
    })?;
    let salt = SaltString::encode_b64(&salt_bytes).map_err(|err| {
        tracing::error!("salt encode: {err}");
        AppError::Internal("비밀번호를 저장하지 못했습니다")
    })?;
    Argon2::default()
        .hash_password(password.as_bytes(), &salt)
        .map(|hash| hash.to_string())
        .map_err(|err| {
            tracing::error!("argon2: {err}");
            AppError::Internal("비밀번호를 저장하지 못했습니다")
        })
}

fn verify_password(password: &str, encoded: &str) -> bool {
    let Ok(parsed) = PasswordHash::new(encoded) else {
        return false;
    };
    Argon2::default().verify_password(password.as_bytes(), &parsed).is_ok()
}
