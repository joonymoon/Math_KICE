-- ============================================
-- KICE 수학 문제 관리 시스템 Supabase 스키마 v2
-- Make.com 자동화 파이프라인 최적화 버전
-- ============================================

-- 기존 테이블 삭제 (새로 시작할 경우만)
-- DROP TABLE IF EXISTS hint_requests, deliveries, daily_schedules, hints, problems, users, units CASCADE;

-- ============================================
-- 1. 문제 테이블 (problems) - Make.com 매핑 기준
-- ============================================
CREATE TABLE problems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- ============================================
    -- 핵심 식별자 (Make에서 자동 생성)
    -- ============================================
    problem_id VARCHAR(50) UNIQUE NOT NULL,  -- 예: 2024_CSAT_COMMON_Q13

    -- ============================================
    -- 출처 정보 (Make 시나리오 A에서 파일명 파싱)
    -- ============================================
    year INTEGER NOT NULL,
    exam VARCHAR(10) NOT NULL,  -- CSAT, KICE6, KICE9 (exam_type → exam으로 간소화)
    question_no INTEGER NOT NULL,

    -- ============================================
    -- 분류 정보 (검수에서 확정, 초기값 null 허용)
    -- ============================================
    subject VARCHAR(10),         -- Math1, Math2 (검수 후 확정)
    unit VARCHAR(50),            -- 세부 단원 (검수 후 확정)
    topic VARCHAR(100),          -- 구체적 내용/주제

    -- ============================================
    -- 배점 및 정답 (Make에서 자동 추출, 검수로 확정)
    -- ============================================
    score INTEGER,               -- 3 or 4 (자동 추출, null 가능)
    score_verified INTEGER,      -- 검수 후 확정된 배점
    answer VARCHAR(50),          -- 자동 추출된 정답
    answer_verified VARCHAR(50), -- 검수 후 확정된 정답
    answer_type VARCHAR(10) DEFAULT 'multiple',

    -- ============================================
    -- 텍스트 추출 (Make 시나리오 A에서 저장)
    -- ============================================
    extract_text TEXT,           -- PDF에서 추출한 원본 텍스트

    -- ============================================
    -- 문제 콘텐츠 (이미지/텍스트)
    -- ============================================
    problem_text TEXT,           -- 정제된 문제 텍스트 (LaTeX)
    problem_text_format VARCHAR(20) DEFAULT 'latex',
    problem_image_url TEXT,      -- Supabase Storage URL
    problem_image_key VARCHAR(200),
    choices JSONB,               -- {"1": "보기1", ...}

    -- ============================================
    -- 이미지 페이지 참조 (검수에서 입력)
    -- ============================================
    img_page_refs JSONB,         -- {"pages": ["p03", "p04"], "folder": "..."}

    -- ============================================
    -- 출처 참조
    -- ============================================
    source_ref TEXT,             -- Google Drive 원본 PDF 링크
    source_pdf_url TEXT,         -- KICE 공식 PDF 링크
    page_images_folder TEXT,     -- 페이지 이미지 폴더 링크

    -- ============================================
    -- 출제 의도 (검수에서 입력)
    -- ============================================
    intent_1 TEXT,               -- 출제의도 첫 번째 줄
    intent_2 TEXT,               -- 출제의도 두 번째 줄

    -- ============================================
    -- 풀이 (검수에서 입력)
    -- ============================================
    solution TEXT,               -- 상세 풀이 (LaTeX 지원)

    -- ============================================
    -- AI 분류 (선택적 자동화)
    -- ============================================
    confidence DECIMAL(3,2) DEFAULT 0,  -- AI 분류 신뢰도

    -- ============================================
    -- 난이도 정보 (적응형 학습용)
    -- ============================================
    difficulty INTEGER DEFAULT 3,        -- 1(쉬움) ~ 5(어려움), 검수자가 설정
    difficulty_auto DECIMAL(3,2),        -- 정답률 기반 자동 계산 (0.00 ~ 1.00)
    correct_rate DECIMAL(5,2),           -- 전체 정답률 (%)
    attempt_count INTEGER DEFAULT 0,     -- 총 시도 횟수

    -- ============================================
    -- 상태 관리
    -- ============================================
    status VARCHAR(20) DEFAULT 'needs_review',
    -- needs_review: 자동 추출 완료, 검수 필요
    -- ready: 검수 완료, 발송 가능
    -- hold: 보류
    -- inactive: 비활성화

    -- ============================================
    -- Notion 연동
    -- ============================================
    notion_page_id VARCHAR(50),  -- Notion 검수 카드 ID

    -- ============================================
    -- 타임스탬프
    -- ============================================
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- ============================================
    -- 제약조건
    -- ============================================
    CONSTRAINT valid_exam CHECK (exam IN ('CSAT', 'KICE6', 'KICE9')),
    CONSTRAINT valid_subject CHECK (subject IS NULL OR subject IN ('Math1', 'Math2')),
    CONSTRAINT valid_score CHECK (score IS NULL OR score IN (2, 3, 4)),
    CONSTRAINT valid_score_verified CHECK (score_verified IS NULL OR score_verified IN (2, 3, 4)),
    CONSTRAINT valid_status CHECK (status IN ('needs_review', 'ready', 'hold', 'inactive'))
);

