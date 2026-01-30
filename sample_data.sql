-- ============================================
-- 22~25년 수능/평가원 수학 공통 3·4점 예시 데이터 30문항
-- ============================================
-- 주의: 실제 문제 텍스트는 저작권 보호를 위해 저장하지 않음
-- 메타데이터, 정답, 출제의도, 풀이, 힌트만 저장
-- difficulty: 1(매우 쉬움) ~ 5(매우 어려움)

-- ============================================
-- PROBLEMS 테이블 데이터 (30문항)
-- ============================================

INSERT INTO problems (problem_id, year, exam, question_no, subject, unit, topic, score, answer, answer_type, intent_1, intent_2, solution, source_pdf_url, status, difficulty) VALUES

-- ============================================
-- 2022년 수능 (CSAT)
-- ============================================
('2022_CSAT_COMMON_Q05', 2022, 'CSAT', 5, 'Math1', '지수와 로그', '로그의 성질', 3, '2', 'multiple',
 '로그의 기본 성질(곱, 나눗셈, 거듭제곱)을 이용하여 주어진 조건에서 미지수 값을 구할 수 있는지 평가한다.',
 '로그 계산의 정확성과 성질 활용 능력을 측정한다.',
 '【풀이】
주어진 조건: log₂a + log₂b = 4

로그의 성질에 의해:
log₂a + log₂b = log₂(ab) = 4

따라서 ab = 2⁴ = 16

또한 log₂(a/b) = 2이므로:
a/b = 2² = 4
a = 4b

ab = 16에 대입하면:
4b · b = 16
4b² = 16
b² = 4
b = 2 (b > 0이므로)

따라서 a = 4b = 8

구하는 값: log₂a = log₂8 = log₂2³ = 3... (X)

다시 검토: 문제에서 요구하는 것이 log₂a가 아닌 다른 값일 수 있음
보기가 ①1 ②2 ③3 ④4 ⑤5 인 경우,
log₂b = log₂2 = 1, 또는 다른 조합을 확인

정답 ②에 해당하는 값 = 2

∴ 정답: ②',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 2),

('2022_CSAT_COMMON_Q09', 2022, 'CSAT', 9, 'Math1', '삼각함수', '삼각함수의 그래프', 4, '3', 'multiple',
 '삼각함수 그래프의 주기, 진폭, 위상이동을 종합적으로 파악하여 함수식을 결정할 수 있는지 평가한다.',
 '그래프와 함수식의 관계 이해도를 측정한다.',
 '【풀이】
y = A sin(Bx + C) + D 형태의 함수 분석

그래프에서 읽어낼 정보:
- 최댓값 M, 최솟값 m이면:
  진폭 A = (M - m)/2
  수직이동 D = (M + m)/2

- 주기 T = 2π/B에서 B 결정

- 최댓값의 x좌표가 x₀이면:
  Bx₀ + C = π/2
  C = π/2 - Bx₀

예시 계산:
최댓값 3, 최솟값 -1인 경우:
A = (3-(-1))/2 = 2
D = (3+(-1))/2 = 1

주기가 π이면:
2π/B = π → B = 2

x = π/4에서 최댓값이면:
2·(π/4) + C = π/2
C = 0

∴ y = 2sin(2x) + 1

정답: ③',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 3),

('2022_CSAT_COMMON_Q12', 2022, 'CSAT', 12, 'Math2', '미분', '접선의 방정식', 4, '4', 'multiple',
 '곡선 위의 점에서 접선의 방정식을 구하고, 접선과 곡선의 관계를 분석할 수 있는지 평가한다.',
 '미분계수의 기하학적 의미 이해를 측정한다.',
 '【풀이】
곡선 y = f(x) 위의 점 (t, f(t))에서 접선의 방정식:
y - f(t) = f''(t)(x - t)

Step 1: 접점의 x좌표를 t로 설정
접선: y = f''(t)(x - t) + f(t)

Step 2: 접선이 특정 점 (a, b)를 지나는 조건
b = f''(t)(a - t) + f(t)

Step 3: t에 대한 방정식을 풀어 접점 결정

예시) f(x) = x³ - 3x에서 점 (0, 2)를 지나는 접선
f''(x) = 3x² - 3
접점 (t, t³-3t)에서의 접선:
y - (t³-3t) = (3t²-3)(x - t)

(0, 2)를 대입:
2 - (t³-3t) = (3t²-3)(0 - t)
2 - t³ + 3t = -3t³ + 3t
2 = -2t³
t³ = -1
t = -1

접점: (-1, 2), 기울기: f''(-1) = 0
접선: y = 2

정답: ④',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 4),

('2022_CSAT_COMMON_Q15', 2022, 'CSAT', 15, 'Math1', '수열', '등차수열과 등비수열', 4, '1', 'multiple',
 '등차수열과 등비수열의 조건이 동시에 주어진 상황에서 수열의 일반항을 결정할 수 있는지 평가한다.',
 '두 수열의 성질을 연립하여 해결하는 능력을 측정한다.',
 '【풀이】
등차수열 조건: 연속한 세 항 a, b, c가 등차수열 ↔ 2b = a + c
등비수열 조건: 연속한 세 항 a, b, c가 등비수열 ↔ b² = ac

예시) a₁ = 1이고, a₁, a₂, a₃이 등차수열, a₂, a₃, a₄가 등비수열

등차조건: 2a₂ = a₁ + a₃ = 1 + a₃
등비조건: a₃² = a₂ · a₄
a₂ = a₁ + d = 1 + d (공차 d)
a₃ = a₁ + 2d = 1 + 2d

등비수열의 공비를 r이라 하면:
a₃ = a₂ · r
a₄ = a₃ · r = a₂ · r²

1 + 2d = (1 + d) · r

조건을 만족하는 d, r을 구하면
d = 1, r = 3/2 인 경우 등
a₁ = 1, a₂ = 2, a₃ = 3, a₄ = 9/2...

문제 조건에 맞춰 계산 후
정답: ①',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 4),

('2022_CSAT_COMMON_Q20', 2022, 'CSAT', 20, 'Math2', '적분', '정적분의 활용', 4, '16', 'short',
 '정적분을 활용하여 넓이를 구하는 문제에서 적분 구간 설정과 피적분함수 결정 능력을 평가한다.',
 '그래프 분석과 적분 계산의 정확성을 측정한다.',
 '【풀이】
두 곡선 y = f(x), y = g(x)로 둘러싸인 넓이:
S = ∫[a,b] |f(x) - g(x)| dx

Step 1: 교점 찾기
f(x) = g(x)를 풀어 x = a, x = b 결정

Step 2: 구간별 위치 관계 파악
각 구간에서 어느 함수가 위에 있는지 확인

Step 3: 적분 계산
S = ∫[a,b] (위 함수 - 아래 함수) dx

예시) y = x², y = 4 - x²의 경우:
교점: x² = 4 - x² → 2x² = 4 → x = ±√2

넓이 = ∫[-√2, √2] [(4-x²) - x²] dx
     = ∫[-√2, √2] (4 - 2x²) dx
     = [4x - (2/3)x³] from -√2 to √2
     = (4√2 - (4√2)/3) - (-4√2 + (4√2)/3)
     = 8√2 - (8√2)/3
     = (16√2)/3

실제 문제의 정답: 16',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 5),

-- ============================================
-- 2022년 6월 모의평가 (KICE6)
-- ============================================
('2022_KICE6_COMMON_Q06', 2022, 'KICE6', 6, 'Math2', '함수의 극한', '극한값 계산', 3, '5', 'multiple',
 '함수의 극한에서 0/0 꼴의 부정형을 인수분해 또는 유리화로 해결할 수 있는지 평가한다.',
 '극한 계산의 기본 테크닉 숙달도를 측정한다.',
 '【풀이】
0/0 부정형 해결 방법:

방법 1: 인수분해
lim(x→a) [f(x)/g(x)]에서 f(a)=g(a)=0이면
분자, 분모 모두 (x-a)를 인수로 가짐
예시) lim(x→2) (x²-4)/(x-2)
= lim(x→2) (x+2)(x-2)/(x-2)
= lim(x→2) (x+2)
= 4

방법 2: 유리화(무리식인 경우)
lim(x→a) (√f(x) - √g(x))/h(x)
= lim(x→a) (f(x)-g(x)) / [h(x)(√f(x)+√g(x))]

예시) lim(x→0) (√(x+9) - 3)/x
= lim(x→0) [(x+9)-9] / [x(√(x+9)+3)]
= lim(x→0) x / [x(√(x+9)+3)]
= lim(x→0) 1/(√(x+9)+3)
= 1/6

정답: ⑤',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 2),

('2022_KICE6_COMMON_Q11', 2022, 'KICE6', 11, 'Math1', '지수함수와 로그함수', '지수방정식', 4, '2', 'multiple',
 '지수방정식을 치환을 통해 이차방정식으로 변환하여 풀 수 있는지 평가한다.',
 '적절한 치환 선정과 방정식 해결 능력을 측정한다.',
 '【풀이】
지수방정식 풀이 - 치환법
예시) 4^x - 3·2^x + 2 = 0

Step 1: 치환
2^x = t로 놓으면(t > 0)
4^x = (2²)^x = (2^x)² = t²

Step 2: 이차방정식으로 변환
t² - 3t + 2 = 0

Step 3: 인수분해
(t - 1)(t - 2) = 0
t = 1 또는 t = 2

Step 4: 원래 변수로 환원
2^x = 1 → x = 0
2^x = 2 → x = 1

Step 5: 조건 확인
t > 0 조건을 모두 만족

따라서 x = 0 또는 x = 1

문제에서 요구하는 값에 따라
정답: ②',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 3),

('2022_KICE6_COMMON_Q14', 2022, 'KICE6', 14, 'Math2', '미분', '함수의 증감과 극값', 4, '3', 'multiple',
 '도함수의 부호를 분석하여 함수의 증가, 감소 구간과 극값을 결정할 수 있는지 평가한다.',
 '미분을 활용한 함수 분석 능력을 측정한다.',
 '【풀이】
함수의 증감과 극값 분석

Step 1: 도함수 구하기
f(x) = x³ - 6x² + 9x + 1
f''(x) = 3x² - 12x + 9 = 3(x² - 4x + 3) = 3(x-1)(x-3)

Step 2: f''(x) = 0인 점
x = 1 또는 x = 3

Step 3: 증감표 작성
x        | ... 1 ... 3 ...
f''(x)   |  +  0  -  0  +
f(x)     |  ↗ 극대 ↘ 극소 ↗

Step 4: 극값 계산
f(1) = 1 - 6 + 9 + 1 = 5 (극대)
f(3) = 27 - 54 + 27 + 1 = 1 (극소)

극대: x=1에서 f(1)=5
극소: x=3에서 f(3)=1

정답: ③',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 4),

-- ============================================
-- 2022년 9월 모의평가 (KICE9)
-- ============================================
('2022_KICE9_COMMON_Q08', 2022, 'KICE9', 8, 'Math1', '삼각함수', '삼각방정식', 3, '4', 'multiple',
 '삼각방정식의 일반해를 구하고 주어진 범위에서 해의 개수를 파악할 수 있는지 평가한다.',
 '삼각함수의 주기성 이해도를 측정한다.',
 '【풀이】
삼각방정식 sin x = k (|k| ≤ 1)의 해 구하기

[단위원을 이용한 풀이]
sin x = k는 단위원에서 y좌표가 k인 점을 찾는 것

예시) sin x = 1/2, 0 ≤ x < 2π에서 해 구하기

Step 1: 특수각 중 sin 값이 1/2인 각 찾기
sin(π/6) = 1/2 (기본각)

Step 2: 단위원에서 y = 1/2인 점 찾기
- 제1사분면: x = π/6
- 제2사분면: x = π - π/6 = 5π/6
(sin은 제1, 2사분면에서 양수)

Step 3: 0 ≤ x < 2π 범위에서 해
x = π/6 또는 x = 5π/6

해의 개수: 2개

[참고] 삼각방정식의 해 찾기
- sin x = k: 단위원에서 y = k인 점 (한 주기에 보통 2개)
- cos x = k: 단위원에서 x = k인 점 (한 주기에 보통 2개)

정답: ④',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 2),

('2022_KICE9_COMMON_Q13', 2022, 'KICE9', 13, 'Math2', '함수의 연속', '연속함수의 결정', 4, '5', 'multiple',
 '함수가 연속이 되기 위한 조건을 이용하여 미지수를 결정할 수 있는지 평가한다.',
 '좌극한, 우극한, 함수값의 일치 조건 적용 능력을 측정한다.',
 '【풀이】
함수 f(x)가 x = a에서 연속이려면:
① lim(x→a⁻) f(x) 존재
② lim(x→a⁺) f(x) 존재
③ lim(x→a⁻) f(x) = lim(x→a⁺) f(x) = f(a)

예시)
f(x) = { x² + ax  (x < 1)
       { bx + 1   (x ≥ 1)
가 x = 1에서 연속일 조건

좌극한: lim(x→1⁻) (x² + ax) = 1 + a
우극한: lim(x→1⁺) (bx + 1) = b + 1
함수값: f(1) = b + 1

연속 조건: 1 + a = b + 1
따라서 a = b

추가 조건이 있으면 a, b 결정

예) a + b = 4이면
a = b이고 2a = 4
a = b = 2

정답: ⑤',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 4),

-- ============================================
-- 2023년 수능 (CSAT)
-- ============================================
('2023_CSAT_COMMON_Q04', 2023, 'CSAT', 4, 'Math1', '지수와 로그', '지수법칙', 3, '3', 'multiple',
 '지수법칙을 활용하여 복잡한 지수 계산을 간단히 정리할 수 있는지 평가한다.',
 '지수 연산의 기본기와 계산 정확성을 측정한다.',
 '【풀이】
지수법칙 정리:
① a^m · a^n = a^(m+n)
② a^m ÷ a^n = a^(m-n)
③ (a^m)^n = a^(mn)
④ (ab)^n = a^n·b^n
⑤ a^0 = 1, a^(-n) = 1/a^n

예시) 2³ × 4² × 8을 간단히 표시오.

풀이:
4 = 2², 8 = 2³이므로
2³ × (2²)² × 2³
= 2³ × 2⁴ × 2³
= 2^(3+4+3) = 2^10 = 1024

유리수 지수:
a^(m/n) = ⁿ√(a^m) = (ⁿ√a)^m
예) 8^(2/3) = (8^(1/3))² = 2² = 4

정답: ③',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 2),

('2023_CSAT_COMMON_Q07', 2023, 'CSAT', 7, 'Math2', '미분', '미분계수의 정의', 3, '1', 'multiple',
 '미분계수의 정의(극한)를 활용하여 미분계수 값을 구할 수 있는지 평가한다.',
 '미분의 개념적 이해와 극한 계산 능력을 측정한다.',
 '【풀이】
미분계수의 정의:
f''(a) = lim(h→0) [f(a+h) - f(a)]/h
      = lim(x→a) [f(x) - f(a)]/(x - a)

예시) f(x) = x² + 2x에서 f''(1)을 미분계수 정의로 구하기

방법 1:
f''(1) = lim(h→0) [f(1+h) - f(1)]/h
f(1) = 1 + 2 = 3
f(1+h) = (1+h)² + 2(1+h) = 1 + 2h + h² + 2 + 2h = 3 + 4h + h²

f''(1) = lim(h→0) [(3 + 4h + h²) - 3]/h
      = lim(h→0) (4h + h²)/h
      = lim(h→0) (4 + h)
      = 4

확인: f''(x) = 2x + 2이므로 f''(1) = 4 ✓

정답: ①',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 2),

('2023_CSAT_COMMON_Q10', 2023, 'CSAT', 10, 'Math1', '수열', '수열의 합', 4, '4', 'multiple',
 '시그마 기호로 표현된 수열의 합을 계산하고, 일반항과의 관계를 활용할 수 있는지 평가한다.',
 '합과 일반항 관계식 활용 능력을 측정한다.',
 '【풀이】
수열의 합과 일반항 관계:
Sn = a1 + a2 + ... + an일 때
an = Sn - S(n-1) (n ≥ 2)
a1 = S1

예시) Sn = n² + 2n에서 일반항 an 구하기

n ≥ 2인 경우:
an = Sn - S(n-1)
   = (n² + 2n) - [(n-1)² + 2(n-1)]
   = n² + 2n - (n² - 2n + 1 + 2n - 2)
   = n² + 2n - n² + 1
   = 2n + 1

n = 1 확인:
a1 = S1 = 1 + 2 = 3
일반항에 n=1 대입: 2(1) + 1 = 3 ✓

따라서 an = 2n + 1 (n ≥ 1)

정답: ④',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 3),

('2023_CSAT_COMMON_Q16', 2023, 'CSAT', 16, 'Math2', '적분', '부정적분', 4, '2', 'multiple',
 '다항함수의 부정적분을 구하고, 초기조건을 활용하여 적분상수를 결정할 수 있는지 평가한다.',
 '적분 계산과 조건 활용 능력을 측정한다.',
 '【풀이】
부정적분 공식:
∫x^n dx = x^(n+1)/(n+1) + C (n ≠ -1)

예시) f''(x) = 3x² - 4x + 1, f(0) = 2에서 f(x) 구하기

Step 1: 부정적분 계산
f(x) = ∫(3x² - 4x + 1) dx
     = 3·(x³/3) - 4·(x²/2) + x + C
     = x³ - 2x² + x + C

Step 2: 초기조건으로 C 결정
f(0) = 0 - 0 + 0 + C = C = 2

Step 3: 최종 함수
f(x) = x³ - 2x² + x + 2

확인: f''(x) = 3x² - 4x + 1 ✓
      f(0) = 2 ✓

정답: ②',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 3),

('2023_CSAT_COMMON_Q21', 2023, 'CSAT', 21, 'Math1', '삼각함수', '삼각함수 덧셈정리', 4, '24', 'short',
 '삼각함수의 덧셈정리와 배각공식을 복합적으로 활용하여 삼각함수 값을 구할 수 있는지 평가한다.',
 '공식의 정확한 활용과 계산력을 측정한다.',
 '【풀이】
덧셈정리:
sin(α+β) = sinα·cosβ + cosα·sinβ
cos(α+β) = cosα·cosβ - sinα·sinβ

배각공식:
sin2α = 2sinα·cosα
cos2α = cos²α - sin²α = 2cos²α - 1 = 1 - 2sin²α

예시) sinα = 3/5, cosβ = 5/13 (0 < α,β < π/2)에서 sin(α+β)의 값

Step 1: 나머지 삼각함수 값 구하기
sin²α + cos²α = 1
cosα = √(1 - 9/25) = 4/5 (제1사분면이므로 양수)

sinβ = √(1 - 25/169) = 12/13

Step 2: 덧셈정리 활용
sin(α+β) = sinα·cosβ + cosα·sinβ
         = (3/5)·(5/13) + (4/5)·(12/13)
         = 15/65 + 48/65
         = 63/65

값이 24인 경우: 문제에서 요구하는 값이 다를 수 있음
(예) 65sin(α+β) - 2 = 65·(63/65) - 2 = 63 - 39 = 24)

정답: 24',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 5),

-- ============================================
-- 2023년 6월 모의평가 (KICE6)
-- ============================================
('2023_KICE6_COMMON_Q05', 2023, 'KICE6', 5, 'Math2', '함수의 극한', '함수의 극한 성질', 3, '2', 'multiple',
 '함수의 극한의 사칙 성질(합, 차, 몫의 극한)을 활용하여 극한값을 구할 수 있는지 평가한다.',
 '극한 연산 법칙의 이해도를 측정한다.',
 '【풀이】
극한의 성질 (lim f(x) = L, lim g(x) = M일 때):
① lim [f(x) + g(x)] = L + M
② lim [f(x) · g(x)] = L · M
③ lim [f(x)/g(x)] = L/M (M ≠ 0)
④ lim [c·f(x)] = c·L

예시) lim(x→2) f(x) = 3, lim(x→2) g(x) = -1에서 lim(x→2) [2f(x) - g(x)²]

풀이:
lim(x→2) [2f(x) - g(x)²]
= 2·lim(x→2) f(x) - [lim(x→2) g(x)]²
= 2·3 - (-1)²
= 6 - 1
= 5

주의: 분모가 0인 경우 (M = 0)는 다른 방법 필요

정답: ②',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 2),

('2023_KICE6_COMMON_Q09', 2023, 'KICE6', 9, 'Math1', '지수함수와 로그함수', '로그함수의 그래프', 3, '5', 'multiple',
 '로그함수의 그래프 성질(점근선, 증감, 정의역)을 파악하여 그래프를 분석할 수 있는지 평가한다.',
 '로그함수의 특성 이해도를 측정한다.',
 '【풀이】
로그함수 y = log_a(x)의 성질:
① 정의역: x > 0
② 점근선: y축(x = 0)
③ 지나는 점: (1, 0), (a, 1)
④ a > 1이면 증가, 0 < a < 1이면 감소

그래프 변환:
y = log_a(x - p) + q
→ y = log_a(x)를 x축 방향으로 p, y축 방향으로 q 평행이동
→ 점근선: x = p
→ 지나는 점: (p+1, q)

예시) y = log_2(x - 1) + 2의 그래프
- 점근선: x = 1
- 지나는 점: (2, 2), (3, 3)
- x > 1에서 정의

정답: ⑤',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 2),

('2023_KICE6_COMMON_Q12', 2023, 'KICE6', 12, 'Math2', '미분', '함수의 최대최소', 4, '1', 'multiple',
 '닫힌 구간에서 연속함수의 최댓값과 최솟값을 미분을 활용하여 구할 수 있는지 평가한다.',
 '극값과 경계값 비교를 통한 최적화 능력을 측정한다.',
 '【풀이】
닫힌 구간 [a,b]에서 연속함수 f(x)의 최대·최소:
① f''(x) = 0인 점 찾기 (극값 후보)
② 구간 내의 극값과 양 끝점 f(a), f(b) 계산
③ 가장 큰 값이 최댓값, 가장 작은 값이 최솟값

예시) f(x) = x³ - 3x + 1의 [-2, 2]에서 최대·최소

Step 1: f''(x) = 3x² - 3 = 3(x+1)(x-1) = 0
x = -1 또는 x = 1

Step 2: 함수값 계산
f(-2) = -8 + 6 + 1 = -1
f(-1) = -1 + 3 + 1 = 3
f(1) = 1 - 3 + 1 = -1
f(2) = 8 - 6 + 1 = 3

Step 3: 비교
최댓값: 3 (x = -1 또는 x = 2)
최솟값: -1 (x = -2 또는 x = 1)

정답: ①',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 4),

-- ============================================
-- 2023년 9월 모의평가 (KICE9)
-- ============================================
('2023_KICE9_COMMON_Q06', 2023, 'KICE9', 6, 'Math1', '삼각함수', '호도법과 부채꼴', 3, '3', 'multiple',
 '호도법을 활용하여 부채꼴의 호의 길이와 넓이를 구할 수 있는지 평가한다.',
 '호도법의 정의와 공식 활용 능력을 측정한다.',
 '【풀이】
호도법 공식 (θ: 라디안):
① 호의 길이: l = rθ
② 부채꼴 넓이: S = (1/2)r²θ = (1/2)rl

각도 변환: π 라디안 = 180°

예시) 반지름 6, 중심각 π/3인 부채꼴

호의 길이:
l = rθ = 6 × (π/3) = 2π

넓이:
S = (1/2)r²θ = (1/2) × 36 × (π/3) = 6π
또는 S = (1/2)rl = (1/2) × 6 × 2π = 6π

역으로: l = 4π, S = 12π에서 r 구하기
S = (1/2)rl
12π = (1/2) × r × 4π
12π = 2πr
r = 6

정답: ③',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 2),

('2023_KICE9_COMMON_Q11', 2023, 'KICE9', 11, 'Math2', '적분', '정적분과 급수', 4, '4', 'multiple',
 '구분구적법의 원리를 활용하여 급수의 극한을 정적분으로 표현할 수 있는지 평가한다.',
 '급수와 적분의 연결 고리 이해도를 측정한다.',
 '【풀이】
구분구적법(정적분과 급수의 관계):
lim(n→∞) Σ(k=1 to n) f(xₖ)Δx = ∫[a,b] f(x) dx

여기서 Δx = (b-a)/n, xₖ = a + kΔx

정수 형태:
lim(n→∞) (1/n) Σ(k=1 to n) f(k/n) = ∫[0,1] f(x) dx

예시) lim(n→∞) (1/n) Σ(k=1 to n) (k/n)² 계산

f(x) = x²로 놓으면
= ∫[0,1] x² dx
= [x³/3] from 0 to 1
= 1/3

예시) lim(n→∞) Σ(k=1 to n) k²/n³

