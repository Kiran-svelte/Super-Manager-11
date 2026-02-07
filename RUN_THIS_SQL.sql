-- =============================================================================
-- MISSING TABLES - Run this in Supabase SQL Editor
-- =============================================================================
-- https://supabase.com/dashboard/project/hpqmcdygbjdmvxfmvucf/sql/new
-- =============================================================================

-- Enable pgcrypto for encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =============================================================================
-- 1. AGENT TASKS (Task Orchestration)
-- =============================================================================
CREATE TABLE IF NOT EXISTS agent_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    task_type VARCHAR(100) NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    estimated_duration_minutes INTEGER,
    assignee_type VARCHAR(50) DEFAULT 'ai',
    parent_task_id UUID,
    conversation_id UUID,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    due_at TIMESTAMP WITH TIME ZONE,
    result JSONB DEFAULT '{}',
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_tasks_user_id ON agent_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON agent_tasks(status);

-- =============================================================================
-- 2. TASK DEPENDENCIES
-- =============================================================================
CREATE TABLE IF NOT EXISTS task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL,
    depends_on_task_id UUID NOT NULL,
    dependency_type VARCHAR(50) DEFAULT 'finish_to_start',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(task_id, depends_on_task_id)
);

-- =============================================================================
-- 3. WORKFLOW TEMPLATES
-- =============================================================================
CREATE TABLE IF NOT EXISTS workflow_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    trigger_type VARCHAR(100) NOT NULL,
    steps JSONB NOT NULL DEFAULT '[]',
    variables JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- 4. WORKFLOW EXECUTIONS
-- =============================================================================
CREATE TABLE IF NOT EXISTS workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL,
    user_id UUID NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    current_step INTEGER DEFAULT 0,
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_logs JSONB DEFAULT '[]',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- 5. AUTONOMOUS OPERATIONS
-- =============================================================================
CREATE TABLE IF NOT EXISTS autonomous_operations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    operation_type VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    requires_approval BOOLEAN DEFAULT FALSE,
    approved_at TIMESTAMP WITH TIME ZONE,
    executed_at TIMESTAMP WITH TIME ZONE,
    result JSONB DEFAULT '{}',
    autonomous_level INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- 6. USER ACCESS TOKENS
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_access_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    token_type VARCHAR(50) NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    scopes JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, service_name)
);

-- =============================================================================
-- 7. DELEGATED PERMISSIONS
-- =============================================================================
CREATE TABLE IF NOT EXISTS delegated_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    permission_type VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    allowed_actions JSONB DEFAULT '[]',
    conditions JSONB DEFAULT '{}',
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- 8. AI IDENTITIES (For AI's own Gmail/accounts)
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_identities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    gmail_address VARCHAR(255) NOT NULL,
    gmail_app_password_encrypted TEXT,
    identity_name VARCHAR(255) DEFAULT 'AI Assistant',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    last_email_check TIMESTAMP WITH TIME ZONE,
    capabilities JSONB DEFAULT '["send_email", "read_email", "sign_up_services"]',
    UNIQUE(user_id)
);

-- =============================================================================
-- 9. AI SERVICE ACCOUNTS (Services AI signed up for)
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_service_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    identity_id UUID NOT NULL,
    service_name VARCHAR(255) NOT NULL,
    username VARCHAR(255),
    email_used VARCHAR(255),
    password_encrypted TEXT,
    api_key_encrypted TEXT,
    signup_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'active',
    capabilities JSONB DEFAULT '[]',
    free_tier_info JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    UNIQUE(identity_id, service_name)
);

-- =============================================================================
-- 10. AI DECISION LOG (For responsible AI tracking)
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_decision_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    identity_id UUID NOT NULL,
    decision_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    reasoning TEXT,
    confidence DECIMAL(3,2) DEFAULT 1.0,
    user_approved BOOLEAN,
    outcome VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- 11. AI COMMITMENTS (Promises AI made)
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_commitments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    identity_id UUID NOT NULL,
    commitment_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    due_date TIMESTAMP WITH TIME ZONE,
    fulfilled_at TIMESTAMP WITH TIME ZONE,
    related_task_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- 12. BLOCKED SERVICES (Services requiring phone/KYC)
