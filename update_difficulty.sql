-- ============================================
-- 문제 난이도 업데이트 스크립트
-- 배점과 문제 유형에 따라 기본 난이도 설정
-- 최종 업데이트: 2026-02-04
-- ============================================
-- problem_id 형식: {year}_{exam}_Q{question_no:02d}
-- 예: 2026_CSAT_Q01, 2025_KICE6_Q15

-- 규칙:
-- 3점 문제: 기본 난이도 2~3 (쉬움~보통)
-- 4점 문제: 기본 난이도 3~4 (보통~어려움)
-- 단답형(short): +1 난이도
-- 뒷번호 문제일수록 어려움

-- 2022년 수능
UPDATE problems SET difficulty = 2 WHERE problem_id = '2022_CSAT_Q05';  -- 3점, 로그 기본
UPDATE problems SET difficulty = 3 WHERE problem_id = '2022_CSAT_Q09';  -- 4점, 삼각함수 그래프
UPDATE problems SET difficulty = 4 WHERE problem_id = '2022_CSAT_Q12';  -- 4점, 접선
UPDATE problems SET difficulty = 4 WHERE problem_id = '2022_CSAT_Q15';  -- 4점, 수열
UPDATE problems SET difficulty = 5 WHERE problem_id = '2022_CSAT_Q20';  -- 4점 단답형, 적분

-- 2022년 6월 모의평가
UPDATE problems SET difficulty = 2 WHERE problem_id = '2022_KICE6_Q06';  -- 3점, 극한
UPDATE problems SET difficulty = 3 WHERE problem_id = '2022_KICE6_Q11';  -- 4점, 지수방정식
UPDATE problems SET difficulty = 4 WHERE problem_id = '2022_KICE6_Q14';  -- 4점, 극값

-- 2022년 9월 모의평가
UPDATE problems SET difficulty = 2 WHERE problem_id = '2022_KICE9_Q08';  -- 3점, 삼각방정식
UPDATE problems SET difficulty = 4 WHERE problem_id = '2022_KICE9_Q13';  -- 4점, 연속

-- 2023년 수능
UPDATE problems SET difficulty = 2 WHERE problem_id = '2023_CSAT_Q04';  -- 3점, 지수
UPDATE problems SET difficulty = 2 WHERE problem_id = '2023_CSAT_Q07';  -- 3점, 미분계수
UPDATE problems SET difficulty = 3 WHERE problem_id = '2023_CSAT_Q10';  -- 4점, 수열의 합
UPDATE problems SET difficulty = 3 WHERE problem_id = '2023_CSAT_Q16';  -- 4점, 부정적분
UPDATE problems SET difficulty = 5 WHERE problem_id = '2023_CSAT_Q21';  -- 4점 단답형, 삼각함수

-- 2023년 6월 모의평가
UPDATE problems SET difficulty = 2 WHERE problem_id = '2023_KICE6_Q05';  -- 3점, 극한 성질
UPDATE problems SET difficulty = 2 WHERE problem_id = '2023_KICE6_Q09';  -- 3점, 로그함수
UPDATE problems SET difficulty = 4 WHERE problem_id = '2023_KICE6_Q12';  -- 4점, 최대최소

-- 2023년 9월 모의평가
UPDATE problems SET difficulty = 2 WHERE problem_id = '2023_KICE9_Q06';  -- 3점, 호도법
UPDATE problems SET difficulty = 4 WHERE problem_id = '2023_KICE9_Q11';  -- 4점, 구분구적법
UPDATE problems SET difficulty = 4 WHERE problem_id = '2023_KICE9_Q15';  -- 4점, 점화식

-- 2024년 수능
UPDATE problems SET difficulty = 2 WHERE problem_id = '2024_CSAT_Q03';  -- 3점, 로그 계산
UPDATE problems SET difficulty = 3 WHERE problem_id = '2024_CSAT_Q08';  -- 3점, 무한대 극한
UPDATE problems SET difficulty = 3 WHERE problem_id = '2024_CSAT_Q11';  -- 4점, 삼각함수 응용
UPDATE problems SET difficulty = 4 WHERE problem_id = '2024_CSAT_Q14';  -- 4점, 속도 가속도
UPDATE problems SET difficulty = 5 WHERE problem_id = '2024_CSAT_Q19';  -- 4점 단답형, 넓이

-- 2024년 6월 모의평가
UPDATE problems SET difficulty = 2 WHERE problem_id = '2024_KICE6_Q07';  -- 3점, 등비급수
UPDATE problems SET difficulty = 3 WHERE problem_id = '2024_KICE6_Q10';  -- 4점, 중간값정리
UPDATE problems SET difficulty = 4 WHERE problem_id = '2024_KICE6_Q13';  -- 4점, 지수부등식

-- 2025년 수능
UPDATE problems SET difficulty = 3 WHERE problem_id = '2025_CSAT_Q06';  -- 3점, 미분가능성

-- ============================================
-- 배점별 기본 난이도 설정 (새 문제용)
-- ============================================
-- 위에서 개별 설정하지 않은 문제들에 대해 기본값 적용
UPDATE problems
SET difficulty = CASE
    WHEN COALESCE(score_verified, score) = 2 THEN 1
    WHEN COALESCE(score_verified, score) = 3 AND question_no <= 10 THEN 2
    WHEN COALESCE(score_verified, score) = 3 AND question_no > 10 THEN 3
    WHEN COALESCE(score_verified, score) = 4 AND question_no <= 15 THEN 3
    WHEN COALESCE(score_verified, score) = 4 AND question_no > 15 AND answer_type = 'multiple' THEN 4
    WHEN COALESCE(score_verified, score) = 4 AND answer_type = 'short' THEN 5
    ELSE 3
END
WHERE difficulty IS NULL OR difficulty = 3;  -- 기본값만 업데이트
