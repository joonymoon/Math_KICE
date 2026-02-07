-- =============================================
-- 시간차 힌트 공개 시스템 (Phase 2)
-- =============================================

-- 문제 공개 스케줄 컬럼 추가
ALTER TABLE problems ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ;
ALTER TABLE problems ADD COLUMN IF NOT EXISTS hint_interval_hours INTEGER DEFAULT 24;

-- published_at: 문제 공개 시각 (NULL이면 제한 없이 전체 공개)
-- hint_interval_hours: 힌트 단계 간 간격 (기본 24시간)
--
-- 공개 로직:
--   힌트 1: published_at 이후 즉시
--   힌트 2: published_at + hint_interval_hours
--   힌트 3 + 풀이: published_at + hint_interval_hours * 2

COMMENT ON COLUMN problems.published_at IS '문제 공개 시각 (NULL=즉시 전체 공개)';
COMMENT ON COLUMN problems.hint_interval_hours IS '힌트 단계 간 간격(시간), 기본 24';

-- 인덱스: 공개 스케줄 조회용
CREATE INDEX IF NOT EXISTS idx_problems_published_at
    ON problems (published_at)
    WHERE published_at IS NOT NULL;
