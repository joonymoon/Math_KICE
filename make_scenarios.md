# Make.com 자동화 시나리오 설계

> **ARCHIVED**: 이 문서는 더 이상 사용되지 않습니다.
> Make.com 기반 자동화는 Python 파이프라인(`src/pipeline.py`)과
> Notion 동기화(`sync_to_notion.py`)로 완전히 대체되었습니다.
> 현재 시스템은 `PIPELINE_GUIDE.md`를 참고하세요.

---

## 전체 구조

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Google Drive 폴더 구조                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  /KICE/                                                                      │
│  ├── 2022/                                                                   │
│  │   ├── CSAT/                                                               │
│  │   │   ├── 2022_CSAT_PROBLEM.pdf        ← 시나리오 A 트리거               │
│  │   │   └── 2022_CSAT_ANSWER.pdf         ← 시나리오 B 트리거               │
│  │   ├── KICE6/                                                              │
│  │   │   ├── 2022_KICE6_PROBLEM.pdf                                         │
│  │   │   └── 2022_KICE6_ANSWER.pdf                                          │
│  │   └── KICE9/                                                              │
│  │       ├── 2022_KICE9_PROBLEM.pdf                                         │
│  │       └── 2022_KICE9_ANSWER.pdf                                          │
│  ├── 2023/ ...                                                               │
│  ├── 2024/ ...                                                               │
│  └── _pages/                              ← PDF→이미지 변환 결과             │
│      └── 2024/CSAT/                                                          │
│          ├── 2024_CSAT_PROBLEM_p001.png                                     │
│          ├── 2024_CSAT_PROBLEM_p002.png                                     │
│          └── ...                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 사전 준비: Custom OAuth 연결

> **중요**: **Custom OAuth Client** 방식을 사용합니다.
> Google Cloud에서 OAuth 클라이언트를 생성하고 Make.com에 연결합니다.

### Google Drive 연결 설정

**사전 준비 (BEGINNER_GUIDE.md 2장 참고):**
1. Google Cloud Console에서 프로젝트 생성
2. Google Drive API 활성화
3. OAuth 동의 화면 설정 → **프로덕션으로 게시**
4. OAuth 클라이언트 ID 생성 (웹 애플리케이션)
5. 리디렉션 URI: `https://www.integromat.com/oauth/cb/google/`

**Make.com에서 Google Drive 모듈 연결:**
1. 시나리오에서 Google Drive 모듈 추가
2. Connection에서 `Add` 클릭
3. **Show advanced settings** 토글 켜기
4. 입력 정보:
   - **Client ID**: OAuth 클라이언트 ID
   - **Client Secret**: 클라이언트 보안 비밀번호
5. `Sign in with Google` → 권한 허용

---

## 시나리오 A: 문제 PDF → 문항 레코드 생성

### A-1. 트리거 & 메타 파싱

#### (1) Google Drive - Watch files (Custom OAuth 연결)
- **Connection**: Custom OAuth 클라이언트 사용 (6.4 참고)
- **Folder**: `/KICE/` (하위 폴더 포함)
- **Filter**: 파일명에 `_PROBLEM` 포함
- **Output**: `fileId`, `fileName`, `webViewLink`

#### (2) Tools - Set variables (파일명 파싱)

```
파일명 규칙: YYYY_EXAM_PROBLEM.pdf
예: 2024_KICE6_PROBLEM.pdf
```

| 변수명 | Make 표현식 |
|--------|-------------|
| `year` | `{{substring(1.fileName; 0; 4)}}` |
| `exam` | `{{get(split(1.fileName; "_"); 1)}}` |
| `paper` | `PROBLEM` (고정) |
| `drive_link` | `{{1.webViewLink}}` |

---

### A-2. PDF → 페이지 이미지 변환

#### (3) CloudConvert - Create a job