-- ============================================
-- 2. 힌트 테이블 (hints) - 검수에서 입력
-- ============================================
CREATE TABLE hints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    problem_id VARCHAR(50) NOT NULL REFERENCES problems(problem_id) ON DELETE CASCADE,

    stage INTEGER NOT NULL,
    -- 1: 개념 방향
    -- 2: 핵심 전환
    -- 3: 결정적 한 줄

    hint_type VARCHAR(20) NOT NULL,
    hint_text TEXT NOT NULL,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(problem_id, stage),
    CONSTRAINT valid_stage CHECK (stage IN (1, 2, 3)),
    CONSTRAINT valid_hint_type CHECK (hint_type IN ('concept_direction', 'key_transformation', 'decisive_line'))
);

-- ============================================
-- 3. 사용자 테이블 (users)
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 인증 정보
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20) UNIQUE,
    kakao_id VARCHAR(100) UNIQUE,
    kakao_access_token TEXT,
    kakao_refresh_token TEXT,

    -- 프로필
    nickname VARCHAR(50),
    grade VARCHAR(10),  -- 고1, 고2, 고3, N수

    -- 설정
    daily_problem_count INTEGER DEFAULT 1,
    preferred_time TIME DEFAULT '07:00',
    hint_delay_minutes INTEGER DEFAULT 30,

    -- 통계
    total_solved INTEGER DEFAULT 0,
    correct_count INTEGER DEFAULT 0,

    -- ============================================
    -- 적응형 학습 (난이도 조절)
    -- ============================================
    current_level INTEGER DEFAULT 3,          -- 현재 학습 수준 (1~5)
    current_score_level INTEGER DEFAULT 3,    -- 현재 배점 수준 (2, 3, 4점)
    consecutive_correct INTEGER DEFAULT 0,    -- 연속 정답 횟수
    consecutive_wrong INTEGER DEFAULT 0,      -- 연속 오답 횟수

    -- 단원별 정답률 (JSONB로 저장)
    -- {"Math1_지수와로그": {"correct": 5, "total": 8}, ...}
    unit_stats JSONB DEFAULT '{}',

    -- 최근 학습 이력 (최근 10문제)
    recent_history JSONB DEFAULT '[]',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_current_level CHECK (current_level BETWEEN 1 AND 5),
    CONSTRAINT valid_score_level CHECK (current_score_level IN (2, 3, 4))
);

-- ============================================
-- 4. 발송 테이블 (deliveries)
-- ============================================
CREATE TABLE deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    problem_id VARCHAR(50) NOT NULL REFERENCES problems(problem_id),

    -- 발송 정보
    delivered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivery_method VARCHAR(20) DEFAULT 'kakao',
    hint_available_at TIMESTAMPTZ NOT NULL,

    -- 카카오 발송 결과
    kakao_message_id VARCHAR(100),
    kakao_send_result JSONB,

    -- 사용자 응답
    user_answer VARCHAR(50),
    answered_at TIMESTAMPTZ,
    is_correct BOOLEAN,
    time_spent_seconds INTEGER,

    -- 힌트 사용 기록
    hint_1_viewed_at TIMESTAMPTZ,
    hint_2_viewed_at TIMESTAMPTZ,
    hint_3_viewed_at TIMESTAMPTZ,

    -- 상태
    status VARCHAR(20) DEFAULT 'pending',

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_delivery_method CHECK (delivery_method IN ('push', 'kakao', 'sms', 'email')),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'viewed', 'answered', 'skipped', 'expired'))
);

