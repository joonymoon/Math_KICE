/**
 * ============================================
 * Make.com JavaScript 모듈 코드 모음
 * 복사해서 "Code by Make" 모듈에 붙여넣기
 * ============================================
 */

// ============================================
// 모듈 1: 문항 분리 + 배점 추출
// 시나리오 A에서 사용
// ============================================
// Input 변수 설정 (Make에서):
//   - raw_text: PDF에서 추출한 전체 텍스트
//   - year: 연도 문자열 (예: "2024")
//   - exam: 시험 유형 (예: "CSAT", "KICE6", "KICE9")
//   - drive_link: 원본 PDF Google Drive 링크
//   - page_images_folder: 페이지 이미지 폴더 링크

function splitProblems(inputData) {
    const raw = (inputData.raw_text || "").replace(/\r/g, "\n");

    // 1) 문항 시작 패턴
    // "1." "1)" "1번" "1 ." " 12. " 등 대응
    const startRe = /(?:^|\n)\s*(\d{1,2})\s*(?:[.)]|번)\s+/g;

    // 2) 문항별 위치 추출
    let matches = [];
    let m;
    while ((m = startRe.exec(raw)) !== null) {
        matches.push({ q: parseInt(m[1], 10), idx: m.index });
    }
    matches.push({ q: null, idx: raw.length }); // 끝 마커

    // 3) 문항별 블록 생성
    let items = [];
    for (let i = 0; i < matches.length - 1; i++) {
        const qno = matches[i].q;
        const block = raw.slice(matches[i].idx, matches[i + 1].idx).trim();

        // 4) 배점 추출: [3점], (3점), 3점, [4점] 등
        let score = null;
        const scoreRe = /(?:\[|\()?\s*([234])\s*점\s*(?:\]|\))?/;
        const sm = block.match(scoreRe);
        if (sm) score = parseInt(sm[1], 10);

        // 5) problem_id 생성
        const problem_id = `${inputData.year}_${inputData.exam}_COMMON_Q${String(qno).padStart(2, "0")}`;

        items.push({
            problem_id,
            year: parseInt(inputData.year, 10),
            exam: inputData.exam,
            question_no: qno,
            score,
            extract_text: block.substring(0, 2000), // 길이 제한 (Supabase TEXT 대비)
            source_ref: inputData.drive_link || "",
            page_images_folder: inputData.page_images_folder || ""
        });
    }

    return { items };
}

// Make에서 실행되는 코드 (위 함수를 직접 인라인으로 사용)
// 아래 코드를 Make "Code" 모듈에 붙여넣기:

/*
const raw = (inputData.raw_text || "").replace(/\r/g, "\n");
const startRe = /(?:^|\n)\s*(\d{1,2})\s*(?:[.)]|번)\s+/g;

let matches = [];
let m;
while ((m = startRe.exec(raw)) !== null) {
    matches.push({ q: parseInt(m[1], 10), idx: m.index });
}
matches.push({ q: null, idx: raw.length });

let items = [];
for (let i = 0; i < matches.length - 1; i++) {
    const qno = matches[i].q;
    const block = raw.slice(matches[i].idx, matches[i + 1].idx).trim();

    let score = null;
    const scoreRe = /(?:\[|\()?\s*([234])\s*점\s*(?:\]|\))?/;
    const sm = block.match(scoreRe);
    if (sm) score = parseInt(sm[1], 10);

    const problem_id = `${inputData.year}_${inputData.exam}_COMMON_Q${String(qno).padStart(2, "0")}`;

    items.push({
        problem_id,
        year: parseInt(inputData.year, 10),
        exam: inputData.exam,
        question_no: qno,
        score,
        extract_text: block.substring(0, 2000),
        source_ref: inputData.drive_link || "",
        page_images_folder: inputData.page_images_folder || ""
    });
}

return { items };
*/


// ============================================
// 모듈 2: 정답표 파싱
// 시나리오 B에서 사용
// ============================================
// Input 변수 설정 (Make에서):
//   - answer_text: 정답 PDF에서 추출한 텍스트
//   - year: 연도 문자열
//   - exam: 시험 유형

function parseAnswerSheet(inputData) {
    const t = (inputData.answer_text || "").replace(/\r/g, "\n");

    // 동그라미 숫자 → 일반 숫자 변환
    const circled = {
        "①": "1", "②": "2", "③": "3", "④": "4", "⑤": "5",
        "⓵": "1", "⓶": "2", "⓷": "3", "⓸": "4", "⓹": "5",
        "❶": "1", "❷": "2", "❸": "3", "❹": "4", "❺": "5"
    };

    // 패턴: "1 ②" "1. 2" "1) 4" "1번 3" "21 -5" 등
    const re = /(?:^|\n)\s*(\d{1,2})\s*[.)번]?\s*([①②③④⑤⓵⓶⓷⓸⓹❶❷❸❹❺]|[1-5]|-?\d+(?:\.\d+)?)/g;

    let map = {};
    let m;
    while ((m = re.exec(t)) !== null) {
        const qno = parseInt(m[1], 10);
        let ans = m[2];

        // 동그라미 → 숫자
        if (circled[ans]) ans = circled[ans];

        // 중복 방지 (정답표가 페이지에 여러 번 나올 수 있음)
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
}

// Make에서 실행되는 코드 (아래 복사):

/*
const t = (inputData.answer_text || "").replace(/\r/g, "\n");

const circled = {
    "①": "1", "②": "2", "③": "3", "④": "4", "⑤": "5",
    "⓵": "1", "⓶": "2", "⓷": "3", "⓸": "4", "⓹": "5",
    "❶": "1", "❷": "2", "❸": "3", "❹": "4", "❺": "5"
};

const re = /(?:^|\n)\s*(\d{1,2})\s*[.)번]?\s*([①②③④⑤⓵⓶⓷⓸⓹❶❷❸❹❺]|[1-5]|-?\d+(?:\.\d+)?)/g;

let map = {};
let m;
while ((m = re.exec(t)) !== null) {
    const qno = parseInt(m[1], 10);
    let ans = m[2];
    if (circled[ans]) ans = circled[ans];
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
*/


