ALTER TABLE users ADD COLUMN password_hash TEXT NOT NULL;

CREATE TABLE auth_tokens (
    token_hash TEXT PRIMARY KEY,
    user_id    UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX auth_tokens_user_id_idx ON auth_tokens (user_id);