-- ============================================
-- 5. 일일 스케줄 (daily_schedules)
-- ============================================
CREATE TABLE daily_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    scheduled_date DATE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    problem_id VARCHAR(50) NOT NULL REFERENCES problems(problem_id),
    scheduled_time TIME NOT NULL,

    status VARCHAR(20) DEFAULT 'scheduled',
    executed_at TIMESTAMPTZ,
    error_message TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(scheduled_date, user_id),
    CONSTRAINT valid_status CHECK (status IN ('scheduled', 'sent', 'failed', 'cancelled'))
);

-- ============================================
-- 6. 힌트 요청 로그 (hint_requests)
-- ============================================
CREATE TABLE hint_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    delivery_id UUID NOT NULL REFERENCES deliveries(id) ON DELETE CASCADE,
    stage INTEGER NOT NULL,

    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    was_available BOOLEAN NOT NULL,
    time_to_answer_after_hint INTEGER,

    CONSTRAINT valid_stage CHECK (stage IN (1, 2, 3))
);

-- ============================================
-- 7. 단원 마스터 (units)
-- ============================================
CREATE TABLE units (
    id SERIAL PRIMARY KEY,
    subject VARCHAR(10) NOT NULL,
    unit_code VARCHAR(20) NOT NULL UNIQUE,
    unit_name VARCHAR(50) NOT NULL,
    unit_name_ko VARCHAR(50) NOT NULL,
    display_order INTEGER NOT NULL,

    UNIQUE(subject, unit_code)
);

INSERT INTO units (subject, unit_code, unit_name, unit_name_ko, display_order) VALUES
-- 수학1
('Math1', 'M1_EXP_LOG', 'Exponential and Logarithm', '지수와 로그', 1),
('Math1', 'M1_EXP_LOG_FUNC', 'Exp/Log Functions', '지수함수와 로그함수', 2),
('Math1', 'M1_TRIG_FUNC', 'Trigonometric Functions', '삼각함수', 3),
('Math1', 'M1_TRIG_ADD', 'Trig Addition Formulas', '삼각함수 덧셈정리', 4),
('Math1', 'M1_SEQ', 'Sequences', '수열', 5),
('Math1', 'M1_SEQ_SUM', 'Series and Sum', '급수와 합', 6),
('Math1', 'M1_MATH_IND', 'Mathematical Induction', '수학적 귀납법', 7),
-- 수학2
('Math2', 'M2_LIMIT', 'Limits of Functions', '함수의 극한', 8),
('Math2', 'M2_CONT', 'Continuity', '함수의 연속', 9),
('Math2', 'M2_DIFF_DEF', 'Definition of Derivative', '미분계수와 도함수', 10),
('Math2', 'M2_DIFF_APP', 'Applications of Derivative', '도함수의 활용', 11),
('Math2', 'M2_INT_DEF', 'Definition of Integral', '부정적분과 정적분', 12),
('Math2', 'M2_INT_APP', 'Applications of Integral', '정적분의 활용', 13);

-- ============================================
-- 인덱스
-- ============================================
CREATE INDEX idx_problems_year_exam ON problems(year, exam);
CREATE INDEX idx_problems_subject_unit ON problems(subject, unit);
CREATE INDEX idx_problems_status ON problems(status);
CREATE INDEX idx_problems_question_no ON problems(year, exam, question_no);

CREATE INDEX idx_hints_problem_id ON hints(problem_id);
CREATE INDEX idx_deliveries_user_id ON deliveries(user_id);
CREATE INDEX idx_deliveries_status ON deliveries(status);
CREATE INDEX idx_schedules_date_status ON daily_schedules(scheduled_date, status);