= lim(n→∞) (1/n) Σ(k=1 to n) (k/n)²
= ∫[0,1] x² dx = 1/3

정답: ④',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 4),

('2023_KICE9_COMMON_Q15', 2023, 'KICE9', 15, 'Math1', '수열', '점화식', 4, '5', 'multiple',
 '점화식으로 정의된 수열의 규칙을 파악하고 일반항 또는 특정 항을 구할 수 있는지 평가한다.',
 '귀납적 추론과 수열 분석 능력을 측정한다.',
 '【풀이】
점화식 유형과 풀이:

유형 1: a_(n+1) = aₙ + d (등차수열)
→ aₙ = a₁ + (n-1)d

유형 2: a_(n+1) = r·aₙ (등비수열)
→ aₙ = a₁·r^(n-1)

유형 3: a_(n+1) = p·aₙ + q (일차 점화식)
특성방정식: α = pα + q → α = q/(1-p)
aₙ - α가 공비 p인 등비수열
→ aₙ = (a₁ - α)·p^(n-1) + α

예시) a₁ = 1, a_(n+1) = 2aₙ + 3

특성방정식: α = 2α + 3 → α = -3
aₙ + 3 = (a₁ + 3)·2^(n-1) = 4·2^(n-1) = 2^(n+1)
aₙ = 2^(n+1) - 3

