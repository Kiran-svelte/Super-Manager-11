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
