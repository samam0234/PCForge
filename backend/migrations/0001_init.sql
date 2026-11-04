-- PCForge 초기 스키마 (기획서 5.3 데이터 모델 기준)

CREATE TABLE users (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email            TEXT NOT NULL UNIQUE,
    name             TEXT NOT NULL,
    preferences_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE search_sessions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    requirements_json JSONB NOT NULL,
    status            TEXT NOT NULL DEFAULT 'pending',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX search_sessions_user_id_idx ON search_sessions (user_id, created_at DESC);

CREATE TABLE recommendations (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id   UUID NOT NULL REFERENCES search_sessions (id) ON DELETE CASCADE,
    product_name TEXT NOT NULL,
    price        BIGINT NOT NULL,
    site         TEXT NOT NULL,
    url          TEXT,
    reason       TEXT,
    specs_json   JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_used      BOOLEAN NOT NULL DEFAULT false,
    score        DOUBLE PRECISION,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX recommendations_session_id_idx ON recommendations (session_id);

CREATE TABLE product_cache (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site        TEXT NOT NULL,
    external_id TEXT NOT NULL,
    title       TEXT NOT NULL,
    price       BIGINT,
    specs       JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (site, external_id)
);

CREATE TABLE compatibility_rules (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category    TEXT NOT NULL,
    rule_json   JSONB NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