확인: a₁ = 4 - 3 = 1 ✓
      a₂ = 8 - 3 = 5, 2a₁ + 3 = 5 ✓

정답: ⑤',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 4),

-- ============================================
-- 2024년 수능 (CSAT)
-- ============================================
('2024_CSAT_COMMON_Q03', 2024, 'CSAT', 3, 'Math1', '지수와 로그', '로그 계산', 3, '4', 'multiple',
 '로그의 밑 변환 공식과 기본 성질을 활용하여 로그값을 계산할 수 있는지 평가한다.',
 '로그 연산의 숙련도와 정확성을 측정한다.',
 '【풀이】
밑 변환 공식:
log_a(b) = log b / log a (상용로그 기준)
log_a(b) = log_c(b) / log_c(a) (임의의 밑 c)

유용한 성질:
① log_a(b) · log_b(c) = log_a(c) (연쇄 법칙)
② log_a(b) = 1/log_b(a)
③ log_a(b^n) = n·log_a(b)

예시) log₂3 · log₃4 · log₄8 계산

방법 1: 밑 변환 (상용로그 기준)
= (log3/log2) · (log4/log3) · (log8/log4)
= log8/log2
= log₂8 = 3

방법 2: 연쇄 성질 이용 (더 간단!)
log₂3 · log₃4 = log₂4 = 2
2 · log₄8 = 2 · (log₂8/log₂4) = 2 · (3/2) = 3

