-- =============================================================================
-- AI IDENTITY SYSTEM SCHEMA
-- =============================================================================
-- Each user creates a dedicated Gmail account for their AI agent
-- The AI uses this email to sign up for services, get API keys, etc.
-- =============================================================================

-- Enable encryption extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- AI IDENTITIES TABLE
-- The AI's digital identity (Gmail account assigned to it)
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_identities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- AI Identity Info
    email VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) DEFAULT 'AI Assistant',
    
    -- Authentication (encrypted)
    -- We store encrypted credentials, never plain text
    auth_type VARCHAR(50) NOT NULL DEFAULT 'app_password',  -- app_password, oauth
    
    -- For App Password auth (encrypted with pgcrypto)
    encrypted_password TEXT,  -- Encrypted app password
    
    -- For OAuth auth
    oauth_access_token TEXT,
    oauth_refresh_token TEXT,
    oauth_expires_at TIMESTAMP WITH TIME ZONE,
    oauth_scope TEXT,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending_setup',  -- pending_setup, active, suspended, verification_needed
    last_verified_at TIMESTAMP WITH TIME ZONE,
    verification_error TEXT,
    
    -- Capabilities unlocked
    can_send_email BOOLEAN DEFAULT FALSE,
    can_read_email BOOLEAN DEFAULT FALSE,
    can_signup_services BOOLEAN DEFAULT FALSE,
    
    -- Usage limits
    daily_email_limit INTEGER DEFAULT 100,
    emails_sent_today INTEGER DEFAULT 0,
    last_email_reset DATE DEFAULT CURRENT_DATE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- One AI identity per user
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_ai_identities_user_id ON ai_identities(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_identities_email ON ai_identities(email);

-- =============================================================================
-- AI SERVICE ACCOUNTS TABLE
-- Services the AI has signed up for with its identity
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_service_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ai_identity_id UUID NOT NULL REFERENCES ai_identities(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Service info
    service_name VARCHAR(255) NOT NULL,  -- github, openai, twilio, sendgrid, etc.
    service_url VARCHAR(500),
    account_email VARCHAR(255),  -- May differ from AI email for some services
    account_username VARCHAR(255),
    
    -- API credentials (encrypted)
    encrypted_api_key TEXT,
    encrypted_api_secret TEXT,
    additional_creds JSONB DEFAULT '{}',  -- Encrypted additional credentials
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',  -- active, expired, rate_limited, suspended
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    daily_limit INTEGER,
    monthly_limit INTEGER,
    
    -- Verification status
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,  -- Some services need phone
    verification_pending BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    capabilities JSONB DEFAULT '[]',  -- What this service can do
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(ai_identity_id, service_name)
);

CREATE INDEX IF NOT EXISTS idx_ai_service_accounts_identity ON ai_service_accounts(ai_identity_id);
CREATE INDEX IF NOT EXISTS idx_ai_service_accounts_service ON ai_service_accounts(service_name);

-- =============================================================================
-- SENSITIVE DATA REQUESTS TABLE
-- When AI needs OTP/PAN/Aadhaar, tracked here and deleted after use
-- =============================================================================
CREATE TABLE IF NOT EXISTS sensitive_data_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Request info
    data_type VARCHAR(50) NOT NULL,  -- otp, pan, aadhaar, phone_otp, bank_otp, etc.
    purpose TEXT NOT NULL,  -- Why the AI needs this
    service_name VARCHAR(255),  -- Which service requires this
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending',  -- pending, received, used, expired, cancelled
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    received_at TIMESTAMP WITH TIME ZONE,
    used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,  -- Auto-delete after this
    
    -- The actual data is NOT stored permanently
    -- It's only held in memory during the session
    data_received BOOLEAN DEFAULT FALSE,
    
    -- Audit
    audit_log JSONB DEFAULT '[]',  -- Track every access
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sensitive_requests_user ON sensitive_data_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_sensitive_requests_status ON sensitive_data_requests(status);

-- Auto-delete expired sensitive data requests
CREATE OR REPLACE FUNCTION cleanup_sensitive_requests()
RETURNS VOID AS $$
BEGIN
    DELETE FROM sensitive_data_requests 
    WHERE expires_at < NOW() 
    OR (status = 'used' AND used_at < NOW() - INTERVAL '5 minutes');
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- AI DECISION LOG TABLE
-- Every major decision the AI makes, for accountability
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_decision_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255),
    
    -- Decision info
    decision_type VARCHAR(100) NOT NULL,  -- action, response, signup, api_call, etc.
    decision_summary TEXT NOT NULL,
    reasoning TEXT,  -- Why the AI made this decision
    
    -- What was proposed vs executed
    proposed_action JSONB,
    executed_action JSONB,
    
    -- User interaction
    required_confirmation BOOLEAN DEFAULT FALSE,
    user_confirmed BOOLEAN,
    user_feedback TEXT,
    
    -- Outcome
    outcome VARCHAR(50),  -- success, failed, cancelled, pending
    outcome_details JSONB,
    
    -- Consistency tracking
    related_decisions UUID[],  -- Previous related decisions
    consistency_score FLOAT,  -- How consistent with past decisions
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_decisions_user ON ai_decision_log(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_decisions_type ON ai_decision_log(decision_type);
CREATE INDEX IF NOT EXISTS idx_ai_decisions_time ON ai_decision_log(created_at);

-- =============================================================================
-- AI COMMITMENT TABLE
-- Promises/commitments the AI has made that it must keep
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_commitments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Commitment info
    commitment_text TEXT NOT NULL,  -- What the AI committed to
    context TEXT,  -- Original conversation context
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',  -- active, fulfilled, broken, cancelled
    fulfilled_at TIMESTAMP WITH TIME ZONE,
    
    -- Linked entities
    related_task_id UUID REFERENCES orchestrated_tasks(id),
    related_decision_id UUID REFERENCES ai_decision_log(id),
    
    -- Metadata
    importance VARCHAR(20) DEFAULT 'normal',  -- low, normal, high, critical
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_ai_commitments_user ON ai_commitments(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_commitments_status ON ai_commitments(status);

-- =============================================================================
-- BLOCKED SERVICES TABLE
-- Services that require manual verification
-- =============================================================================
CREATE TABLE IF NOT EXISTS blocked_services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    service_name VARCHAR(255) NOT NULL UNIQUE,
    service_url VARCHAR(500),
    
    -- Why blocked
    block_reason VARCHAR(100) NOT NULL,  -- phone_verification, government_id, payment_required, etc.
    block_category VARCHAR(100),  -- verification, legal, technical, platform_rules
    
    -- Alternatives
    alternative_services JSONB DEFAULT '[]',  -- List of alternative services
    workaround_possible BOOLEAN DEFAULT FALSE,
    workaround_description TEXT,
    
    -- Metadata
    last_checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pre-populate with known blocked services
INSERT INTO blocked_services (service_name, block_reason, block_category, alternative_services) VALUES
    ('WhatsApp Business API', 'phone_verification', 'verification', '["Telegram Bot API", "Signal API"]'),
    ('Twitter/X API', 'phone_verification', 'verification', '["Mastodon API", "Bluesky API"]'),
    ('Facebook Graph API', 'phone_verification', 'verification', '["Telegram Bot API"]'),
    ('Instagram API', 'phone_verification', 'verification', '["Telegram Bot API"]'),
    ('LinkedIn API', 'business_verification', 'verification', '[]'),
    ('PayPal API', 'identity_verification', 'financial', '["Stripe", "Razorpay"]'),
    ('Stripe', 'business_verification', 'financial', '["Razorpay", "PayU"]'),
    ('AWS', 'payment_required', 'financial', '["Google Cloud Free Tier", "Azure Free Tier"]'),
    ('Google Cloud', 'payment_required', 'financial', '["Firebase Free Tier", "Supabase Free Tier"]'),
    ('Zoom API', 'payment_required', 'platform_rules', '["Jitsi Meet (free)", "Google Meet"]'),
    ('Aadhaar Services', 'government_id', 'legal', '[]'),
    ('DigiLocker', 'government_id', 'legal', '[]'),
    ('UPI Apps', 'phone_verification', 'financial', '[]'),
    ('Banking APIs', 'kyc_required', 'financial', '[]')
ON CONFLICT (service_name) DO NOTHING;

-- =============================================================================
-- ENCRYPTION HELPER FUNCTIONS
-- =============================================================================

-- Encrypt sensitive data
CREATE OR REPLACE FUNCTION encrypt_sensitive(data TEXT, secret TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN encode(pgp_sym_encrypt(data, secret), 'base64');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Decrypt sensitive data
CREATE OR REPLACE FUNCTION decrypt_sensitive(encrypted_data TEXT, secret TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(decode(encrypted_data, 'base64'), secret);
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- RLS POLICIES
-- =============================================================================

ALTER TABLE ai_identities ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_service_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE sensitive_data_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_decision_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_commitments ENABLE ROW LEVEL SECURITY;
ALTER TABLE blocked_services ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role access ai_identities" ON ai_identities FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role access ai_service_accounts" ON ai_service_accounts FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role access sensitive_data_requests" ON sensitive_data_requests FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role access ai_decision_log" ON ai_decision_log FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role access ai_commitments" ON ai_commitments FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role access blocked_services" ON blocked_services FOR ALL USING (true) WITH CHECK (true);

-- =============================================================================
-- TRIGGERS
-- =============================================================================

CREATE TRIGGER update_ai_identities_updated_at
    BEFORE UPDATE ON ai_identities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_service_accounts_updated_at
    BEFORE UPDATE ON ai_service_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- DONE! Run this after schema_orchestration.sql
-- =============================================================================
