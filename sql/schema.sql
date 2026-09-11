

CREATE TABLE IF NOT EXISTS search_log (
    id            SERIAL PRIMARY KEY,
    user_id       VARCHAR(255),
    keyword       VARCHAR(500) NOT NULL,
    tags_filter   JSONB DEFAULT '[]'::jsonb,
    result_count  INTEGER,
    searched_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dataset_view_log (
    id            SERIAL PRIMARY KEY,
    user_id       VARCHAR(255),
    dataset_fqn   VARCHAR(1000) NOT NULL,
    dataset_name  VARCHAR(500),
    entity_type   VARCHAR(50) DEFAULT 'table',
    viewed_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dataset_favorite (
    id            SERIAL PRIMARY KEY,
    user_id       VARCHAR(255) NOT NULL,
    dataset_fqn   VARCHAR(1000) NOT NULL,
    dataset_name  VARCHAR(500),
    entity_type   VARCHAR(50) DEFAULT 'table',
    favorited_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, dataset_fqn)
);

CREATE INDEX IF NOT EXISTS idx_search_log_keyword     ON search_log (keyword);
CREATE INDEX IF NOT EXISTS idx_search_log_searched_at ON search_log (searched_at);
CREATE INDEX IF NOT EXISTS idx_search_log_tags        ON search_log USING GIN (tags_filter);

CREATE INDEX IF NOT EXISTS idx_view_log_fqn        ON dataset_view_log (dataset_fqn);
CREATE INDEX IF NOT EXISTS idx_view_log_viewed_at  ON dataset_view_log (viewed_at);

CREATE INDEX IF NOT EXISTS idx_favorite_user  ON dataset_favorite (user_id);
CREATE INDEX IF NOT EXISTS idx_favorite_fqn   ON dataset_favorite (dataset_fqn);