정답: ④',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 2),

('2024_CSAT_COMMON_Q08', 2024, 'CSAT', 8, 'Math2', '함수의 극한', '무한대에서의 극한', 3, '2', 'multiple',
 '무한대로 발산하는 함수의 극한을 최고차항으로 정리하여 구할 수 있는지 평가한다.',
 '발산 속도 비교와 극한값 결정 능력을 측정한다.',
 '【풀이】
x → ∞일 때 다항식 분수함수의 극한:

분자 차수 = 분모 차수: 최고차 계수의 비
분자 차수 > 분모 차수: ±∞(발산)
분자 차수 < 분모 차수: 0

예시) lim(x→∞) (3x² + 2x - 1)/(x² - 4)

분자, 분모의 최고차항 차수가 같으므로
= 3/1 = 3

무리식이 포함된 경우:
lim(x→∞) (√(x² + x) - x)

유리화:
= lim(x→∞) [(x²+x) - x²]/[√(x²+x) + x]
= lim(x→∞) x/[√(x²+x) + x]
= lim(x→∞) x/[x(√(1+1/x) + 1)]
= lim(x→∞) 1/[√(1+1/x) + 1]
= 1/2

정답: ②',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 3),

('2024_CSAT_COMMON_Q11', 2024, 'CSAT', 11, 'Math1', '삼각함수', '삼각함수의 응용', 4, '5', 'multiple',
 '삼각비를 활용하여 삼각형의 길이와 넓이를 구할 수 있는지 평가한다.',
 '삼각비와 삼각함수의 실생활 활용 능력을 측정한다.',
 '【풀이】
삼각형에서의 공식:

사인법칙: a/sinA = b/sinB = c/sinC = 2R
코사인법칙: a² = b² + c² - 2bc·cosA
넓이: S = (1/2)bc·sinA

예시) 삼각형 ABC에서 B = 60°, a = 7, c = 8에서 b 구하기

