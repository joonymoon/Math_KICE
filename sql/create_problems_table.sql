-- ============================================
-- KICE Math Problems Table
-- 최종 업데이트: 2026-02-04
-- ============================================

-- Drop existing table if needed
-- DROP TABLE IF EXISTS hints CASCADE;
-- DROP TABLE IF EXISTS problems CASCADE;

-- Problems table
CREATE TABLE IF NOT EXISTS problems (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- ============================================
    -- 핵심 식별자
    -- 형식: {year}_{exam}_Q{question_no:02d}
    -- 예: 2026_CSAT_Q01, 2025_KICE6_Q15
    -- ============================================
    problem_id VARCHAR(50) UNIQUE NOT NULL,

    -- Source info
    year INT NOT NULL,
    exam VARCHAR(20) NOT NULL,  -- CSAT, KICE6, KICE9
    question_no INT NOT NULL,
    score INT DEFAULT 0,  -- 배점 (2, 3, 4)

    -- Content
    subject VARCHAR(20),  -- Math1, Math2
    unit VARCHAR(100),  -- 단원
    extract_text TEXT,  -- PDF 추출 텍스트

    -- Answer & Solution
    answer VARCHAR(50),  -- 자동 추출 정답
    answer_verified VARCHAR(50),  -- 검수 확정 정답
    score_verified INT,  -- 검수 확정 배점
    solution TEXT,  -- 풀이

    -- Hints (3 stages)
    hint_1 TEXT,  -- 개념 방향 (Stage 1)
    hint_2 TEXT,  -- 핵심 전환 (Stage 2)
    hint_3 TEXT,  -- 결정적 한 줄 (Stage 3)

    -- Metadata
    difficulty INT DEFAULT 3,  -- 1(쉬움) ~ 5(어려움)
    intent_1 TEXT,  -- 출제 의도

    -- ============================================
    -- 이미지 URL (중요!)
    -- Supabase Storage 공개 URL 형식:
    -- https://{project}.supabase.co/storage/v1/object/public/problem-images/{problem_id}.png
    --
    -- 파일명 규칙: {problem_id}.png (예: 2026_CSAT_Q01.png)
    -- 이미지 품질: 250 DPI → 1600px 폭 다운스케일
    -- ============================================
    source_ref VARCHAR(500),  -- 원본 PDF Google Drive 링크
    image_url VARCHAR(500),  -- Supabase Storage 공개 URL
    page_images_folder VARCHAR(500),  -- 이미지 폴더 링크

    -- ============================================
    -- 상태 관리
    -- needs_review: 자동 추출 완료, 검수 필요
    -- ready: 검수 완료, 발송 가능
    -- sent: 카카오톡으로 발송 완료
    -- hold: 보류
    -- inactive: 비활성화
    -- ============================================
    status VARCHAR(20) DEFAULT 'needs_review',
    notion_page_id VARCHAR(100),  -- Notion 페이지 ID

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- ============================================
    -- 제약조건
    -- ============================================
    CONSTRAINT valid_exam CHECK (exam IN ('CSAT', 'KICE6', 'KICE9')),
    CONSTRAINT valid_status CHECK (status IN ('needs_review', 'ready', 'sent', 'hold', 'inactive'))
);

-- Create index for common queries
CREATE INDEX IF NOT EXISTS idx_problems_year ON problems(year);
CREATE INDEX IF NOT EXISTS idx_problems_exam ON problems(exam);
CREATE INDEX IF NOT EXISTS idx_problems_status ON problems(status);
CREATE INDEX IF NOT EXISTS idx_problems_subject ON problems(subject);

-- Hints table (optional, can use columns in problems table instead)
CREATE TABLE IF NOT EXISTS hints (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    problem_id VARCHAR(50) REFERENCES problems(problem_id) ON DELETE CASCADE,
    stage INT NOT NULL,  -- 1, 2, 3
    hint_type VARCHAR(50),  -- concept_direction, key_transformation, decisive_line
    hint_text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(problem_id, stage)
);

-- User problem history (for tracking sent problems)
CREATE TABLE IF NOT EXISTS user_problems (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    problem_id VARCHAR(50) REFERENCES problems(problem_id) ON DELETE CASCADE,

    -- Status
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    viewed_at TIMESTAMPTZ,
    answered_at TIMESTAMPTZ,

    -- User response
    user_answer VARCHAR(50),
    is_correct BOOLEAN,
    hints_used INT DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, problem_id)
);

CREATE INDEX IF NOT EXISTS idx_user_problems_user ON user_problems(user_id);
CREATE INDEX IF NOT EXISTS idx_user_problems_problem ON user_problems(problem_id);

-- Enable Row Level Security
ALTER TABLE problems ENABLE ROW LEVEL SECURITY;
ALTER TABLE hints ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_problems ENABLE ROW LEVEL SECURITY;

-- Allow public read for problems
CREATE POLICY "Allow public read" ON problems FOR SELECT USING (true);
CREATE POLICY "Allow service insert" ON problems FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow service update" ON problems FOR UPDATE USING (true);

-- Allow public read for hints
CREATE POLICY "Allow public read hints" ON hints FOR SELECT USING (true);
CREATE POLICY "Allow service insert hints" ON hints FOR INSERT WITH CHECK (true);

-- User problems policies
CREATE POLICY "Users can read own history" ON user_problems FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Service can insert" ON user_problems FOR INSERT WITH CHECK (true);
CREATE POLICY "Service can update" ON user_problems FOR UPDATE USING (true);