**Tasks 구성:**
```json
{
  "tasks": {
    "import-file": {
      "operation": "import/google-drive",
      "file_id": "{{1.fileId}}"
    },
    "convert-to-png": {
      "operation": "convert",
      "input": ["import-file"],
      "output_format": "png",
      "page_range": "1-",
      "pixel_density": 200,
      "filename": "{{2.year}}_{{2.exam}}_PROBLEM_p%03d.png"
    },
    "export-to-drive": {
      "operation": "export/google-drive",
      "input": ["convert-to-png"],
      "folder_id": "YOUR_PAGES_FOLDER_ID"
    }
  }
}
```

#### (4) Google Drive - List folder contents
- Export된 이미지 파일 목록 가져오기
- **Folder**: `/KICE/_pages/{{2.year}}/{{2.exam}}/`

---

### A-3. 텍스트 추출

#### (5) PDF.co - PDF to Text
- **Input**: `{{1.fileId}}` (Google Drive 파일)
- **Output**: `raw_text`

**또는 CloudConvert:**
```json
{
  "operation": "convert",
  "input_format": "pdf",
  "output_format": "txt"
}
```

---

### A-4. 문항 분리 (JavaScript 모듈)

#### (6) Code by Make (JavaScript)

```javascript
// ============================================
// Make.com JavaScript 모듈: 문항 분리 + 배점 추출
// ============================================
// Input 변수:
//   - inputData.raw_text: PDF에서 추출한 전체 텍스트
//   - inputData.year: 연도 (예: "2024")
//   - inputData.exam: 시험 유형 (예: "CSAT")
//   - inputData.drive_link: 원본 PDF Drive 링크
//   - inputData.page_images_folder: 페이지 이미지 폴더 링크

const raw = (inputData.raw_text || "").replace(/\r/g, "\n");

// 1) 문항 시작 패턴: "1." "1)" "1번" "1 ." 등
const startRe = /(?:^|\n)\s*(\d{1,2})\s*(?:[.)]|번)\s+/g;

// 2) 문항별 블록 추출
let matches = [];
let m;
while ((m = startRe.exec(raw)) !== null) {
    matches.push({ q: parseInt(m[1], 10), idx: m.index });
}
matches.push({ q: null, idx: raw.length }); // 끝 마커

let items = [];
for (let i = 0; i < matches.length - 1; i++) {
    const qno = matches[i].q;
    const block = raw.slice(matches[i].idx, matches[i + 1].idx).trim();

    // 3) 배점 추출: [3점], (3점), 3점, [4점] 등
    let score = null;
    const scoreRe = /(?:\[|\()?\s*([234])\s*점\s*(?:\]|\))?/;
    const sm = block.match(scoreRe);
    if (sm) score = parseInt(sm[1], 10);

    // 4) problem_id 생성
    const problem_id = `${inputData.year}_${inputData.exam}_COMMON_Q${String(qno).padStart(2, "0")}`;

    items.push({
        problem_id,
        year: parseInt(inputData.year, 10),
        exam: inputData.exam,
        question_no: qno,
        score,
        extract_text: block.substring(0, 2000), // 길이 제한
        source_ref: inputData.drive_link,
        page_images_folder: inputData.page_images_folder
    });
}

return { items };
```

**Output:** `items[]` 배열

---

### A-5. Supabase Insert

#### (7) Iterator - items 반복
- Source: `{{6.items}}`

#### (8) Supabase - Insert a Row (또는 RPC 호출)

**Table**: `problems`

| Supabase 필드 | Make 값 |
|---------------|---------|
| `problem_id` | `{{7.problem_id}}` |
| `year` | `{{7.year}}` |
| `exam` | `{{7.exam}}` |
| `question_no` | `{{7.question_no}}` |
| `score` | `{{7.score}}` |
| `extract_text` | `{{7.extract_text}}` |
| `source_ref` | `{{7.source_ref}}` |
| `page_images_folder` | `{{7.page_images_folder}}` |
| `status` | `needs_review` |