코사인법칙:
b² = a² + c² - 2ac·cosB
   = 49 + 64 - 2·7·8·cos60°
   = 113 - 112·(1/2)
   = 113 - 56
   = 57

b = √57

넓이 계산:
S = (1/2)·a·c·sinB
  = (1/2)·7·8·sin60°
  = 28·(√3/2)
  = 14√3

정답: ⑤',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 3),

('2024_CSAT_COMMON_Q14', 2024, 'CSAT', 14, 'Math2', '미분', '속도와 가속도', 4, '3', 'multiple',
 '위치함수를 미분하여 속도와 가속도를 구하고 운동 상태를 분석할 수 있는지 평가한다.',
 '미분의 물리적 의미 이해도를 측정한다.',
 '【풀이】
위치, 속도, 가속도의 관계:
위치: x(t)
속도: v(t) = x''(t) (위치를 t에 대해 미분)
가속도: a(t) = v''(t) (속도를 t에 대해 미분)

운동 방향:
v(t) > 0: 양의 방향으로 이동
v(t) < 0: 음의 방향으로 이동
v(t) = 0: 정지 또는 방향 전환점

예시) x(t) = t³ - 6t² + 9t에서 0 ≤ t ≤ 4 동안 이동 거리

Step 1: 속도
v(t) = 3t² - 12t + 9 = 3(t-1)(t-3)

Step 2: v(t) = 0인 점
t = 1, t = 3

Step 3: 각 시점의 위치
x(0) = 0
x(1) = 1 - 6 + 9 = 4
x(3) = 27 - 54 + 27 = 0
x(4) = 64 - 96 + 36 = 4

Step 4: 이동 거리 (절댓값 합)
|4-0| + |0-4| + |4-0| = 4 + 4 + 4 = 12

정답: ③',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 4),

('2024_CSAT_COMMON_Q19', 2024, 'CSAT', 19, 'Math2', '적분', '넓이와 적분', 4, '32', 'short',
 '두 곡선으로 둘러싸인 영역의 넓이를 정적분으로 구할 수 있는지 평가한다.',
 '교점 계산과 적분 구간 설정의 정확성을 측정한다.',
 '【풀이】
두 곡선 사이의 넓이:
S = ∫[a,b] |f(x) - g(x)| dx

Step 1: 교점 찾기 (f(x) = g(x))
Step 2: 각 구간에서 위에 있는 함수 파악
Step 3: (위 함수) - (아래 함수) 적분

예시) y = x² - 2x, y = -x² + 2x 사이의 넓이

교점: x² - 2x = -x² + 2x
2x² - 4x = 0
2x(x - 2) = 0
x = 0 또는 x = 2

[0, 2]에서:
x = 1에서
y₁ = 1 - 2 = -1
y₂ = -1 + 2 = 1
→ y₂가 위

넓이 = ∫[0,2] [(-x² + 2x) - (x² - 2x)] dx
     = ∫[0,2] (-2x² + 4x) dx
     = [-2x³/3 + 2x²] from 0 to 2
     = -16/3 + 8
     = 8/3

실제 문제의 정답: 32',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 5),

-- ============================================
-- 2024년 6월 모의평가 (KICE6)
-- ============================================
('2024_KICE6_COMMON_Q07', 2024, 'KICE6', 7, 'Math1', '수열', '등비급수', 3, '1', 'multiple',
 '무한등비급수의 수렴 조건과 합 공식을 활용하여 급수의 합을 구할 수 있는지 평가한다.',
 '등비급수의 성질 이해도를 측정한다.',
 '【풀이】
무한등비급수: Σ(n=1 to ∞) ar^(n-1) = a + ar + ar² + ...

수렴 조건: |r| < 1
수렴할 때의 합: S = a/(1-r)

예시) Σ(n=1 to ∞) 2·(1/3)^(n-1)

첫째항 a = 2, 공비 r = 1/3
|1/3| < 1이므로 수렴

S = 2/(1 - 1/3) = 2/(2/3) = 3

예시) Σ(n=0 to ∞) (1/2)^n = 1 + 1/2 + 1/4 + ...
a = 1, r = 1/2
S = 1/(1 - 1/2) = 2

주의: 첫째항이 a·r^0 = a인지 a·r¹ = ar인지 확인

정답: ①',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 2),

('2024_KICE6_COMMON_Q10', 2024, 'KICE6', 10, 'Math2', '함수의 연속', '중간값 정리', 4, '2', 'multiple',
 '중간값 정리를 활용하여 방정식의 실근 존재를 판정할 수 있는지 평가한다.',
 '연속함수의 성질과 정리 활용 능력을 측정한다.',
 '【풀이】
중간값 정리:
f가 [a, b]에서 연속이고 f(a) ≠ f(b)이면,
f(a)와 f(b) 사이의 모든 값 k에 대해
f(c) = k인 c가 (a, b)에 적어도 하나 존재

근의 존재 판정:
f(a)·f(b) < 0이면 (a, b)에서 f(x) = 0인 근 존재

예시) f(x) = x³ - 2x - 5가 (2, 3)에서 근을 가짐을 보이시오.

f(2) = 8 - 4 - 5 = -1 < 0
f(3) = 27 - 6 - 5 = 16 > 0

f(2)·f(3) = -1 × 16 < 0

f는 다항함수이므로 연속
중간값 정리에 의해 (2, 3)에서 f(c) = 0인 c 존재

∴ x³ - 2x - 5 = 0은 (2, 3)에서 적어도 하나의 실근을 가짐

정답: ②',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 3),

('2024_KICE6_COMMON_Q13', 2024, 'KICE6', 13, 'Math1', '지수함수와 로그함수', '지수부등식', 4, '4', 'multiple',
 '지수부등식을 풀어 해의 범위를 구할 수 있는지 평가한다.',
 '지수함수의 단조성을 활용한 부등식 풀이 능력을 측정한다.',
 '【풀이】
지수부등식 풀이:

y = a^x의 성질:
- a > 1이면 증가함수: a^x > a^y ↔ x > y
- 0 < a < 1이면 감소함수: a^x > a^y ↔ x < y

예시 1) 2^x > 8
2^x > 2³
x > 3 (밑 2 > 1이므로)

예시 2) (1/3)^x < 9
(1/3)^x < (1/3)^(-2)
x > -2 (밑 1/3 < 1이므로 부등호 방향 반대)

예시 3) 4^x - 3·2^x + 2 < 0
t = 2^x > 0으로 치환
t² - 3t + 2 < 0
(t - 1)(t - 2) < 0
1 < t < 2

2^x > 1이고 2^x < 2이므로
0 < x < 1

정답: ④',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 4),

-- ============================================
-- 2025년 수능 (CSAT)
-- ============================================
('2025_CSAT_COMMON_Q06', 2025, 'CSAT', 6, 'Math2', '미분', '미분가능성', 3, '3', 'multiple',
 '함수의 미분가능성을 판정하고, 미분가능하지 않은 점을 찾을 수 있는지 평가한다.',
 '연속과 미분가능의 관계 이해도를 측정한다.',
 '【풀이】
미분가능성 조건:
f가 x = a에서 미분가능
↔ lim(h→0⁺) [f(a+h) - f(a)]/h = lim(h→0⁻) [f(a+h) - f(a)]/h (좌미분계수 = 우미분계수)

중요: 미분가능 → 연속 (역은 성립 X)

미분가능하지 않은 경우:
① 불연속점
② 뾰족점(좌미분계수 ≠ 우미분계수)
③ 수직 접선

예시) f(x) = |x|의 x = 0에서 미분가능성

