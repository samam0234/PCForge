use axum::http::{HeaderMap, header};
use sha2::{Digest, Sha256};
use sqlx::PgPool;

pub struct CurrentUser {
    pub id: String,
    pub email: String,
    pub name: String,
}

pub fn hash_token(token: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(token.as_bytes());
    hex::encode(hasher.finalize())
}

pub fn new_token() -> Result<String, getrandom::Error> {
    let mut bytes = [0u8; 32];
    getrandom::fill(&mut bytes)?;
    Ok(hex::encode(bytes))
}

pub fn bearer(headers: &HeaderMap) -> Option<String> {
    let value = headers.get(header::AUTHORIZATION)?.to_str().ok()?;
    let token = value.strip_prefix("Bearer ")?.trim();
    if token.is_empty() {
        None
    } else {
        Some(token.to_string())
    }
}

pub async fn resolve_user(pool: &PgPool, headers: &HeaderMap) -> Result<Option<CurrentUser>, sqlx::Error> {
    let Some(token) = bearer(headers) else {
        return Ok(None);
    };
    let row = sqlx::query_as::<_, (String, String, String)>(
        "SELECT u.id::text, u.email, u.name
         FROM auth_tokens t
         JOIN users u ON u.id = t.user_id
         WHERE t.token_hash = $1 AND t.expires_at > now()",
    )
    .bind(hash_token(&token))
    .fetch_optional(pool)
    .await?;
    Ok(row.map(|(id, email, name)| CurrentUser { id, email, name }))
}
