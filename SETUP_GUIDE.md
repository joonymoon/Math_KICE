# 서비스 가입 및 설정 가이드

## 필수 가입 목록

| 서비스 | 필수 | 용도 | 예상 시간 | 비용 |
|--------|------|------|----------|------|
| Supabase | O | DB, Storage, 인증 | 5분 | 무료 |
| 카카오 개발자 | O | 카카오 로그인/메시지 | 10분 | 무료 |
| 카카오톡 채널 | O | 채널 메시지 발송 | 10분 | 무료 |
| Make.com | 선택 | 자동화 (노코드) | 5분 | 무료 1000 ops/월 |
| NHN Cloud | 선택 | 알림톡 (유료) | 30분 | 건당 8~15원 |

---

## 1. Supabase 가입 및 설정

### 1.1 가입
1. https://supabase.com 접속
2. "Start your project" 클릭
3. GitHub 계정으로 로그인

### 1.2 프로젝트 생성
1. "New Project" 클릭
2. 프로젝트 이름: `math-kice` (원하는 이름)
3. Database Password: 안전한 비밀번호 설정 (저장해두기!)
4. Region: `Northeast Asia (Seoul)` 선택
5. "Create new project" 클릭 (2~3분 소요)

### 1.3 DB 스키마 생성
1. 좌측 메뉴 "SQL Editor" 클릭
2. "New query" 클릭
3. `schema.sql` 파일 내용 전체 복사 붙여넣기
4. "Run" 클릭
5. `sample_data.sql` 파일도 동일하게 실행

### 1.4 Storage 설정 (문제 이미지용)
1. 좌측 메뉴 "Storage" 클릭
2. "New bucket" 클릭
3. Name: `problems`
4. Public bucket: ON (체크)
5. "Create bucket" 클릭

### 1.5 API 키 확인
1. 좌측 메뉴 "Project Settings" > "API"
2. 다음 값들을 `.env` 파일에 복사:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` → `SUPABASE_KEY`
   - `service_role` → `SUPABASE_SERVICE_KEY` (서버 전용, 노출 금지!)

---

## 2. 카카오 개발자 등록

### 2.1 개발자 등록
1. https://developers.kakao.com 접속
2. "로그인" 클릭 (카카오 계정)
3. 개발자 등록 동의

### 2.2 애플리케이션 생성
1. "내 애플리케이션" > "애플리케이션 추가하기"
2. 앱 이름: `수학문제배달`
3. 사업자명: 본인 이름 또는 사업자명
4. "저장" 클릭

### 2.3 플랫폼 등록
1. 생성된 앱 클릭 > "플랫폼"
2. "Web" > "사이트 도메인" 추가
   - 개발: `http://localhost:8000`
   - 운영: `https://your-domain.com`

### 2.4 카카오 로그인 설정
1. "카카오 로그인" 메뉴
2. "활성화 설정" ON
3. "Redirect URI" 등록:
   - `http://localhost:8000/auth/kakao/callback`
4. "동의항목" 설정:
   - 닉네임: 필수
   - 카카오톡 메시지 전송: 필수 (talk_message)

### 2.5 앱 키 확인
1. "앱 키" 메뉴
2. `REST API 키` → `.env`의 `KAKAO_REST_API_KEY`에 복사

---

## 3. 카카오톡 채널 개설

### 3.1 채널 생성
1. https://center-pf.kakao.com 접속
2. "새 채널 만들기" 클릭
3. 채널 정보 입력:
   - 채널 이름: `오늘의 수학문제`
   - 검색용 아이디: `math_daily` (원하는 ID)
   - 프로필 사진 등록
4. "채널 개설" 클릭

### 3.2 카카오 개발자와 연결
1. 카카오 개발자 > 앱 선택 > "카카오톡 채널"
2. "채널 연결" 클릭
3. 방금 만든 채널 선택

### 3.3 메시지 발송 설정
1. 카카오 개발자 > "메시지" 메뉴
2. "메시지 템플릿" 등록 (선택)
3. 발송 테스트 진행

---

## 4. (선택) Make.com 가입

> 코드 없이 자동화하고 싶을 때 사용

### 4.1 가입
1. https://make.com 접속
2. "Get started free" 클릭
3. 이메일 또는 Google 계정으로 가입

### 4.2 시나리오 생성
1. "Create a new scenario" 클릭
2. 모듈 추가:
   - Schedule (매일 특정 시간)
   - Supabase (문제 조회)
   - HTTP (카카오 API 호출)

### 4.3 무료 티어
- 1,000 operations/월
- 하루 33명 × 1문제 발송 가능

---

## 5. (선택) 알림톡 설정 - NHN Cloud

> 비용 발생! 대량 발송 또는 비즈니스용

### 5.1 가입
1. https://www.nhncloud.com 접속
2. 회원가입 (사업자등록증 필요)
3. 프로젝트 생성

### 5.2 알림톡 서비스 활성화
1. "Notification" > "KakaoTalk Bizmessage" 선택
2. 서비스 활성화
3. 발신 프로필 등록 (카카오톡 채널 연동)

### 5.3 템플릿 등록
1. "템플릿 관리" > "템플릿 등록"
2. 템플릿 코드: `DAILY_PROBLEM`
3. 템플릿 내용:
```
[오늘의 수학문제]

#{연도}학년도 #{시험} #{문제번호}
단원: #{단원}
배점: #{배점}점

문제 풀러 가기 👇
```
4. 심사 제출 (1~2일 소요)

### 5.4 API 키 확인
- `APP KEY` → `NHN_ALIMTALK_APP_KEY`
- `SECRET KEY` → `NHN_ALIMTALK_SECRET_KEY`

---

## 발송 방식 비교

| 방식 | 대상 | 비용 | 이미지 | 설정 난이도 |
|------|------|------|--------|------------|
| 나에게 보내기 | 본인만 | 무료 | O | 쉬움 |
| 채널 메시지 | 친구 추가자 | 무료 | O | 보통 |
| 알림톡 | 전화번호 | 유료 | X | 어려움 |

### 추천 시작 순서
1. **테스트**: "나에게 보내기"로 기능 확인
2. **베타**: 카카오톡 채널 친구 추가로 소규모 운영
3. **확장**: 알림톡으로 대규모 발송

---

## 최종 .env 파일 예시

```env
# Supabase
SUPABASE_URL=https://abcdefg.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# 카카오
KAKAO_REST_API_KEY=1234567890abcdef
KAKAO_REDIRECT_URI=http://localhost:8000/auth/kakao/callback
KAKAO_CHANNEL_ID=_xAbCdE

# (선택) NHN Cloud
NHN_ALIMTALK_APP_KEY=your-app-key
NHN_ALIMTALK_SECRET_KEY=your-secret-key
```

---

## 체크리스트

- [ ] Supabase 가입 완료
- [ ] Supabase 프로젝트 생성
- [ ] schema.sql 실행
- [ ] sample_data.sql 실행
- [ ] Storage 버킷 생성
- [ ] 카카오 개발자 등록
- [ ] 카카오 앱 생성
- [ ] 카카오톡 채널 개설
- [ ] 카카오 앱과 채널 연결
- [ ] .env 파일 설정
- [ ] 테스트 메시지 발송 성공