-- ============================================
-- 함수: Upsert용 (Make에서 사용)
-- ============================================
CREATE OR REPLACE FUNCTION upsert_problem(
    p_problem_id VARCHAR(50),
    p_year INTEGER,
    p_exam VARCHAR(10),
    p_question_no INTEGER,
    p_score INTEGER DEFAULT NULL,
    p_extract_text TEXT DEFAULT NULL,
    p_source_ref TEXT DEFAULT NULL,
    p_page_images_folder TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_id UUID;
BEGIN
    INSERT INTO problems (problem_id, year, exam, question_no, score, extract_text, source_ref, page_images_folder)
    VALUES (p_problem_id, p_year, p_exam, p_question_no, p_score, p_extract_text, p_source_ref, p_page_images_folder)
    ON CONFLICT (problem_id) DO UPDATE SET
        score = COALESCE(EXCLUDED.score, problems.score),
        extract_text = COALESCE(EXCLUDED.extract_text, problems.extract_text),
        source_ref = COALESCE(EXCLUDED.source_ref, problems.source_ref),
        page_images_folder = COALESCE(EXCLUDED.page_images_folder, problems.page_images_folder),
        updated_at = NOW()
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 함수: 정답 업데이트 (Make 시나리오 B용)
-- ============================================
CREATE OR REPLACE FUNCTION update_answer(
    p_year INTEGER,
    p_exam VARCHAR(10),
    p_question_no INTEGER,
    p_answer VARCHAR(50)
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE problems
    SET answer = p_answer, updated_at = NOW()
    WHERE year = p_year AND exam = p_exam AND question_no = p_question_no;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 함수: 힌트 활성화 시간 자동 계산
-- ============================================
CREATE OR REPLACE FUNCTION calculate_hint_available_time()
RETURNS TRIGGER AS $$
BEGIN
    NEW.hint_available_at := NEW.delivered_at +
        (SELECT COALESCE(hint_delay_minutes, 30) FROM users WHERE id = NEW.user_id) * INTERVAL '1 minute';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_hint_available_time
    BEFORE INSERT ON deliveries
    FOR EACH ROW
    EXECUTE FUNCTION calculate_hint_available_time();

-- ============================================
-- 뷰: 검수 필요 문제
-- ============================================
CREATE OR REPLACE VIEW problems_to_review AS
SELECT
    problem_id,
    year,
    exam,
    question_no,
    score,
    answer,
    extract_text,
    source_ref,
    page_images_folder,
    confidence,
    status,
    created_at
FROM problems
WHERE status = 'needs_review'
ORDER BY year DESC, exam, question_no;

-- ============================================
-- 뷰: 발송 가능 문제
-- ============================================
CREATE OR REPLACE VIEW problems_ready AS
SELECT
    p.problem_id,
    p.year,
    p.exam,
    p.question_no,
    COALESCE(p.score_verified, p.score) as score,
    COALESCE(p.answer_verified, p.answer) as answer,
    p.subject,
    p.unit,
    p.problem_image_url,
    p.problem_text,
    p.intent_1,
    p.intent_2,
    p.solution,
    h1.hint_text as hint_1,
    h2.hint_text as hint_2,
    h3.hint_text as hint_3
FROM problems p
LEFT JOIN hints h1 ON p.problem_id = h1.problem_id AND h1.stage = 1
LEFT JOIN hints h2 ON p.problem_id = h2.problem_id AND h2.stage = 2
LEFT JOIN hints h3 ON p.problem_id = h3.problem_id AND h3.stage = 3
WHERE p.status = 'ready';

-- ============================================
-- 뷰: 문제별 정답률 통계
-- ============================================
CREATE OR REPLACE VIEW problem_stats AS
SELECT
    p.problem_id,
    p.year,
    p.exam,
    p.question_no,
    p.subject,
    p.unit,
    COALESCE(p.score_verified, p.score) as score,
    p.difficulty,
    p.attempt_count,
    p.correct_rate,
    CASE
        WHEN p.correct_rate >= 80 THEN 1
        WHEN p.correct_rate >= 60 THEN 2
        WHEN p.correct_rate >= 40 THEN 3
        WHEN p.correct_rate >= 20 THEN 4
        ELSE 5
    END as auto_difficulty
FROM problems p
WHERE p.status = 'ready';

-- ============================================
-- 함수: 정답 처리 및 통계 업데이트
-- ============================================
CREATE OR REPLACE FUNCTION process_answer(
    p_delivery_id UUID,
    p_user_answer VARCHAR(50),
    p_time_spent INTEGER DEFAULT NULL
) RETURNS JSONB AS $$
DECLARE
    v_problem_id VARCHAR(50);
    v_correct_answer VARCHAR(50);
    v_is_correct BOOLEAN;
    v_user_id UUID;
    v_problem_score INTEGER;
    v_problem_difficulty INTEGER;
    v_user_level INTEGER;
    v_user_score_level INTEGER;
    v_consecutive_correct INTEGER;
    v_consecutive_wrong INTEGER;
BEGIN
    -- 1. 문제 정보 조회
    SELECT d.problem_id, d.user_id,
           COALESCE(p.answer_verified, p.answer),
           COALESCE(p.score_verified, p.score),
           p.difficulty
    INTO v_problem_id, v_user_id, v_correct_answer, v_problem_score, v_problem_difficulty
    FROM deliveries d
    JOIN problems p ON d.problem_id = p.problem_id
    WHERE d.id = p_delivery_id;

    -- 2. 정답 여부 확인
    v_is_correct := (TRIM(LOWER(p_user_answer)) = TRIM(LOWER(v_correct_answer)));

    -- 3. 발송 기록 업데이트
    UPDATE deliveries
    SET user_answer = p_user_answer,
        answered_at = NOW(),
        is_correct = v_is_correct,
        time_spent_seconds = p_time_spent,
        status = 'answered'
    WHERE id = p_delivery_id;

    -- 4. 문제 통계 업데이트
    UPDATE problems
    SET attempt_count = attempt_count + 1,
        correct_rate = (
            SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE is_correct = true) / COUNT(*), 2)
            FROM deliveries
            WHERE problem_id = v_problem_id AND status = 'answered'
        )
    WHERE problem_id = v_problem_id;

    -- 5. 사용자 통계 조회
    SELECT current_level, current_score_level, consecutive_correct, consecutive_wrong
    INTO v_user_level, v_user_score_level, v_consecutive_correct, v_consecutive_wrong
    FROM users WHERE id = v_user_id;

    -- 6. 사용자 수준 조정
    IF v_is_correct THEN
        -- 정답: 연속 정답 증가
        v_consecutive_correct := v_consecutive_correct + 1;
        v_consecutive_wrong := 0;

        -- 3연속 정답이면 레벨/배점 상승
        IF v_consecutive_correct >= 3 THEN
            -- 난이도 상승 (최대 5)
            IF v_user_level < 5 THEN
                v_user_level := v_user_level + 1;
            -- 난이도가 이미 최대이면 배점 상승
            ELSIF v_user_score_level < 4 THEN
                v_user_score_level := v_user_score_level + 1;
                v_user_level := 3;  -- 배점 상승 시 난이도는 중간으로
            END IF;
            v_consecutive_correct := 0;
        END IF;
    ELSE
        -- 오답: 연속 오답 증가
        v_consecutive_wrong := v_consecutive_wrong + 1;
        v_consecutive_correct := 0;

        -- 2연속 오답이면 같은 난이도 유지 (배점 유지)
        -- 3연속 오답이면 레벨 하락
        IF v_consecutive_wrong >= 3 THEN
            IF v_user_level > 1 THEN
                v_user_level := v_user_level - 1;
            ELSIF v_user_score_level > 2 THEN
                v_user_score_level := v_user_score_level - 1;
                v_user_level := 3;
            END IF;
            v_consecutive_wrong := 0;
        END IF;
    END IF;

    -- 7. 사용자 정보 업데이트
    UPDATE users
    SET total_solved = total_solved + 1,
        correct_count = correct_count + CASE WHEN v_is_correct THEN 1 ELSE 0 END,
        current_level = v_user_level,
        current_score_level = v_user_score_level,
        consecutive_correct = v_consecutive_correct,
        consecutive_wrong = v_consecutive_wrong,
        recent_history = (
            SELECT jsonb_agg(item) FROM (
                SELECT item FROM (
                    SELECT jsonb_build_object(
                        'problem_id', v_problem_id,
                        'is_correct', v_is_correct,
                        'score', v_problem_score,
                        'difficulty', v_problem_difficulty,
                        'answered_at', NOW()
                    ) as item
                    UNION ALL
                    SELECT jsonb_array_elements(recent_history) as item
                    FROM users WHERE id = v_user_id
                ) sub
                LIMIT 10
            ) limited
        ),
        updated_at = NOW()
    WHERE id = v_user_id;

    -- 8. 결과 반환
    RETURN jsonb_build_object(
        'is_correct', v_is_correct,
        'correct_answer', v_correct_answer,
        'new_level', v_user_level,
        'new_score_level', v_user_score_level,
        'consecutive_correct', v_consecutive_correct,
        'consecutive_wrong', v_consecutive_wrong
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 함수: 적응형 다음 문제 추천
-- ============================================
CREATE OR REPLACE FUNCTION recommend_next_problem(
    p_user_id UUID,
    p_subject VARCHAR(10) DEFAULT NULL  -- 특정 과목 지정 가능
) RETURNS TABLE (
    problem_id VARCHAR(50),
    year INTEGER,
    exam VARCHAR(10),
    question_no INTEGER,
    subject VARCHAR(10),
    unit VARCHAR(50),
    score INTEGER,
    difficulty INTEGER,
    recommendation_reason TEXT
) AS $$
DECLARE
    v_user_level INTEGER;
    v_user_score_level INTEGER;
    v_is_correct_last BOOLEAN;
    v_weak_unit VARCHAR(50);
BEGIN
    -- 1. 사용자 현재 수준 조회
    SELECT u.current_level, u.current_score_level,
           (recent_history->0->>'is_correct')::boolean
    INTO v_user_level, v_user_score_level, v_is_correct_last
    FROM users u
    WHERE u.id = p_user_id;

    -- 2. 취약 단원 파악 (정답률 50% 미만인 단원 중 가장 낮은 것)
    SELECT key INTO v_weak_unit
    FROM users u,
         jsonb_each(u.unit_stats) AS stats(key, value)
    WHERE u.id = p_user_id
      AND (value->>'total')::int >= 3  -- 최소 3문제 이상 푼 단원
      AND (value->>'correct')::float / (value->>'total')::float < 0.5
    ORDER BY (value->>'correct')::float / (value->>'total')::float ASC
    LIMIT 1;

    -- 3. 추천 로직
    IF v_is_correct_last IS NULL OR v_is_correct_last = true THEN
        -- 정답이었거나 첫 문제: 같은 레벨 또는 약간 높은 레벨
        RETURN QUERY
        SELECT
            p.problem_id,
            p.year,
            p.exam,
            p.question_no,
            p.subject,
            p.unit,
            COALESCE(p.score_verified, p.score) as score,
            p.difficulty,
            CASE
                WHEN p.unit = v_weak_unit THEN '취약 단원 보강 문제'
                WHEN p.difficulty > v_user_level THEN '도전 문제 (난이도 상승)'
                ELSE '현재 수준 맞춤 문제'
            END as recommendation_reason
        FROM problems p
        WHERE p.status = 'ready'
          AND (p_subject IS NULL OR p.subject = p_subject)
          AND COALESCE(p.score_verified, p.score) = v_user_score_level
          AND p.difficulty BETWEEN v_user_level AND v_user_level + 1
          -- 이미 푼 문제 제외
          AND p.problem_id NOT IN (
              SELECT d.problem_id FROM deliveries d WHERE d.user_id = p_user_id
          )
        ORDER BY
            -- 취약 단원 우선
            CASE WHEN p.unit = v_weak_unit THEN 0 ELSE 1 END,
            -- 그 다음 랜덤
            RANDOM()
        LIMIT 1;
    ELSE
        -- 오답이었음: 같은 난이도, 같은 배점의 비슷한 문제
        RETURN QUERY
        SELECT
            p.problem_id,
            p.year,
            p.exam,
            p.question_no,
            p.subject,
            p.unit,
            COALESCE(p.score_verified, p.score) as score,
            p.difficulty,
            '오답 복습용 (같은 난이도/배점)' as recommendation_reason
        FROM problems p
        WHERE p.status = 'ready'
          AND (p_subject IS NULL OR p.subject = p_subject)
          AND COALESCE(p.score_verified, p.score) = v_user_score_level
          AND p.difficulty BETWEEN v_user_level - 1 AND v_user_level  -- 같거나 약간 쉬운
          -- 이미 푼 문제 제외
          AND p.problem_id NOT IN (
              SELECT d.problem_id FROM deliveries d WHERE d.user_id = p_user_id
          )
        ORDER BY
            -- 같은 난이도 우선
            ABS(p.difficulty - v_user_level),
            RANDOM()
        LIMIT 1;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 함수: 사용자 단원별 통계 업데이트
-- ============================================
CREATE OR REPLACE FUNCTION update_unit_stats()
RETURNS TRIGGER AS $$
DECLARE
    v_unit VARCHAR(50);
    v_subject VARCHAR(10);
    v_unit_key VARCHAR(100);
BEGIN
    -- 문제의 단원 정보 조회
    SELECT p.subject, p.unit
    INTO v_subject, v_unit
    FROM problems p
    WHERE p.problem_id = NEW.problem_id;

    IF v_subject IS NOT NULL AND v_unit IS NOT NULL THEN
        v_unit_key := v_subject || '_' || v_unit;

        -- 단원별 통계 업데이트
        UPDATE users
        SET unit_stats = jsonb_set(
            unit_stats,
            ARRAY[v_unit_key],
            jsonb_build_object(
                'correct', COALESCE((unit_stats->v_unit_key->>'correct')::int, 0) +
                           CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,
                'total', COALESCE((unit_stats->v_unit_key->>'total')::int, 0) + 1
            )
        )
        WHERE id = NEW.user_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_unit_stats
    AFTER UPDATE OF is_correct ON deliveries
    FOR EACH ROW
    WHEN (NEW.is_correct IS NOT NULL AND OLD.is_correct IS NULL)
    EXECUTE FUNCTION update_unit_stats();

-- ============================================
-- 뷰: 사용자 학습 현황 대시보드
-- ============================================
CREATE OR REPLACE VIEW user_learning_dashboard AS
SELECT
    u.id as user_id,
    u.nickname,
    u.grade,
    u.current_level,
    u.current_score_level,
    u.total_solved,
    u.correct_count,
    ROUND(100.0 * u.correct_count / NULLIF(u.total_solved, 0), 1) as overall_correct_rate,
    u.consecutive_correct,
    u.consecutive_wrong,
    u.unit_stats,
    -- 최근 5문제 정답률
    (
        SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE (item->>'is_correct')::boolean) / COUNT(*), 1)
        FROM jsonb_array_elements(u.recent_history) AS item
        LIMIT 5
    ) as recent_5_correct_rate,
    -- 추천 학습 방향
    CASE
        WHEN u.consecutive_wrong >= 2 THEN '기초 다지기 권장'
        WHEN u.consecutive_correct >= 2 THEN '도전 문제 추천'
        ELSE '현재 수준 유지'
    END as learning_suggestion
