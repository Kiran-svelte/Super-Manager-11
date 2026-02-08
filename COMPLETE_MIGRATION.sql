-- =============================================================================
-- SUPER MANAGER - COMPLETE DATABASE MIGRATION
-- =============================================================================
-- Run this ENTIRE file in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/hpqmcdygbjdmvxfmvucf/sql
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- HELPER FUNCTION FOR UPDATED_AT
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- USERS TABLE (if not exists)
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    phone VARCHAR(50),
    telegram_id VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
    language VARCHAR(10) DEFAULT 'en',
    preferences JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- =============================================================================
-- SESSIONS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);

-- =============================================================================
-- MESSAGES TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    actions_taken JSONB DEFAULT '[]',
    expert_persona VARCHAR(100),
    model_used VARCHAR(100),
    tokens_used INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);

-- =============================================================================
-- MEETINGS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS meetings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    meeting_link VARCHAR(500),
    platform VARCHAR(50) DEFAULT 'jitsi',
    status VARCHAR(50) DEFAULT 'scheduled',
    attendees JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_meetings_user_id ON meetings(user_id);
CREATE INDEX IF NOT EXISTS idx_meetings_start ON meetings(start_time);

-- =============================================================================
-- USER PROFILES TABLE (Memory)
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    name VARCHAR(255),
    preferences JSONB DEFAULT '{}',
    context JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);

-- =============================================================================
-- USER CONTACTS TABLE (Relationships)
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    relationship VARCHAR(50) DEFAULT 'other',
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_contacts_user_id ON user_contacts(user_id);
CREATE INDEX IF NOT EXISTS idx_user_contacts_name ON user_contacts(name);

