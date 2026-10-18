-- ============================================================
-- CareFlow PostgreSQL Database Schema
-- Phase 3 - PostgreSQL
-- ============================================================

-- ============================================================
-- 1. USERS
-- ============================================================

CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    hospital_name VARCHAR(255) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    city VARCHAR(150) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 2. DATASETS
-- ============================================================

CREATE TABLE datasets (
    id BIGSERIAL PRIMARY KEY,

    user_id BIGINT NOT NULL,
    filename VARCHAR(255) NOT NULL,

    dataset_type VARCHAR(50) NOT NULL
        CHECK (
            dataset_type IN (
                'hospital_history',
                'hospital_resources',
                'disease_data'
            )
        ),

    upload_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    start_date DATE,
    end_date DATE,

    status VARCHAR(50) NOT NULL DEFAULT 'uploaded',

    is_current BOOLEAN NOT NULL DEFAULT TRUE,

    version_number INTEGER NOT NULL DEFAULT 1,

    file_path TEXT,

    CONSTRAINT fk_datasets_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_dataset_dates
        CHECK (
            end_date IS NULL
            OR start_date IS NULL
            OR end_date >= start_date
        ),

    CONSTRAINT chk_dataset_version
        CHECK (version_number >= 1)
);


-- Only one current dataset of each type may exist for a user.
CREATE UNIQUE INDEX uq_current_dataset_per_user_type
ON datasets (user_id, dataset_type)
WHERE is_current = TRUE;


-- ============================================================
-- 3. TRAINING RUNS
-- ============================================================

CREATE TABLE training_runs (
    id BIGSERIAL PRIMARY KEY,

    dataset_id BIGINT NOT NULL,

    training_period_start DATE,
    training_period_end DATE,

    model_name VARCHAR(255) NOT NULL,
    model_version VARCHAR(100) NOT NULL,

    feature_schema_version VARCHAR(100),

    validation_metrics JSONB,
    test_metrics JSONB,

    training_started_at TIMESTAMPTZ,
    training_completed_at TIMESTAMPTZ,

    status VARCHAR(50) NOT NULL DEFAULT 'completed',

    CONSTRAINT fk_training_runs_dataset
        FOREIGN KEY (dataset_id)
        REFERENCES datasets(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_training_period
        CHECK (
            training_period_end IS NULL
            OR training_period_start IS NULL
            OR training_period_end >= training_period_start
        )
);


-- ============================================================
-- 4. FORECASTS
-- ============================================================

CREATE TABLE forecasts (
    id BIGSERIAL PRIMARY KEY,

    user_id BIGINT NOT NULL,
    dataset_id BIGINT NOT NULL,
    training_run_id BIGINT,

    forecast_type VARCHAR(50) NOT NULL
        CHECK (
            forecast_type IN (
                'admissions',
                'icu',
                'resource',
                'disease'
            )
        ),

    horizon INTEGER NOT NULL,

    generated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    model_name VARCHAR(255) NOT NULL,
    model_version VARCHAR(100),

    results JSONB NOT NULL,
    performance_metrics JSONB,

    CONSTRAINT fk_forecasts_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_forecasts_dataset
        FOREIGN KEY (dataset_id)
        REFERENCES datasets(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_forecasts_training_run
        FOREIGN KEY (training_run_id)
        REFERENCES training_runs(id)
        ON DELETE SET NULL,

    CONSTRAINT chk_forecast_horizon
        CHECK (horizon > 0)
);


-- ============================================================
-- 5. RESOURCE RECORDS
-- ============================================================

CREATE TABLE resource_records (
    id BIGSERIAL PRIMARY KEY,

    dataset_id BIGINT NOT NULL,

    date DATE NOT NULL,

    resource_category VARCHAR(100) NOT NULL,
    resource_name VARCHAR(255) NOT NULL,
    unit VARCHAR(100) NOT NULL,

    quantity_available NUMERIC(14,2) NOT NULL,
    quantity_used NUMERIC(14,2) NOT NULL,
    reference_capacity NUMERIC(14,2) NOT NULL,

    CONSTRAINT fk_resource_records_dataset
        FOREIGN KEY (dataset_id)
        REFERENCES datasets(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_quantity_available
        CHECK (quantity_available >= 0),

    CONSTRAINT chk_quantity_used
        CHECK (quantity_used >= 0),

    CONSTRAINT chk_reference_capacity
        CHECK (reference_capacity > 0)
);


-- ============================================================
-- 6. DISEASE DATA
-- ============================================================

CREATE TABLE disease_data (
    id BIGSERIAL PRIMARY KEY,

    date DATE NOT NULL,
    city VARCHAR(150) NOT NULL,
    disease VARCHAR(150) NOT NULL,
    cases INTEGER NOT NULL,

    CONSTRAINT chk_disease_cases
        CHECK (cases >= 0)
);

-- ============================================================
-- 7. AUDIT LOGS
-- ============================================================

CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,

    user_id BIGINT,

    action VARCHAR(100) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    details JSONB,

    CONSTRAINT fk_audit_logs_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL,

    CONSTRAINT chk_audit_action
        CHECK (
            action IN (
                'LOGIN',
                'DATASET_UPLOAD',
                'DATASET_VERSION_CREATED',
                'TRAINING_RUN',
                'FORECAST_GENERATED',
                'DATASET_DELETED',
                'LOGOUT'
            )
        )
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_datasets_user_id
ON datasets(user_id);

CREATE INDEX idx_datasets_type
ON datasets(dataset_type);

CREATE INDEX idx_forecasts_user_id
ON forecasts(user_id);

CREATE INDEX idx_forecasts_dataset_id
ON forecasts(dataset_id);

CREATE INDEX idx_training_runs_dataset_id
ON training_runs(dataset_id);

CREATE INDEX idx_resource_records_dataset_id
ON resource_records(dataset_id);

CREATE INDEX idx_resource_records_date
ON resource_records(date);

CREATE INDEX idx_disease_data_city_date
ON disease_data(city, date);

CREATE INDEX idx_audit_logs_user_id
ON audit_logs(user_id);

CREATE INDEX idx_audit_logs_created_at
ON audit_logs(created_at);