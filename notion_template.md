# Notion 검수 데이터베이스 템플릿

## Database 이름
**KICE Problem Review**

---

## Properties (속성) 설정

### 1. 기본 식별 정보

| 속성명 | 타입 | 설명 | Make 매핑 |
|--------|------|------|-----------|
| **Problem ID** | Title | 문제 고유 ID | `{{item.problem_id}}` |
| **Year** | Number | 연도 (2022~2025) | `{{item.year}}` |
| **Exam** | Select | 시험 유형 | `{{item.exam}}` |
| **Q No** | Number | 문항 번호 (1~30) | `{{item.question_no}}` |

**Exam Select 옵션:**
- CSAT (수능)
- KICE6 (6월 모의평가)
- KICE9 (9월 모의평가)

---

### 2. 자동 추출 정보 (Make에서 입력)

| 속성명 | 타입 | 설명 | Make 매핑 |
|--------|------|------|-----------|
| **Score(auto)** | Number | 자동 추출 배점 | `{{item.score}}` |
| **Answer(auto)** | Text | 자동 추출 정답 | `{{item.answer}}` |
| **Extract Text** | Text | 추출된 문제 텍스트 | `{{substring(item.extract_text; 0; 500)}}` |

---

### 3. 검수자가 확정하는 정보

| 속성명 | 타입 | 설명 | Select 옵션 |
|--------|------|------|-------------|
| **Subject(verify)** | Select | 과목 (수1/수2) | Math1, Math2 |
| **Unit(verify)** | Select | 단원 | 아래 참조 |
| **Score(verify)** | Select | 확정 배점 | 2, 3, 4 |
| **Answer(verify)** | Text | 확정 정답 | - |

**Unit(verify) Select 옵션:**

수학1:
- 지수와 로그
- 지수함수와 로그함수
- 삼각함수
- 삼각함수 덧셈정리
- 수열
- 급수와 합
- 수학적 귀납법

수학2:
- 함수의 극한
- 함수의 연속
- 미분계수와 도함수
- 도함수의 활용
- 부정적분과 정적분
- 정적분의 활용

기타:
- 복합 (여러 단원)
- 기타

---

### 4. 출제 의도 & 힌트 (검수자 입력)

| 속성명 | 타입 | 설명 |
|--------|------|------|
| **Intent 1** | Text | 출제 의도 첫 번째 줄 |
| **Intent 2** | Text | 출제 의도 두 번째 줄 |
| **Hint 1** | Text | 힌트 ① 개념 방향 |
| **Hint 2** | Text | 힌트 ② 핵심 전환 |
| **Hint 3** | Text | 힌트 ③ 결정적 한 줄 |

---

### 5. 소스 & 링크

| 속성명 | 타입 | 설명 | Make 매핑 |
|--------|------|------|-----------|
| **Source PDF** | URL | 원본 PDF Drive 링크 | `{{item.source_ref}}` |
| **Page Images Folder** | URL | 페이지 이미지 폴더 | `{{item.page_images_folder}}` |
| **Img Page Refs** | Text | 해당 문항 페이지 | 검수자 입력 (예: p03-p04) |
| **Problem Image** | Files & media | 문제 이미지 | 검수자 업로드 |

---

### 6. 상태 & 동기화

| 속성명 | 타입 | 설명 | Select 옵션 |
|--------|------|------|-------------|
| **Status** | Select | 검수 상태 | Needs Review, In Progress, Ready, Hold |
| **Supabase UUID** | Text | Supabase problems.id | `{{supabase_result.id}}` |
| **Confidence** | Number | AI 분류 신뢰도 | 0.00 ~ 1.00 |
| **Last Synced** | Date | 마지막 동기화 | 자동 |

---

### 7. 메모 & 태그

| 속성명 | 타입 | 설명 |
|--------|------|------|
| **Notes** | Text | 검수자 메모 |
| **Tags** | Multi-select | 특이사항 태그 |

**Tags 옵션:**
- 그림 필수
- 수식 복잡
- OCR 오류
- 정답 확인 필요
- 우선 처리

---

## Views (뷰) 구성

### 1. Board: Needs Review (칸반)

**Group by:** Status
**Filter:** Status = "Needs Review"
**Sort:** Year DESC, Exam ASC, Q No ASC