**Upsert 사용 권장:** `ON CONFLICT (problem_id) DO UPDATE`

---

### A-6. Notion 검수 카드 생성

#### (9) Notion - Create a Database Item

**Database**: `KICE Problem Review`

| Notion Property | Make 값 |
|-----------------|---------|
| `Problem ID` (Title) | `{{7.problem_id}}` |
| `Year` | `{{7.year}}` |
| `Exam` | `{{7.exam}}` |
| `Q No` | `{{7.question_no}}` |
| `Score(auto)` | `{{7.score}}` |
| `Extract Text` | `{{substring(7.extract_text; 0; 500)}}` |
| `Source PDF` | `{{7.source_ref}}` |
| `Page Images Folder` | `{{7.page_images_folder}}` |
| `Status` | `Needs Review` |
| `Supabase UUID` | `{{8.id}}` |

---

## 시나리오 B: 정답 PDF → 정답표 파싱

### B-1. 트리거 & 텍스트 추출

#### (1) Google Drive - Watch files
- **Filter**: 파일명에 `_ANSWER` 포함
- **Output**: `fileId`, `fileName`

#### (2) Tools - Set variables
```
year = {{substring(1.fileName; 0; 4)}}
exam = {{get(split(1.fileName; "_"); 1)}}
```

#### (3) PDF.co - PDF to Text
- **Output**: `answer_text`

---

### B-2. 정답표 파싱 (JavaScript 모듈)

#### (4) Code by Make (JavaScript)

```javascript
// ============================================
// Make.com JavaScript 모듈: 정답표 파싱
// ============================================
// Input 변수:
//   - inputData.answer_text: 정답 PDF에서 추출한 텍스트
//   - inputData.year: 연도
//   - inputData.exam: 시험 유형

const t = (inputData.answer_text || "").replace(/\r/g, "\n");

// 동그라미 숫자 → 일반 숫자 변환
const circled = {
    "①": "1", "②": "2", "③": "3", "④": "4", "⑤": "5",
    "⓵": "1", "⓶": "2", "⓷": "3", "⓸": "4", "⓹": "5"
};

// 패턴: "1 ②" "1. 2" "1) 4" "1번 3" 등
const re = /(?:^|\n)\s*(\d{1,2})\s*[.)번]?\s*([①②③④⑤⓵⓶⓷⓸⓹]|[1-5]|-?\d+(?:\.\d+)?)/g;

let map = {};
let m;
while ((m = re.exec(t)) !== null) {
    const qno = parseInt(m[1], 10);
    let ans = m[2];

    // 동그라미 → 숫자
    if (circled[ans]) ans = circled[ans];

    // 중복 방지 (정답표가 여러 번 나올 수 있음)
    if (!map[qno]) map[qno] = ans;
}

const items = Object.keys(map)
    .map(k => ({
        question_no: parseInt(k, 10),
        answer: map[k],
        year: parseInt(inputData.year, 10),
        exam: inputData.exam
    }))
    .sort((a, b) => a.question_no - b.question_no);

return { items };
```

**Output:** `items[]` - 문항번호별 정답 배열

---

### B-3. Supabase 업데이트

#### (5) Iterator - items 반복
- Source: `{{4.items}}`

#### (6) Supabase - Update Row(s)

**Table**: `problems`

**Filter (Where 조건):**
```
year = {{5.year}}
AND exam = {{5.exam}}
AND question_no = {{5.question_no}}
```

**Update 값:**
| 필드 | 값 |
|------|-----|
| `answer` | `{{5.answer}}` |
| `updated_at` | `{{now}}` |

---

## 정규식 패턴 모음

### 1. 문항 시작 (문항 분리용)
```regex
(?:^|\n)\s*(\d{1,2})\s*(?:[.)]|번)\s+
```
- 매칭: `1.`, `1)`, `1번`, ` 12. `

