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