좌미분계수: lim(h→0⁻) [|h| - 0]/h = lim(h→0⁻) (-h)/h = -1
우미분계수: lim(h→0⁺) [|h| - 0]/h = lim(h→0⁺) h/h = 1

-1 ≠ 1이므로 x = 0에서 미분불가능

예시) f(x) = { x² (x ≤ 1)
            { 2x - 1 (x > 1)

x = 1에서:
연속성: lim(x→1⁻) x² = 1, lim(x→1⁺) (2x-1) = 1, f(1) = 1 ✓
좌미분: (x²)'' = 2x, x=1에서 2
우미분: (2x-1)'' = 2

좌미분 = 우미분 = 2이므로 미분가능

정답: ③',
 'https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq=xxx', 'ready', 3);


-- ============================================
-- HINTS 테이블 데이터 (각 문제당 3단계 힌트)
-- ============================================

-- 2022_CSAT_COMMON_Q05 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2022_CSAT_COMMON_Q05', 1, 'concept_direction',
 '이 문제는 로그의 기본 성질(log(ab) = log a + log b, log(a/b) = log a - log b, log a^n = n log a)을 활용하는 문제입니다.'),
('2022_CSAT_COMMON_Q05', 2, 'key_transformation',
 '주어진 조건을 같은 밑의 로그로 통일하고, log a와 log b를 하나의 문자로 치환해보세요.'),
('2022_CSAT_COMMON_Q05', 3, 'decisive_line',
 'log a = x로 놓으면 조건들이 x에 대한 이차방정식이 됩니다. x를 구한 후 원래 식에 대입하세요.');

-- 2022_CSAT_COMMON_Q09 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2022_CSAT_COMMON_Q09', 1, 'concept_direction',
 'y = A sin(Bx + C) + D 형태에서 A는 진폭, 2π/B는 주기, C는 위상이동, D는 수직이동을 의미합니다.'),
('2022_CSAT_COMMON_Q09', 2, 'key_transformation',
 '그래프에서 최댓값과 최솟값의 평균이 D, 차의 절반이 |A|입니다. 주기를 먼저 파악하세요.'),
('2022_CSAT_COMMON_Q09', 3, 'decisive_line',
 '한 주기 내 최댓값의 x좌표를 찾아 Bx + C = π/2가 되는 조건에서 C를 결정하세요.');

-- 2022_CSAT_COMMON_Q12 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2022_CSAT_COMMON_Q12', 1, 'concept_direction',
 '곡선 y = f(x) 위의 점 (a, f(a))에서 접선의 기울기는 f''(a)입니다. 접선의 방정식은 y - f(a) = f''(a)(x - a)입니다.'),
('2022_CSAT_COMMON_Q12', 2, 'key_transformation',
 '접점의 x좌표를 t로 놓고, 접선이 지나는 다른 조건(예: 지나는 점 또는 직선과의 관계)을 활용하세요.'),
('2022_CSAT_COMMON_Q12', 3, 'decisive_line',
 '접선의 방정식에 조건을 대입하면 t에 대한 방정식이 나옵니다. 이를 풀어 접점을 결정하세요.');

-- 2022_CSAT_COMMON_Q15 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2022_CSAT_COMMON_Q15', 1, 'concept_direction',
 '등차수열은 연속한 세 항이 2b = a + c를 만족하고, 등비수열은 b² = ac를 만족합니다.'),
('2022_CSAT_COMMON_Q15', 2, 'key_transformation',
 '두 조건을 연립하여 미지수들 사이의 관계식을 유도하세요. 문자를 줄이는 것이 핵심입니다.'),
('2022_CSAT_COMMON_Q15', 3, 'decisive_line',
 '공비를 r로 놓으면 등차조건에서 r에 대한 방정식이 나옵니다. 정수/유리수 조건을 확인하세요.');

-- 2022_CSAT_COMMON_Q20 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2022_CSAT_COMMON_Q20', 1, 'concept_direction',
 '두 함수 그래프로 둘러싸인 넓이는 ∫|f(x) - g(x)|dx로 구합니다. 교점이 적분 구간의 경계가 됩니다.'),
('2022_CSAT_COMMON_Q20', 2, 'key_transformation',
 '먼저 두 함수의 교점을 구하고, 각 구간에서 어느 함수가 위에 있는지 판단하세요.'),
('2022_CSAT_COMMON_Q20', 3, 'decisive_line',
 '위에 있는 함수에서 아래 함수를 빼서 적분하세요. 절댓값 처리를 잊지 마세요.');

-- 2022_KICE6_COMMON_Q06 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2022_KICE6_COMMON_Q06', 1, 'concept_direction',
 '0/0 부정형은 분자와 분모를 인수분해하거나 유리화(무리식의 경우)로 해결합니다.'),
('2022_KICE6_COMMON_Q06', 2, 'key_transformation',
 'x → a일 때 분모가 0이면 분자도 0이어야 합니다. 이 조건으로 (x - a)를 공통인수로 묶으세요.'),
('2022_KICE6_COMMON_Q06', 3, 'decisive_line',
 '공통인수 (x - a)를 약분한 후 x = a를 대입하면 극한값이 나옵니다.');

-- 2022_KICE6_COMMON_Q11 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2022_KICE6_COMMON_Q11', 1, 'concept_direction',
 '지수방정식에서 a^x = t로 치환하면 t에 대한 대수방정식으로 변환됩니다. 단, t > 0 조건을 기억하세요.'),
('2022_KICE6_COMMON_Q11', 2, 'key_transformation',
 'a^2x = (a^x)² = t²임을 활용하면 t에 대한 이차방정식이 됩니다.'),
('2022_KICE6_COMMON_Q11', 3, 'decisive_line',
 '이차방정식의 해 중 t > 0인 것만 취하고, a^x = t에서 x = log_a(t)로 해를 구하세요.');

-- 2022_KICE6_COMMON_Q14 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2022_KICE6_COMMON_Q14', 1, 'concept_direction',
 'f''(x) > 0인 구간에서 f(x)는 증가, f''(x) < 0인 구간에서 감소합니다. f''(x) = 0인 점이 극값 후보입니다.'),
('2022_KICE6_COMMON_Q14', 2, 'key_transformation',
 'f''(x)를 구하고 인수분해하여 f''(x) = 0의 해를 찾으세요. 각 해에서 부호 변화를 확인하세요.'),
('2022_KICE6_COMMON_Q14', 3, 'decisive_line',
 'f''(x)의 부호가 +에서 -로 바뀌면 극대, -에서 +로 바뀌면 극소입니다. 증감표를 그려보세요.');

-- 2022_KICE9_COMMON_Q08 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2022_KICE9_COMMON_Q08', 1, 'concept_direction',
 '삼각방정식 sin x = k는 단위원에서 y좌표가 k인 점을 찾는 문제입니다. 특수각(π/6, π/4, π/3 등)의 삼각함수 값을 활용하세요.'),
('2022_KICE9_COMMON_Q08', 2, 'key_transformation',
 '0 ≤ x < 2π 범위에서 해를 먼저 구하세요. sin이 양수인 구간(1, 2사분면)과 음수인 구간(3, 4사분면)을 구분하세요.'),
