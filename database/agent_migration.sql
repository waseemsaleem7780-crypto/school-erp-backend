-- ============================================
-- Agent Migration — Guardians table extend
-- ============================================

-- 1. WhatsApp number add karo (agar phone se alag ho)
ALTER TABLE guardians 
ADD COLUMN IF NOT EXISTS whatsapp_number VARCHAR(20);

-- 2. Verification status (OTP verify ke liye)
ALTER TABLE guardians 
ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;

-- 3. Last verified timestamp (audit ke liye)
ALTER TABLE guardians 
ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP;

-- ============================================
-- Agent Logs Table — har sawal/jawab save
-- ============================================
CREATE TABLE IF NOT EXISTS agent_logs (
    id SERIAL PRIMARY KEY,
    guardian_id INTEGER,
    student_id INTEGER,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    intent VARCHAR(100),
    tools_used TEXT,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guardian_id) REFERENCES guardians(id),
    FOREIGN KEY (student_id) REFERENCES students(id)
);

CREATE INDEX IF NOT EXISTS idx_agent_logs_guardian 
ON agent_logs(guardian_id);

CREATE INDEX IF NOT EXISTS idx_agent_logs_created 
ON agent_logs(created_at DESC);

-- ============================================
-- Agent Settings — school-level config
-- ============================================
CREATE TABLE IF NOT EXISTS agent_settings (
    id SERIAL PRIMARY KEY,
    school_id INTEGER NOT NULL UNIQUE,
    is_enabled BOOLEAN DEFAULT TRUE,
    welcome_message TEXT,
    language VARCHAR(20) DEFAULT 'ur',
    escalate_to_teacher BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