```
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│  Needs Review   │   In Progress   │      Ready      │      Hold       │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ 2025_CSAT_Q15   │ 2024_KICE9_Q12  │ 2024_CSAT_Q03   │ 2023_KICE6_Q21  │
│ 2025_CSAT_Q14   │                 │ 2024_CSAT_Q04   │                 │
│ 2025_CSAT_Q13   │                 │ 2024_CSAT_Q05   │                 │
│ ...             │                 │ ...             │                 │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

---

### 2. Table: Low Confidence

**Filter:** Confidence < 0.85
**Sort:** Confidence ASC
**Columns:** Problem ID, Year, Exam, Q No, Score(auto), Confidence, Status

---

### 3. Table: Ready Export

**Filter:** Status = "Ready"
**Sort:** Year DESC, Exam ASC, Q No ASC
**Columns:**
- Problem ID
- Year, Exam, Q No
- Subject(verify), Unit(verify)
- Score(verify), Answer(verify)
- Intent 1, Intent 2
- Hint 1, Hint 2, Hint 3
- Supabase UUID

---

### 4. Table: By Year

**Group by:** Year
**Sort:** Exam ASC, Q No ASC
**Columns:** Problem ID, Exam, Q No, Subject, Unit, Score, Status

---

### 5. Table: By Unit

**Group by:** Unit(verify)
**Filter:** Status = "Ready"
**Columns:** Problem ID, Year, Exam, Q No, Score, Answer

---

### 6. Gallery: With Images

**Filter:** Problem Image is not empty
**Card preview:** Problem Image
**Properties shown:** Problem ID, Year, Exam, Q No, Score, Status

---

## 검수 워크플로우

### Step 1: 자동 입력 확인
1. Score(auto)와 Answer(auto) 확인
2. Extract Text로 문제 내용 파악
3. 오류 있으면 Notes에 기록

### Step 2: 분류 확정
1. Subject(verify) 선택 (Math1/Math2)
2. Unit(verify) 선택
3. Score(verify) 확정
4. Answer(verify) 확정

### Step 3: 이미지 확인
1. Page Images Folder 링크로 이동
2. 해당 문항 페이지 찾기
3. Img Page Refs에 페이지 번호 입력 (예: p03-p04)
4. (선택) Problem Image에 크롭된 이미지 업로드

### Step 4: 출제의도 & 힌트 작성
1. Intent 1, Intent 2 작성
2. Hint 1 (개념 방향) 작성
3. Hint 2 (핵심 전환) 작성
4. Hint 3 (결정적 한 줄) 작성

### Step 5: 완료
1. Status를 "Ready"로 변경
2. Supabase 동기화 (별도 시나리오 또는 수동)

---

## Notion → Supabase 동기화 시나리오

### Make.com 시나리오 C: 검수 완료 동기화

**트리거:** Notion - Watch Database Items
**필터:** Status changed to "Ready"

**Supabase Update:**
```
UPDATE problems SET
  subject = {{Subject(verify)}},
  unit = {{Unit(verify)}},
  score_verified = {{Score(verify)}},
  answer_verified = {{Answer(verify)}},
  intent_1 = {{Intent 1}},
  intent_2 = {{Intent 2}},
  status = 'ready',
  updated_at = NOW()
WHERE id = {{Supabase UUID}};
```

**Hints Insert:**
```
INSERT INTO hints (problem_id, stage, hint_type, hint_text)
VALUES
  ({{Problem ID}}, 1, 'concept_direction', {{Hint 1}}),
  ({{Problem ID}}, 2, 'key_transformation', {{Hint 2}}),
  ({{Problem ID}}, 3, 'decisive_line', {{Hint 3}})
ON CONFLICT (problem_id, stage) DO UPDATE SET hint_text = EXCLUDED.hint_text;
```

---

## Notion Database 생성 순서

1. **새 페이지 생성** → Database - Full page
2. **이름:** KICE Problem Review
3. **Properties 추가** (위 목록 순서대로)
4. **Views 생성** (Board 먼저, 나머지 Table/Gallery)
5. **Make.com Integration 연결**
   - Notion Settings → Connections → Make 추가
   - Database에 Integration 권한 부여

---

## 빠른 검수 팁

| 상황 | 권장 행동 |
|------|----------|
| OCR이 깨진 경우 | Tags에 "OCR 오류" 추가, Extract Text 직접 수정 |
| 정답 불확실 | Tags에 "정답 확인 필요", Status를 "Hold" |
| 그림이 핵심인 문제 | Tags에 "그림 필수", 이미지 반드시 업로드 |
| 복합 단원 | Unit을 "복합"으로, Notes에 상세 기록 |

---

## 예상 검수 시간

| 항목 | 소요 시간 |
|------|----------|
| 자동 입력 확인 | 5초 |
| 분류 확정 | 10초 |
| 이미지 확인 | 20초 |
| 출제의도 작성 | 30초 |
| 힌트 3개 작성 | 60초 |
| **총 소요** | **~2분/문항** |

**30문항 × 16파일(4년×4회차) = 480문항**
**예상 총 소요: ~16시간** (휴식 포함 2~3일)