FROM users u;

-- ============================================
-- 함수: 일일 문제 자동 스케줄링 (적응형)
-- ============================================
CREATE OR REPLACE FUNCTION schedule_daily_problem_adaptive(
    p_user_id UUID,
    p_date DATE DEFAULT CURRENT_DATE
) RETURNS UUID AS $$
DECLARE
    v_problem_id VARCHAR(50);
    v_scheduled_time TIME;
    v_schedule_id UUID;
BEGIN
    -- 사용자 선호 시간 조회
    SELECT preferred_time INTO v_scheduled_time
    FROM users WHERE id = p_user_id;

    -- 적응형 문제 추천
    SELECT rp.problem_id INTO v_problem_id
    FROM recommend_next_problem(p_user_id) rp;

    IF v_problem_id IS NULL THEN
        -- 추천할 문제가 없으면 랜덤 선택
        SELECT p.problem_id INTO v_problem_id
        FROM problems p
        WHERE p.status = 'ready'
          AND p.problem_id NOT IN (
              SELECT d.problem_id FROM deliveries d WHERE d.user_id = p_user_id
          )
        ORDER BY RANDOM()
        LIMIT 1;
    END IF;

    IF v_problem_id IS NOT NULL THEN
        INSERT INTO daily_schedules (scheduled_date, user_id, problem_id, scheduled_time)
        VALUES (p_date, p_user_id, v_problem_id, v_scheduled_time)
        ON CONFLICT (scheduled_date, user_id) DO UPDATE
            SET problem_id = EXCLUDED.problem_id,
                scheduled_time = EXCLUDED.scheduled_time,
                status = 'scheduled'
        RETURNING id INTO v_schedule_id;
    END IF;

    RETURN v_schedule_id;
END;
$$ LANGUAGE plpgsql;