-- =============================================================================
-- USER PREFERENCES TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    key VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, category, key)
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- =============================================================================
-- ORCHESTRATED TASKS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS orchestrated_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    task_type VARCHAR(100) NOT NULL,
    progress_percent INTEGER DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
    status VARCHAR(50) DEFAULT 'pending',
    estimated_completion TIMESTAMP WITH TIME ZONE,
    actual_completion TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    needs_user_input BOOLEAN DEFAULT FALSE,
    input_prompt TEXT,
    input_options JSONB DEFAULT '[]',
    user_input_received JSONB,
    meeting_id UUID REFERENCES meetings(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orchestrated_tasks_user_id ON orchestrated_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_orchestrated_tasks_status ON orchestrated_tasks(status);

-- =============================================================================
-- TASK SUBSTEPS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS task_substeps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES orchestrated_tasks(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    progress_weight INTEGER DEFAULT 10,
    action_type VARCHAR(100),
    action_params JSONB DEFAULT '{}',
    result JSONB,
    error_message TEXT,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    detection_type VARCHAR(50),
    detection_config JSONB DEFAULT '{}',
    depends_on UUID[],
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_task_substeps_task_id ON task_substeps(task_id);
CREATE INDEX IF NOT EXISTS idx_task_substeps_status ON task_substeps(status);

-- =============================================================================
-- AI IDENTITIES TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_identities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) DEFAULT 'AI Assistant',
    auth_type VARCHAR(50) NOT NULL DEFAULT 'app_password',
    encrypted_password TEXT,
    oauth_access_token TEXT,
    oauth_refresh_token TEXT,
    oauth_expires_at TIMESTAMP WITH TIME ZONE,
    oauth_scope TEXT,
    status VARCHAR(50) DEFAULT 'pending_setup',
    last_verified_at TIMESTAMP WITH TIME ZONE,
    verification_error TEXT,
    can_send_email BOOLEAN DEFAULT FALSE,
    can_read_email BOOLEAN DEFAULT FALSE,
    can_signup_services BOOLEAN DEFAULT FALSE,
    daily_email_limit INTEGER DEFAULT 100,
    emails_sent_today INTEGER DEFAULT 0,
    last_email_reset DATE DEFAULT CURRENT_DATE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_ai_identities_user_id ON ai_identities(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_identities_email ON ai_identities(email);

-- =============================================================================
-- AI SERVICE ACCOUNTS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_service_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ai_identity_id UUID NOT NULL REFERENCES ai_identities(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    service_name VARCHAR(255) NOT NULL,
    service_url VARCHAR(500),
    account_email VARCHAR(255),
    account_username VARCHAR(255),
    encrypted_api_key TEXT,
    encrypted_api_secret TEXT,
    additional_creds JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    daily_limit INTEGER,
    monthly_limit INTEGER,
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    verification_pending BOOLEAN DEFAULT FALSE,
    capabilities JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(ai_identity_id, service_name)
);

CREATE INDEX IF NOT EXISTS idx_ai_service_accounts_identity ON ai_service_accounts(ai_identity_id);
CREATE INDEX IF NOT EXISTS idx_ai_service_accounts_service ON ai_service_accounts(service_name);

-- =============================================================================
-- AI DECISION LOG TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_decision_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255),
    decision_type VARCHAR(100) NOT NULL,
    decision_summary TEXT NOT NULL,
    reasoning TEXT,
    proposed_action JSONB,
    executed_action JSONB,
    required_confirmation BOOLEAN DEFAULT FALSE,
    user_confirmed BOOLEAN,
    user_feedback TEXT,
    outcome VARCHAR(50),
    outcome_details JSONB,
    related_decisions UUID[],
    consistency_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_decisions_user ON ai_decision_log(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_decisions_type ON ai_decision_log(decision_type);

-- =============================================================================
-- AI COMMITMENTS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_commitments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    commitment_text TEXT NOT NULL,
    context TEXT,
    status VARCHAR(50) DEFAULT 'active',
    fulfilled_at TIMESTAMP WITH TIME ZONE,
    related_task_id UUID REFERENCES orchestrated_tasks(id),
    importance VARCHAR(20) DEFAULT 'normal',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_ai_commitments_user ON ai_commitments(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_commitments_status ON ai_commitments(status);

-- =============================================================================
-- SENSITIVE DATA REQUESTS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS sensitive_data_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    data_type VARCHAR(50) NOT NULL,
    purpose TEXT NOT NULL,
    service_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    received_at TIMESTAMP WITH TIME ZONE,
    used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    data_received BOOLEAN DEFAULT FALSE,
    audit_log JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sensitive_requests_user ON sensitive_data_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_sensitive_requests_status ON sensitive_data_requests(status);

-- =============================================================================
-- BLOCKED SERVICES TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS blocked_services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(255) NOT NULL UNIQUE,
    service_url VARCHAR(500),
    block_reason VARCHAR(100) NOT NULL,
    block_category VARCHAR(100),
    alternative_services JSONB DEFAULT '[]',
    workaround_possible BOOLEAN DEFAULT FALSE,
    workaround_description TEXT,
    last_checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pre-populate blocked services
INSERT INTO blocked_services (service_name, block_reason, block_category, alternative_services) VALUES
    ('WhatsApp Business API', 'phone_verification', 'verification', '["Telegram Bot API", "Signal API"]'),
    ('Twitter/X API', 'phone_verification', 'verification', '["Mastodon API", "Bluesky API"]'),
    ('Facebook Graph API', 'phone_verification', 'verification', '["Telegram Bot API"]'),
    ('Instagram API', 'phone_verification', 'verification', '["Telegram Bot API"]'),
    ('LinkedIn API', 'business_verification', 'verification', '[]'),
    ('PayPal API', 'identity_verification', 'financial', '["Stripe", "Razorpay"]'),
    ('Stripe', 'business_verification', 'financial', '["Razorpay", "PayU"]'),
    ('AWS', 'payment_required', 'financial', '["Google Cloud Free Tier", "Azure Free Tier"]'),
    ('Aadhaar Services', 'government_id', 'legal', '[]'),
    ('DigiLocker', 'government_id', 'legal', '[]'),
    ('UPI Apps', 'phone_verification', 'financial', '[]'),
    ('Banking APIs', 'kyc_required', 'financial', '[]')
ON CONFLICT (service_name) DO NOTHING;

-- =============================================================================
-- ENABLE ROW LEVEL SECURITY
-- =============================================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE meetings ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE orchestrated_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_substeps ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_identities ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_service_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_decision_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_commitments ENABLE ROW LEVEL SECURITY;
ALTER TABLE sensitive_data_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE blocked_services ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- CREATE RLS POLICIES FOR SERVICE ROLE ACCESS
-- =============================================================================
DO $$
BEGIN
    -- Each table needs a policy for service role
    CREATE POLICY IF NOT EXISTS "service_role_users" ON users FOR ALL USING (true) WITH CHECK (true);
    CREATE POLICY IF NOT EXISTS "service_role_sessions" ON sessions FOR ALL USING (true) WITH CHECK (true);
    CREATE POLICY IF NOT EXISTS "service_role_messages" ON messages FOR ALL USING (true) WITH CHECK (true);
    CREATE POLICY IF NOT EXISTS "service_role_meetings" ON meetings FOR ALL USING (true) WITH CHECK (true);
    CREATE POLICY IF NOT EXISTS "service_role_user_profiles" ON user_profiles FOR ALL USING (true) WITH CHECK (true);
    CREATE POLICY IF NOT EXISTS "service_role_user_contacts" ON user_contacts FOR ALL USING (true) WITH CHECK (true);
    CREATE POLICY IF NOT EXISTS "service_role_user_preferences" ON user_preferences FOR ALL USING (true) WITH CHECK (true);
    CREATE POLICY IF NOT EXISTS "service_role_orchestrated_tasks" ON orchestrated_tasks FOR ALL USING (true) WITH CHECK (true);
    CREATE POLICY IF NOT EXISTS "service_role_task_substeps" ON task_substeps FOR ALL USING (true) WITH CHECK (true);
    CREATE POLICY IF NOT EXISTS "service_role_ai_identities" ON ai_identities FOR ALL USING (true) WITH CHECK (true);
    CREATE POLICY IF NOT EXISTS "service_role_ai_service_accounts" ON ai_service_accounts FOR ALL USING (true) WITH CHECK (true);
    CREATE POLICY IF NOT EXISTS "service_role_ai_decision_log" ON ai_decision_log FOR ALL USING (true) WITH CHECK (true);
    CREATE POLICY IF NOT EXISTS "service_role_ai_commitments" ON ai_commitments FOR ALL USING (true) WITH CHECK (true);
    CREATE POLICY IF NOT EXISTS "service_role_sensitive_data_requests" ON sensitive_data_requests FOR ALL USING (true) WITH CHECK (true);
    CREATE POLICY IF NOT EXISTS "service_role_blocked_services" ON blocked_services FOR ALL USING (true) WITH CHECK (true);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- =============================================================================
-- CREATE UPDATE TRIGGERS
-- =============================================================================
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_meetings_updated_at ON meetings;
CREATE TRIGGER update_meetings_updated_at
    BEFORE UPDATE ON meetings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_orchestrated_tasks_updated_at ON orchestrated_tasks;
CREATE TRIGGER update_orchestrated_tasks_updated_at
    BEFORE UPDATE ON orchestrated_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_ai_identities_updated_at ON ai_identities;
CREATE TRIGGER update_ai_identities_updated_at
    BEFORE UPDATE ON ai_identities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_ai_service_accounts_updated_at ON ai_service_accounts;
CREATE TRIGGER update_ai_service_accounts_updated_at
    BEFORE UPDATE ON ai_service_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- DONE! All tables created successfully
-- =============================================================================
SELECT 'Migration complete! All ' || count(*) || ' tables are ready.' as status
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE';