// ============================================
// 모듈 3: 파일명 파싱 (보조)
// 트리거 직후 사용
// ============================================
// Input 변수:
//   - fileName: Google Drive 파일명 (예: "2024_KICE6_PROBLEM.pdf")

function parseFileName(inputData) {
    const fileName = inputData.fileName || "";

    // 확장자 제거
    const baseName = fileName.replace(/\.[^/.]+$/, "");

    // 언더스코어로 분리
    const parts = baseName.split("_");

    return {
        year: parts[0] || "",           // "2024"
        exam: parts[1] || "",           // "KICE6" or "CSAT"
        paper: parts[2] || "",          // "PROBLEM" or "ANSWER"
        full_id: `${parts[0]}_${parts[1]}` // "2024_KICE6"
    };
}

// Make에서 실행되는 코드:

/*
const fileName = inputData.fileName || "";
const baseName = fileName.replace(/\.[^/.]+$/, "");
const parts = baseName.split("_");

return {
    year: parts[0] || "",
    exam: parts[1] || "",
    paper: parts[2] || "",
    full_id: `${parts[0]}_${parts[1]}`
};
*/


// ============================================
// 모듈 4: 공통 문항 필터링 (3·4점만)
// 시나리오 A 후처리에서 사용 (선택)
// ============================================
// Input 변수:
//   - items: 문항 배열

function filterCommonProblems(inputData) {
    const items = inputData.items || [];

    // 공통 범위 문항만 필터링 (보통 1~22번이 공통)
    // 3·4점만 필터링
    const filtered = items.filter(item => {
        // 공통 범위 확인 (수능 기준 1~22번)
        const isCommon = item.question_no >= 1 && item.question_no <= 22;

        // 3·4점만
        const isTargetScore = item.score === 3 || item.score === 4;

        return isCommon && isTargetScore;
    });

    return { items: filtered };
}

// Make에서 실행되는 코드:

/*
const items = inputData.items || [];

const filtered = items.filter(item => {
    const isCommon = item.question_no >= 1 && item.question_no <= 22;
    const isTargetScore = item.score === 3 || item.score === 4;
    return isCommon && isTargetScore;
});

return { items: filtered };
*/


// ============================================
// 모듈 5: Supabase Upsert용 데이터 변환
// Iterator 전에 사용 (선택)
// ============================================
// Input 변수:
//   - items: 문항 배열

function prepareForSupabase(inputData) {
    const items = inputData.items || [];

    const prepared = items.map(item => ({
        // Supabase 컬럼명과 정확히 일치
        problem_id: item.problem_id,
        year: item.year,
        exam: item.exam,
        question_no: item.question_no,
        score: item.score,
        extract_text: item.extract_text,
        source_ref: item.source_ref,
        page_images_folder: item.page_images_folder,
        status: "needs_review",
        confidence: 0
    }));

    return { items: prepared };
}


// ============================================
// 정규식 패턴 레퍼런스
// ============================================

const REGEX_PATTERNS = {
    // 문항 시작 (문항 분리용)
    questionStart: /(?:^|\n)\s*(\d{1,2})\s*(?:[.)]|번)\s+/g,

    // 배점 추출
    scoreExtract: /(?:\[|\()?\s*([234])\s*점\s*(?:\]|\))?/,

    // 정답표 파싱
    answerTable: /(?:^|\n)\s*(\d{1,2})\s*[.)번]?\s*([①②③④⑤⓵⓶⓷⓸⓹❶❷❸❹❺]|[1-5]|-?\d+(?:\.\d+)?)/g,

    // 동그라미 숫자
    circledNumbers: {
        "①": "1", "②": "2", "③": "3", "④": "4", "⑤": "5",
        "⓵": "1", "⓶": "2", "⓷": "3", "⓸": "4", "⓹": "5",
        "❶": "1", "❷": "2", "❸": "3", "❹": "4", "❺": "5"
    }
};


// ============================================
// 테스트용 예시
// ============================================

// 테스트 데이터
const testRawText = `
제2교시 수학 영역

1. 다음 식의 값을 구하시오. [3점]
   log₂ 8 + log₃ 27

2. 함수 f(x) = x³ - 3x의 극값을 구하시오. [4점]

3. 등차수열 {aₙ}에서 a₁ = 2, d = 3일 때, a₁₀의 값은? [3점]
   ① 25  ② 27  ③ 29  ④ 31  ⑤ 33
`;

const testAnswerText = `
정답
1 ②
2 ④
3 ③
4 ①
5 ⑤
`;

// 테스트 실행 (Node.js 환경에서)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        splitProblems,
        parseAnswerSheet,
        parseFileName,
        filterCommonProblems,
        prepareForSupabase,
        REGEX_PATTERNS
    };

    // 테스트
    console.log("=== 문항 분리 테스트 ===");
    const splitResult = splitProblems({
        raw_text: testRawText,
        year: "2024",
        exam: "CSAT",
        drive_link: "https://drive.google.com/...",
        page_images_folder: "https://drive.google.com/..."
    });
    console.log(JSON.stringify(splitResult, null, 2));

    console.log("\n=== 정답표 파싱 테스트 ===");
    const answerResult = parseAnswerSheet({
        answer_text: testAnswerText,
        year: "2024",
        exam: "CSAT"
    });
    console.log(JSON.stringify(answerResult, null, 2));
}