### 2. 배점 추출
```regex
(?:\[|\()?\s*([234])\s*점\s*(?:\]|\))?
```
- 매칭: `[3점]`, `(4점)`, `3점`, `3 점`

### 3. 정답표 파싱
```regex
(?:^|\n)\s*(\d{1,2})\s*[.)번]?\s*([①②③④⑤]|[1-5]|-?\d+(?:\.\d+)?)
```
- 매칭: `1 ②`, `1. 3`, `12번 4`, `21 -5`

### 4. 동그라미 숫자 변환
```javascript
const circled = {"①":"1","②":"2","③":"3","④":"4","⑤":"5"};
```

---

## Make.com 시나리오 설정 체크리스트

### 사전 준비 (Custom OAuth)
- [ ] Google Cloud 프로젝트 생성
- [ ] Google Drive API 활성화
- [ ] OAuth 동의 화면 설정 → 프로덕션으로 게시
- [ ] OAuth 클라이언트 ID 생성 (웹 애플리케이션)
- [ ] 리디렉션 URI 설정: `https://www.integromat.com/oauth/cb/google/`
- [ ] Client ID, Client Secret 저장

### 시나리오 A (문제 PDF)
- [ ] Google Drive 연결 (Custom OAuth 방식)
- [ ] CloudConvert 계정 연결
- [ ] PDF.co 계정 연결 (또는 CloudConvert txt 변환)
- [ ] Supabase 연결 (API Key)
- [ ] Notion 연결 (Integration Token)
- [ ] 파일명 규칙 확인: `YYYY_EXAM_PROBLEM.pdf`

### 시나리오 B (정답 PDF)
- [ ] Google Drive 연결 (Custom OAuth 방식)
- [ ] PDF.co 계정 연결
- [ ] Supabase 연결
- [ ] 파일명 규칙 확인: `YYYY_EXAM_ANSWER.pdf`

### 연결 문제 해결
- `Show advanced settings` 토글 켜기
- Client ID, Client Secret 정확히 입력
- 리디렉션 URI가 정확한지 확인
- 앱이 "프로덕션" 상태인지 확인 (테스트 → 7일마다 재인증)

---

## 비용 예상

| 서비스 | 무료 티어 | 예상 사용량 |
|--------|----------|------------|
| Make.com | 1,000 ops/월 | ~500 ops (30문항×16파일) |
| CloudConvert | 25분/일 | ~10분/파일 |
| PDF.co | 100 credits/월 | ~50 credits |
| Supabase | 무제한 (무료) | - |
| Notion | 무제한 (무료) | - |

**결론**: 무료 티어로 22~25년 전체 처리 가능

---

## 시나리오 흐름도

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           시나리오 A: 문제 PDF                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │ Google Drive │───►│ Set Variables│───►│ CloudConvert │                   │
│  │ Watch files  │    │ (파일명 파싱) │    │ PDF → PNG    │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│                                                 │                            │
│                                                 ▼                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   PDF.co     │───►│  JavaScript  │───►│   Iterator   │                   │
│  │ PDF to Text  │    │ (문항 분리)   │    │  (items[])   │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│                                                 │                            │
│                                                 ▼                            │
│                      ┌──────────────┐    ┌──────────────┐                   │
│                      │   Supabase   │───►│    Notion    │                   │
│                      │   Upsert     │    │ Create Card  │                   │
│                      └──────────────┘    └──────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           시나리오 B: 정답 PDF                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │ Google Drive │───►│   PDF.co     │───►│  JavaScript  │                   │
│  │ Watch files  │    │ PDF to Text  │    │ (정답표 파싱) │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│                                                 │                            │
│                                                 ▼                            │
│                      ┌──────────────┐    ┌──────────────┐                   │
│                      │   Iterator   │───►│   Supabase   │                   │
│                      │  (items[])   │    │   Update     │                   │
│                      └──────────────┘    └──────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```