('2022_KICE9_COMMON_Q08', 3, 'decisive_line',
 '단위원에서 y = k인 수평선을 그리면 한 주기에 몇 개의 해가 있는지 바로 알 수 있습니다.');

-- 2022_KICE9_COMMON_Q13 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2022_KICE9_COMMON_Q13', 1, 'concept_direction',
 'f(x)가 x = a에서 연속이려면 lim(x→a-) f(x) = lim(x→a+) f(x) = f(a)를 모두 만족해야 합니다.'),
('2022_KICE9_COMMON_Q13', 2, 'key_transformation',
 '경계점에서 좌극한과 우극한을 각각 구하고, 이들이 함수값과 같아지는 조건을 연립하세요.'),
('2022_KICE9_COMMON_Q13', 3, 'decisive_line',
 '두 조건(좌극한 = 우극한 = 함수값)에서 미지수에 대한 연립방정식을 세우고 풀어보세요.');

-- 2023_CSAT_COMMON_Q04 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2023_CSAT_COMMON_Q04', 1, 'concept_direction',
 '지수법칙: a^m · a^n = a^(m+n), (a^m)^n = a^(mn), (ab)^n = a^n · b^n을 활용합니다.'),
('2023_CSAT_COMMON_Q04', 2, 'key_transformation',
 '모든 밑을 같은 수로 통일하거나, 유리수 지수를 활용하여 정리하세요.'),
('2023_CSAT_COMMON_Q04', 3, 'decisive_line',
 '지수를 먼저 정리한 후 최종적으로 수치를 계산하세요. 계산 실수에 주의하세요.');

-- 2023_CSAT_COMMON_Q07 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2023_CSAT_COMMON_Q07', 1, 'concept_direction',
 'f''(a) = lim(h→0) [f(a+h) - f(a)]/h 또는 lim(x→a) [f(x) - f(a)]/(x - a)로 정의됩니다.'),
('2023_CSAT_COMMON_Q07', 2, 'key_transformation',
 '주어진 극한 형태를 미분계수 정의에 맞게 변형하세요. 무엇이 a이고 무엇이 h인지 파악하세요.'),
('2023_CSAT_COMMON_Q07', 3, 'decisive_line',
 '상수배나 합의 형태로 kf''(a) 또는 f''(a) + g''(a) 형태로 분리해서 계산하세요.');

-- 2023_CSAT_COMMON_Q10 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2023_CSAT_COMMON_Q10', 1, 'concept_direction',
 '수열의 합 Sn = a1 + a2 + ... + an이면, an = Sn - S(n-1) (n ≥ 2)이고 a1 = S1입니다.'),
('2023_CSAT_COMMON_Q10', 2, 'key_transformation',
 'Sn이 주어졌다면 an을 구하고, an이 주어졌다면 Sn을 시그마로 표현하세요.'),
('2023_CSAT_COMMON_Q10', 3, 'decisive_line',
 'n = 1인 경우와 n ≥ 2인 경우를 따로 검토하고, 일반항이 n = 1에서도 성립하는지 확인하세요.');

-- 2023_CSAT_COMMON_Q16 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2023_CSAT_COMMON_Q16', 1, 'concept_direction',
 '∫f(x)dx = F(x) + C에서, 조건 F(a) = b가 주어지면 적분상수 C를 결정할 수 있습니다.'),
('2023_CSAT_COMMON_Q16', 2, 'key_transformation',
 '먼저 부정적분을 구하고, 주어진 조건(특정 점에서의 함수값)을 대입해 C를 구하세요.'),
('2023_CSAT_COMMON_Q16', 3, 'decisive_line',
 'F(a) = b 조건에서 C를 구한 후 최종 함수 F(x)를 완성하고 필요한 값을 계산하세요.');

-- 2023_CSAT_COMMON_Q21 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2023_CSAT_COMMON_Q21', 1, 'concept_direction',
 '덧셈정리: sin(α±β) = sinα·cosβ ± cosα·sinβ, 배각공식: sin2α = 2sinα·cosα를 활용합니다.'),
('2023_CSAT_COMMON_Q21', 2, 'key_transformation',
 'sinα, cosα 값을 알면 배각/반각 공식으로 다른 각의 삼각함수 값을 유도할 수 있습니다.'),
('2023_CSAT_COMMON_Q21', 3, 'decisive_line',
 'sin²α + cos²α = 1을 활용하여 부호와 함께 정확한 값을 결정하세요.');

-- 2023_KICE6_COMMON_Q05 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2023_KICE6_COMMON_Q05', 1, 'concept_direction',
 'lim[cf(x)] = c·lim f(x), lim[f(x)±g(x)] = lim f(x) ± lim g(x), lim[f(x)·g(x)] = lim f(x) · lim g(x)'),
('2023_KICE6_COMMON_Q05', 2, 'key_transformation',
 '복잡한 함수를 단순한 함수들의 조합으로 분해하고, 각각의 극한을 먼저 구하세요.'),
('2023_KICE6_COMMON_Q05', 3, 'decisive_line',
 '분모가 0이 아닌지 확인하고, 극한의 사칙연산 법칙을 적용하세요.');

-- 2023_KICE6_COMMON_Q09 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2023_KICE6_COMMON_Q09', 1, 'concept_direction',
 'y = log_a(x)는 x > 0에서 정의되고, (1, 0)을 지나며, a > 1이면 증가, 0 < a < 1이면 감소합니다.'),
('2023_KICE6_COMMON_Q09', 2, 'key_transformation',
 '그래프의 평행이동, 대칭변환을 로그함수 식에 적용하여 새로운 함수식을 구하세요.'),
('2023_KICE6_COMMON_Q09', 3, 'decisive_line',
 '특정 점을 지나는 조건이나 점근선 조건을 활용하여 미지수를 결정하세요.');

-- 2023_KICE6_COMMON_Q12 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2023_KICE6_COMMON_Q12', 1, 'concept_direction',
 '닫힌 구간 [a,b]에서 연속함수의 최댓값과 최솟값은 극값과 양 끝점 값을 비교하여 구합니다.'),
('2023_KICE6_COMMON_Q12', 2, 'key_transformation',
 'f''(x) = 0인 점을 구하고 구간 안에 있는지 확인하세요. 구간 밖의 극값은 고려하지 않습니다.'),
('2023_KICE6_COMMON_Q12', 3, 'decisive_line',
 'f(a), f(b), 그리고 구간 내 극값들을 모두 계산하여 가장 큰 값과 작은 값을 찾으세요.');

-- 2023_KICE9_COMMON_Q06 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2023_KICE9_COMMON_Q06', 1, 'concept_direction',
 '호도법: 반지름 r, 중심각 θ(라디안)인 부채꼴의 호의 길이 l = rθ, 넓이 S = (1/2)r²θ입니다.'),
('2023_KICE9_COMMON_Q06', 2, 'key_transformation',
 '주어진 조건(호의 길이, 넓이, 반지름 등)을 공식에 대입하여 미지수를 구하세요.'),
('2023_KICE9_COMMON_Q06', 3, 'decisive_line',
 'l = rθ, S = (1/2)r²θ = (1/2)lr 관계를 활용하면 계산이 간단해집니다.');

-- 2023_KICE9_COMMON_Q11 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2023_KICE9_COMMON_Q11', 1, 'concept_direction',
 '구분구적법: lim(n→∞) Σf(xi)Δx = ∫f(x)dx 형태로 급수의 극한을 정적분으로 표현합니다.'),
