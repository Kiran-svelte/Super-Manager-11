-- =============================================================================
-- AGENT DATABASE SCHEMA
-- =============================================================================
-- Run this in Supabase SQL Editor
-- This creates all tables for the new Agent system
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- USERS TABLE
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

-- Index for email lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- =============================================================================
-- CONTACTS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    telegram_id VARCHAR(100),
    relationship VARCHAR(50) DEFAULT 'other',  -- friend, colleague, family, client, etc.
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for lookups
CREATE INDEX IF NOT EXISTS idx_contacts_user_id ON contacts(user_id);
CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(name);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);

-- =============================================================================
-- PREFERENCES TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,  -- fashion, travel, meetings, food, etc.
    key VARCHAR(255) NOT NULL,  -- color, style, airline, meeting_duration, etc.
    value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, category, key)
);

-- Index for lookups
CREATE INDEX IF NOT EXISTS idx_preferences_user_id ON preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_preferences_category ON preferences(category);

-- =============================================================================
-- CONVERSATIONS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    expert_persona VARCHAR(100),  -- executive_assistant, fashion_designer, etc.
    status VARCHAR(50) DEFAULT 'active',  -- active, archived
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for lookups
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);

-- =============================================================================
-- MESSAGES TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- user, assistant, system
    content TEXT NOT NULL,
    actions_taken JSONB DEFAULT '[]',  -- Actions executed in this message
    expert_persona VARCHAR(100),
    model_used VARCHAR(100),
    tokens_used INTEGER,
    latency_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for lookups
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- =============================================================================
-- MEETINGS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS meetings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    meeting_link VARCHAR(1000),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER DEFAULT 30,
    platform VARCHAR(50) DEFAULT 'jitsi',  -- jitsi, zoom, google_meet, teams
    participants JSONB DEFAULT '[]',  -- [{name, email, phone}]
    invites_sent BOOLEAN DEFAULT FALSE,
    calendar_event_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'scheduled',  -- scheduled, in_progress, completed, cancelled
    created_from_message_id UUID REFERENCES messages(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for lookups
CREATE INDEX IF NOT EXISTS idx_meetings_user_id ON meetings(user_id);
CREATE INDEX IF NOT EXISTS idx_meetings_start_time ON meetings(start_time);
CREATE INDEX IF NOT EXISTS idx_meetings_status ON meetings(status);

-- =============================================================================
-- REMINDERS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    remind_at TIMESTAMP WITH TIME ZONE NOT NULL,
    channel VARCHAR(50) DEFAULT 'all',  -- email, telegram, sms, all
    is_sent BOOLEAN DEFAULT FALSE,
    recurrence VARCHAR(50),  -- once, daily, weekly, monthly
    reference_type VARCHAR(50),  -- meeting, task, custom
    reference_id UUID,
    created_from_message_id UUID REFERENCES messages(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for lookups
CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_reminders_remind_at ON reminders(remind_at);
CREATE INDEX IF NOT EXISTS idx_reminders_is_sent ON reminders(is_sent);

-- =============================================================================
-- TASKS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, in_progress, completed, cancelled
    priority VARCHAR(20) DEFAULT 'medium',  -- low, medium, high, urgent
    due_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    assignee VARCHAR(255),
    category VARCHAR(100),
    tags JSONB DEFAULT '[]',
    created_from_message_id UUID REFERENCES messages(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for lookups
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);

-- =============================================================================
-- EMAILS TABLE (Track sent emails)
-- =============================================================================
CREATE TABLE IF NOT EXISTS emails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    to_email VARCHAR(255) NOT NULL,
    to_name VARCHAR(255),
    subject VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'sent',  -- sent, failed, pending
    error_message TEXT,
    meeting_id UUID REFERENCES meetings(id),
    created_from_message_id UUID REFERENCES messages(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for lookups
CREATE INDEX IF NOT EXISTS idx_emails_user_id ON emails(user_id);
CREATE INDEX IF NOT EXISTS idx_emails_sent_at ON emails(sent_at);

-- =============================================================================
-- FASHION PREFERENCES TABLE (For fashion designer persona)
-- =============================================================================
CREATE TABLE IF NOT EXISTS fashion_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body_type VARCHAR(50),  -- athletic, slim, average, plus
    skin_tone VARCHAR(50),  -- fair, medium, olive, dark
    height_cm INTEGER,
    weight_kg INTEGER,
    preferred_colors JSONB DEFAULT '[]',
    avoided_colors JSONB DEFAULT '[]',
    preferred_styles JSONB DEFAULT '[]',  -- casual, formal, bohemian, minimalist, etc.
    outfit_history JSONB DEFAULT '[]',  -- Past outfit suggestions
    occasions JSONB DEFAULT '{}',  -- occasion -> style preferences
    brands JSONB DEFAULT '[]',  -- Favorite brands
    budget_range VARCHAR(50),  -- budget, mid, luxury
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- TRAVEL PREFERENCES TABLE (For travel agent persona)
-- =============================================================================
CREATE TABLE IF NOT EXISTS travel_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preferred_airlines JSONB DEFAULT '[]',
    seat_preferences VARCHAR(50),  -- window, aisle, middle
    meal_preferences VARCHAR(100),  -- vegetarian, vegan, non-veg, jain
    hotel_preferences JSONB DEFAULT '{}',  -- star_rating, amenities
    travel_class VARCHAR(50),  -- economy, business, first
    passport_nationality VARCHAR(100),
    frequent_destinations JSONB DEFAULT '[]',
    trip_history JSONB DEFAULT '[]',
    budget_per_day INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- ACTION LOGS TABLE (Track all agent actions)
-- =============================================================================
CREATE TABLE IF NOT EXISTS action_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id),
    action_type VARCHAR(100) NOT NULL,  -- send_email, create_meeting, etc.
    action_params JSONB NOT NULL,
    result JSONB,
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for lookups
CREATE INDEX IF NOT EXISTS idx_action_logs_user_id ON action_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_action_logs_action_type ON action_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_action_logs_created_at ON action_logs(created_at);

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contacts_updated_at
    BEFORE UPDATE ON contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meetings_updated_at
    BEFORE UPDATE ON meetings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fashion_profiles_updated_at
    BEFORE UPDATE ON fashion_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_travel_profiles_updated_at
    BEFORE UPDATE ON travel_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================================================
-- Enable RLS on all tables

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE meetings ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE emails ENABLE ROW LEVEL SECURITY;
ALTER TABLE fashion_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE travel_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE action_logs ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- SERVICE ROLE POLICIES
-- =============================================================================
-- Allow service role to access all data (for backend)

CREATE POLICY "Service role has full access to users"
    ON users FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role has full access to contacts"
    ON contacts FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role has full access to preferences"
    ON preferences FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role has full access to conversations"
    ON conversations FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role has full access to messages"
    ON messages FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role has full access to meetings"
    ON meetings FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role has full access to reminders"
    ON reminders FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role has full access to tasks"
    ON tasks FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role has full access to emails"
    ON emails FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role has full access to fashion_profiles"
    ON fashion_profiles FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role has full access to travel_profiles"
    ON travel_profiles FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role has full access to action_logs"
    ON action_logs FOR ALL
    USING (true)
    WITH CHECK (true);

-- =============================================================================
-- DONE!
-- =============================================================================
-- Your database is ready for the Agent system.
-- 
-- Tables created:
-- - users: User profiles
-- - contacts: User's address book
-- - preferences: User preferences by category
-- - conversations: Chat sessions
-- - messages: Individual messages
-- - meetings: Scheduled meetings
-- - reminders: Scheduled reminders
-- - tasks: User tasks
-- - emails: Sent email logs
-- - fashion_profiles: Fashion preferences (for fashion designer persona)
-- - travel_profiles: Travel preferences (for travel agent persona)
-- - action_logs: All actions taken by the agent
-- =============================================================================


-- =============================================================================
-- TASK ORCHESTRATION SCHEMA - Additional tables for task tracking
-- =============================================================================

-- =============================================================================
-- ORCHESTRATED TASKS TABLE (Main task with progress tracking)
-- =============================================================================
CREATE TABLE IF NOT EXISTS orchestrated_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Task info
    title VARCHAR(500) NOT NULL,
    description TEXT,
    task_type VARCHAR(100) NOT NULL,  -- meeting, email, reminder, research, etc.
    
    -- Progress tracking
    progress_percent INTEGER DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
    status VARCHAR(50) DEFAULT 'pending',  -- pending, in_progress, waiting_input, completed, failed, cancelled
    
    -- Timing
    estimated_completion TIMESTAMP WITH TIME ZONE,
    actual_completion TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    
    -- User input requirements
    needs_user_input BOOLEAN DEFAULT FALSE,
    input_prompt TEXT,  -- What to ask user
    input_options JSONB DEFAULT '[]',  -- Possible options for user
    user_input_received JSONB,  -- What user provided
    
    -- Related entities
    meeting_id UUID REFERENCES meetings(id),
    message_id UUID REFERENCES messages(id),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_orchestrated_tasks_user_id ON orchestrated_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_orchestrated_tasks_status ON orchestrated_tasks(status);
CREATE INDEX IF NOT EXISTS idx_orchestrated_tasks_progress ON orchestrated_tasks(progress_percent);

-- =============================================================================
-- TASK SUBSTEPS TABLE (Individual steps within a task)
-- =============================================================================
CREATE TABLE IF NOT EXISTS task_substeps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES orchestrated_tasks(id) ON DELETE CASCADE,
    
    -- Step info
    step_number INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Progress
    status VARCHAR(50) DEFAULT 'pending',  -- pending, in_progress, completed, failed, skipped, waiting
    progress_weight INTEGER DEFAULT 10,  -- Contribution to total progress (sum should = 100)
    
    -- Execution
    action_type VARCHAR(100),  -- send_email, create_meeting, wait_for_event, etc.
    action_params JSONB DEFAULT '{}',
    result JSONB,
    error_message TEXT,
    
    -- Timing
    scheduled_at TIMESTAMP WITH TIME ZONE,  -- When to execute (for scheduled steps)
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Detection (for auto-completing steps)
    detection_type VARCHAR(50),  -- webhook, polling, manual, scheduled
    detection_config JSONB DEFAULT '{}',  -- Config for detection
    
    -- Dependencies
    depends_on UUID[],  -- Array of substep IDs that must complete first
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_task_substeps_task_id ON task_substeps(task_id);
CREATE INDEX IF NOT EXISTS idx_task_substeps_status ON task_substeps(status);
CREATE INDEX IF NOT EXISTS idx_task_substeps_scheduled ON task_substeps(scheduled_at);

-- =============================================================================
-- SCHEDULED JOBS TABLE (For reminders, follow-ups, etc.)
-- =============================================================================
CREATE TABLE IF NOT EXISTS scheduled_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Job info
    job_type VARCHAR(100) NOT NULL,  -- send_reminder, check_meeting_status, etc.
    job_params JSONB NOT NULL,
    
    -- Scheduling
    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed, cancelled
    
    -- Retry logic
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    last_error TEXT,
    
    -- Related entities
    task_id UUID REFERENCES orchestrated_tasks(id) ON DELETE CASCADE,
    substep_id UUID REFERENCES task_substeps(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Execution
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_status ON scheduled_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_scheduled_for ON scheduled_jobs(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_task_id ON scheduled_jobs(task_id);

-- =============================================================================
-- MEETING PARTICIPANTS TRACKING (For detecting joins/leaves)
-- =============================================================================
CREATE TABLE IF NOT EXISTS meeting_participants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    
    -- Participant info
    participant_name VARCHAR(255),
    participant_email VARCHAR(255),
    participant_id VARCHAR(255),  -- Platform-specific ID
    
    -- Status
    invite_sent BOOLEAN DEFAULT FALSE,
    invite_opened BOOLEAN DEFAULT FALSE,
    reminder_sent BOOLEAN DEFAULT FALSE,
    joined BOOLEAN DEFAULT FALSE,
    left BOOLEAN DEFAULT FALSE,
    
    -- Timing
    invite_sent_at TIMESTAMP WITH TIME ZONE,
    joined_at TIMESTAMP WITH TIME ZONE,
    left_at TIMESTAMP WITH TIME ZONE,
    
    -- Duration
    total_duration_seconds INTEGER,
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_meeting_participants_meeting ON meeting_participants(meeting_id);
CREATE INDEX IF NOT EXISTS idx_meeting_participants_email ON meeting_participants(participant_email);

-- =============================================================================
-- NOTIFICATIONS TABLE (For in-app, push, email notifications)
-- =============================================================================
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Notification content
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,  -- task_update, reminder, alert, info
    priority VARCHAR(20) DEFAULT 'normal',  -- low, normal, high, urgent
    
    -- Delivery
    channels JSONB DEFAULT '["in_app"]',  -- in_app, push, email, telegram
    delivered_channels JSONB DEFAULT '[]',
    
    -- Status
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,
    
    -- Links
    action_url VARCHAR(500),
    task_id UUID REFERENCES orchestrated_tasks(id),
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at);

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Auto-update timestamp for orchestrated_tasks
CREATE TRIGGER update_orchestrated_tasks_updated_at
    BEFORE UPDATE ON orchestrated_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-update timestamp for task_substeps
CREATE TRIGGER update_task_substeps_updated_at
    BEFORE UPDATE ON task_substeps
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-update timestamp for scheduled_jobs
CREATE TRIGGER update_scheduled_jobs_updated_at
    BEFORE UPDATE ON scheduled_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-update timestamp for meeting_participants
CREATE TRIGGER update_meeting_participants_updated_at
    BEFORE UPDATE ON meeting_participants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- RLS POLICIES
-- =============================================================================

ALTER TABLE orchestrated_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_substeps ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduled_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE meeting_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to orchestrated_tasks"
    ON orchestrated_tasks FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role has full access to task_substeps"
    ON task_substeps FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role has full access to scheduled_jobs"
    ON scheduled_jobs FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role has full access to meeting_participants"
    ON meeting_participants FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role has full access to notifications"
    ON notifications FOR ALL USING (true) WITH CHECK (true);

-- =============================================================================
-- FUNCTION: Calculate task progress from substeps
-- =============================================================================
CREATE OR REPLACE FUNCTION calculate_task_progress(p_task_id UUID)
RETURNS INTEGER AS $$
DECLARE
    total_weight INTEGER;
    completed_weight INTEGER;
    progress INTEGER;
BEGIN
    SELECT 
        COALESCE(SUM(progress_weight), 0),
        COALESCE(SUM(CASE WHEN status = 'completed' THEN progress_weight ELSE 0 END), 0)
    INTO total_weight, completed_weight
    FROM task_substeps
    WHERE task_id = p_task_id;
    
    IF total_weight = 0 THEN
        RETURN 0;
    END IF;
    
    progress := (completed_weight * 100) / total_weight;
    RETURN progress;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- FUNCTION: Auto-update task progress when substep changes
-- =============================================================================
CREATE OR REPLACE FUNCTION update_task_progress()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE orchestrated_tasks
    SET 
        progress_percent = calculate_task_progress(NEW.task_id),
        status = CASE 
            WHEN calculate_task_progress(NEW.task_id) = 100 THEN 'completed'
            WHEN calculate_task_progress(NEW.task_id) > 0 THEN 'in_progress'
            ELSE status
        END,
        actual_completion = CASE 
            WHEN calculate_task_progress(NEW.task_id) = 100 THEN NOW()
            ELSE actual_completion
        END
    WHERE id = NEW.task_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_task_progress
    AFTER UPDATE OF status ON task_substeps
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION update_task_progress();

-- =============================================================================
-- DONE!
-- =============================================================================


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