-- =============================================================================
CREATE TABLE IF NOT EXISTS blocked_services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(255) NOT NULL UNIQUE,
    block_reason VARCHAR(100) NOT NULL,
    alternative_service VARCHAR(255),
    requires_user_help BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert common blocked services
INSERT INTO blocked_services (service_name, block_reason, alternative_service, notes) VALUES
('whatsapp', 'phone_verification', 'telegram', 'Requires mobile number verification'),
('twitter', 'phone_verification', 'mastodon', 'Requires phone for new accounts'),
('facebook', 'phone_verification', 'reddit', 'Requires phone verification'),
('instagram', 'phone_verification', 'pixelfed', 'Linked to Facebook, needs phone'),
('linkedin', 'phone_verification', 'github', 'Professional network needs phone'),
('paypal', 'kyc_required', 'stripe', 'Requires KYC verification'),
('stripe_full', 'kyc_required', 'razorpay', 'Full features need KYC'),
('aws', 'credit_card_required', 'cloudflare', 'Needs credit card'),
('gcp', 'credit_card_required', 'cloudflare', 'Needs credit card'),
('azure', 'credit_card_required', 'cloudflare', 'Needs credit card'),
('aadhaar', 'government_id', NULL, 'Government ID - user must provide'),
('pan', 'government_id', NULL, 'Tax ID - user must provide'),
('bank_api', 'kyc_required', NULL, 'Banking APIs need full KYC')
ON CONFLICT (service_name) DO NOTHING;

-- =============================================================================
-- 13. SENSITIVE DATA REQUESTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS sensitive_data_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    data_type VARCHAR(100) NOT NULL,
    purpose TEXT NOT NULL,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '5 minutes',
    provided_at TIMESTAMP WITH TIME ZONE,
    is_used BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- =============================================================================
-- TRIGGERS FOR updated_at
-- =============================================================================
CREATE TRIGGER update_agent_tasks_updated_at
    BEFORE UPDATE ON agent_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_templates_updated_at
    BEFORE UPDATE ON workflow_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_executions_updated_at
    BEFORE UPDATE ON workflow_executions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_autonomous_operations_updated_at
    BEFORE UPDATE ON autonomous_operations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_access_tokens_updated_at
    BEFORE UPDATE ON user_access_tokens
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_identities_updated_at
    BEFORE UPDATE ON ai_identities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- RLS POLICIES
-- =============================================================================
ALTER TABLE agent_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_dependencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE autonomous_operations ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_access_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE delegated_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_identities ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_service_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_decision_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_commitments ENABLE ROW LEVEL SECURITY;
ALTER TABLE blocked_services ENABLE ROW LEVEL SECURITY;
ALTER TABLE sensitive_data_requests ENABLE ROW LEVEL SECURITY;

-- Service role policies (full access)
CREATE POLICY "Service role access agent_tasks" ON agent_tasks FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role access task_dependencies" ON task_dependencies FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role access workflow_templates" ON workflow_templates FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role access workflow_executions" ON workflow_executions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role access autonomous_operations" ON autonomous_operations FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role access user_access_tokens" ON user_access_tokens FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role access delegated_permissions" ON delegated_permissions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role access ai_identities" ON ai_identities FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role access ai_service_accounts" ON ai_service_accounts FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role access ai_decision_log" ON ai_decision_log FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role access ai_commitments" ON ai_commitments FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role access blocked_services" ON blocked_services FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role access sensitive_data_requests" ON sensitive_data_requests FOR ALL USING (true) WITH CHECK (true);

-- =============================================================================
-- DONE! All 13 missing tables created.
-- =============================================================================