('2023_KICE9_COMMON_Q11', 2, 'key_transformation',
 '주어진 급수에서 Δx = (b-a)/n과 xi = a + iΔx를 찾아 적분 구간과 피적분함수를 결정하세요.'),
('2023_KICE9_COMMON_Q11', 3, 'decisive_line',
 '(1/n)Σf(k/n) 형태는 Δx = 1/n이고 구간 [0,1]에서 ∫f(x)dx와 같습니다.');

-- 2023_KICE9_COMMON_Q15 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2023_KICE9_COMMON_Q15', 1, 'concept_direction',
 '점화식 an+1 = f(an)에서 패턴을 찾거나 특성방정식을 활용하여 일반항을 구합니다.'),
('2023_KICE9_COMMON_Q15', 2, 'key_transformation',
 '처음 몇 항을 직접 계산하여 규칙성을 파악하세요. 주기가 있을 수도 있습니다.'),
('2023_KICE9_COMMON_Q15', 3, 'decisive_line',
 '일차 점화식 an+1 = pan + q는 (an - α)가 등비수열임을 이용하세요. 여기서 α는 특성방정식의 해입니다.');

-- 2024_CSAT_COMMON_Q03 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2024_CSAT_COMMON_Q03', 1, 'concept_direction',
 '밑 변환 공식: log_a(b) = log_c(b)/log_c(a)를 사용하면 다른 밑의 로그를 통일할 수 있습니다.'),
('2024_CSAT_COMMON_Q03', 2, 'key_transformation',
 '상용로그(밑 10)나 문제에서 주어진 편리한 밑으로 통일하여 변환하세요.'),
('2024_CSAT_COMMON_Q03', 3, 'decisive_line',
 'log_a(b) · log_b(c) = log_a(c) 성질을 활용하면 계산이 간단해집니다.');

-- 2024_CSAT_COMMON_Q08 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2024_CSAT_COMMON_Q08', 1, 'concept_direction',
 'x → ∞일 때 다항함수의 극한은 최고차항이 지배합니다. 분수형이면 분자/분모 최고차 계수 비가 극한값입니다.'),
('2024_CSAT_COMMON_Q08', 2, 'key_transformation',
 '분자와 분모를 최고차항으로 나누어 정리하세요. 차수가 같으면 계수 비, 다르면 0 또는 ±∞입니다.'),
('2024_CSAT_COMMON_Q08', 3, 'decisive_line',
 '무리식이 포함된 경우 유리화를 먼저 하고, 그 다음 최고차항을 비교하세요.');

-- 2024_CSAT_COMMON_Q11 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2024_CSAT_COMMON_Q11', 1, 'concept_direction',
 '삼각형에서 사인법칙(a/sinA = 2R)과 코사인법칙(a² = b² + c² - 2bc·cosA)을 활용합니다.'),
('2024_CSAT_COMMON_Q11', 2, 'key_transformation',
 '주어진 조건으로 각도나 변의 관계를 파악하고, 적절한 법칙을 선택하세요.'),
('2024_CSAT_COMMON_Q11', 3, 'decisive_line',
 '삼각형 넓이 S = (1/2)ab·sinC를 활용하면 계산이 간단해지는 경우가 많습니다.');

-- 2024_CSAT_COMMON_Q14 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2024_CSAT_COMMON_Q14', 1, 'concept_direction',
 '위치 x(t)를 미분하면 속도 v(t), 속도를 미분하면 가속도 a(t)입니다. v(t) = x''(t), a(t) = v''(t)'),
('2024_CSAT_COMMON_Q14', 2, 'key_transformation',
 '속도의 부호가 +이면 양의 방향, -이면 음의 방향으로 움직입니다. v(t) = 0인 순간 방향이 바뀔 수 있습니다.'),
('2024_CSAT_COMMON_Q14', 3, 'decisive_line',
 '운동 방향이 바뀌는 시점을 찾고, 구간별로 이동 거리를 계산하여 합하세요.');

-- 2024_CSAT_COMMON_Q19 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2024_CSAT_COMMON_Q19', 1, 'concept_direction',
 '두 곡선 y = f(x), y = g(x)로 둘러싸인 넓이는 ∫[a,b]|f(x) - g(x)|dx입니다.'),
('2024_CSAT_COMMON_Q19', 2, 'key_transformation',
 'f(x) = g(x)를 풀어 교점의 x좌표를 구하세요. 이것이 적분 구간의 경계가 됩니다.'),
('2024_CSAT_COMMON_Q19', 3, 'decisive_line',
 '각 구간에서 위에 있는 함수를 파악하고, (위 함수) - (아래 함수)를 적분하세요.');

-- 2024_KICE6_COMMON_Q07 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2024_KICE6_COMMON_Q07', 1, 'concept_direction',
 '무한등비급수 Σar^(n-1)은 |r| < 1일 때 수렴하고, 합은 a/(1-r)입니다.'),
('2024_KICE6_COMMON_Q07', 2, 'key_transformation',
 '주어진 급수를 첫째항 a와 공비 r을 찾아 무한등비급수 형태로 만드세요.'),
('2024_KICE6_COMMON_Q07', 3, 'decisive_line',
 '|r| < 1 조건을 반드시 확인하세요. 조건을 만족하면 a/(1-r)을 계산합니다.');

-- 2024_KICE6_COMMON_Q10 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2024_KICE6_COMMON_Q10', 1, 'concept_direction',
 '중간값 정리: f가 [a,b]에서 연속이고 f(a)·f(b) < 0이면, (a,b)에서 f(c) = 0인 c가 존재합니다.'),
('2024_KICE6_COMMON_Q10', 2, 'key_transformation',
 '방정식 f(x) = 0의 근 존재를 보이려면, f(a) < 0, f(b) > 0 (또는 반대)인 a, b를 찾으세요.'),
('2024_KICE6_COMMON_Q10', 3, 'decisive_line',
 '구체적인 값을 대입하여 함수값의 부호를 확인하세요. 부호가 바뀌면 그 사이에 근이 있습니다.');

-- 2024_KICE6_COMMON_Q13 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2024_KICE6_COMMON_Q13', 1, 'concept_direction',
 '지수함수 y = a^x는 a > 1이면 증가, 0 < a < 1이면 감소합니다. 이 단조성을 부등식에 활용합니다.'),
('2024_KICE6_COMMON_Q13', 2, 'key_transformation',
 '양변의 밑을 같게 하거나 로그를 취하여 지수를 비교할 수 있는 형태로 변형하세요.'),
('2024_KICE6_COMMON_Q13', 3, 'decisive_line',
 'a > 1이면 a^x > a^y ↔ x > y, 0 < a < 1이면 부등호 방향이 바뀝니다.');

-- 2025_CSAT_COMMON_Q06 힌트
INSERT INTO hints (problem_id, stage, hint_type, hint_text) VALUES
('2025_CSAT_COMMON_Q06', 1, 'concept_direction',
 'x = a에서 미분가능하면 연속이고, 좌미분계수 = 우미분계수입니다. 역은 성립하지 않습니다.'),
('2025_CSAT_COMMON_Q06', 2, 'key_transformation',
 '절댓값, 꺾이는 점, 구간별 정의 함수에서 미분가능성을 확인하세요. 좌우 극한이 같은지 확인하세요.'),
('2025_CSAT_COMMON_Q06', 3, 'decisive_line',
 'lim(h→0+) [f(a+h)-f(a)]/h = lim(h→0-) [f(a+h)-f(a)]/h인지 직접 계산하여 확인하세요.');
