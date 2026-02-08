-- =====================================================
-- MISSING TABLES FOR AI IDENTITY SYSTEM
-- Run this in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/hpqmcdygbjdmvxfmvucf/sql
-- =====================================================

-- 1. Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- 2. AI Identities - The AI's own identity for each user
CREATE TABLE IF NOT EXISTS ai_identities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    email_password_encrypted TEXT NOT NULL,
    display_name TEXT DEFAULT 'Super Manager AI',
    persona TEXT DEFAULT 'professional_assistant',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    UNIQUE(user_id)
);

-- 3. AI Service Accounts - Services the AI has signed up for
CREATE TABLE IF NOT EXISTS ai_service_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ai_identity_id UUID REFERENCES ai_identities(id) ON DELETE CASCADE,
    service_name TEXT NOT NULL,
    service_category TEXT,
    username TEXT,
    email TEXT,
    password_encrypted TEXT,
    api_key_encrypted TEXT,
    api_secret_encrypted TEXT,
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    token_expires_at TIMESTAMPTZ,
    account_status TEXT DEFAULT 'active',
    signup_method TEXT DEFAULT 'automated',
    last_used_at TIMESTAMPTZ,
    usage_count INTEGER DEFAULT 0,
    rate_limit_remaining INTEGER,
    rate_limit_reset_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    UNIQUE(ai_identity_id, service_name)
);

-- 4. AI Decision Log - Track all AI decisions
CREATE TABLE IF NOT EXISTS ai_decision_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    decision_type TEXT NOT NULL,
    decision_context JSONB NOT NULL,
    decision_made TEXT NOT NULL,
    reasoning TEXT,
    confidence_score DECIMAL(3,2),
    was_overridden BOOLEAN DEFAULT FALSE,
    override_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. AI Commitments - Promises the AI has made
CREATE TABLE IF NOT EXISTS ai_commitments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    commitment_type TEXT NOT NULL,
    description TEXT NOT NULL,
    due_at TIMESTAMPTZ,
    status TEXT DEFAULT 'pending',
    fulfilled_at TIMESTAMPTZ,
    related_task_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- 6. Sensitive Data Requests - Track access to sensitive data
CREATE TABLE IF NOT EXISTS sensitive_data_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    data_type TEXT NOT NULL,
    purpose TEXT NOT NULL,
    approved BOOLEAN,
    approved_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Blocked Services - Services AI should never use
CREATE TABLE IF NOT EXISTS blocked_services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name TEXT UNIQUE NOT NULL,
    reason TEXT NOT NULL,
    blocked_at TIMESTAMPTZ DEFAULT NOW(),
    blocked_by TEXT DEFAULT 'system'
);

-- 8. Orchestrated Tasks - Multi-step task tracking
CREATE TABLE IF NOT EXISTS orchestrated_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    total_steps INTEGER DEFAULT 0,
    completed_steps INTEGER DEFAULT 0,
    current_step INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- 9. Task Substeps - Individual steps within orchestrated tasks
CREATE TABLE IF NOT EXISTS task_substeps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES orchestrated_tasks(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    action_params JSONB DEFAULT '{}',
    status TEXT DEFAULT 'pending',
    result JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    execution_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_ai_identities_user_id ON ai_identities(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_service_accounts_identity ON ai_service_accounts(ai_identity_id);
CREATE INDEX IF NOT EXISTS idx_ai_service_accounts_service ON ai_service_accounts(service_name);
CREATE INDEX IF NOT EXISTS idx_ai_decision_log_user ON ai_decision_log(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_commitments_user ON ai_commitments(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_commitments_status ON ai_commitments(status);
CREATE INDEX IF NOT EXISTS idx_orchestrated_tasks_user ON orchestrated_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_orchestrated_tasks_status ON orchestrated_tasks(status);
CREATE INDEX IF NOT EXISTS idx_task_substeps_task ON task_substeps(task_id);

-- =====================================================
-- PRE-POPULATE BLOCKED SERVICES
-- =====================================================

INSERT INTO blocked_services (service_name, reason) VALUES
('facebook', 'Requires phone verification and has strict bot detection'),
('instagram', 'Owned by Meta, requires phone verification'),
('twitter', 'X/Twitter has aggressive bot detection'),
('linkedin', 'Professional network with strict verification'),
('tiktok', 'Requires phone verification'),
('snapchat', 'Mobile-only with phone verification'),
('whatsapp', 'Requires phone number'),
('amazon_aws', 'Requires credit card for signup'),
('google_cloud', 'Requires credit card for signup'),
('azure', 'Requires credit card for signup'),
('stripe', 'Financial service requiring verification'),
('paypal', 'Financial service requiring verification')
ON CONFLICT (service_name) DO NOTHING;

-- =====================================================
-- ENABLE ROW LEVEL SECURITY
-- =====================================================

ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_identities ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_service_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_decision_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_commitments ENABLE ROW LEVEL SECURITY;
ALTER TABLE sensitive_data_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE orchestrated_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_substeps ENABLE ROW LEVEL SECURITY;

-- RLS Policies (allow service role full access)
CREATE POLICY "Service role has full access to sessions" ON sessions FOR ALL USING (true);
CREATE POLICY "Service role has full access to ai_identities" ON ai_identities FOR ALL USING (true);
CREATE POLICY "Service role has full access to ai_service_accounts" ON ai_service_accounts FOR ALL USING (true);
CREATE POLICY "Service role has full access to ai_decision_log" ON ai_decision_log FOR ALL USING (true);
CREATE POLICY "Service role has full access to ai_commitments" ON ai_commitments FOR ALL USING (true);
CREATE POLICY "Service role has full access to sensitive_data_requests" ON sensitive_data_requests FOR ALL USING (true);
CREATE POLICY "Service role has full access to orchestrated_tasks" ON orchestrated_tasks FOR ALL USING (true);
CREATE POLICY "Service role has full access to task_substeps" ON task_substeps FOR ALL USING (true);

-- =====================================================
-- DONE! All 9 missing tables created.
-- =====================================================
