import React, { useState, useRef } from 'react';

// 카카오톡 수능 문제 뷰어 프로토타입
// 흐름: 카톡 메시지(웰컴카드) → 문제보기 클릭 → 웹뷰(문제 + 답안선택)

export default function KakaoProblemViewer() {
  const [currentView, setCurrentView] = useState('kakao'); // kakao | viewer
  const [scale, setScale] = useState(1);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [showHint, setShowHint] = useState(false);
  const viewerRef = useRef(null);

  // 샘플 문제 데이터
  const problem = {
    id: 1,
    number: 7,
    year: '2026학년도',
    type: '수능',
    subject: '수학',
    points: 3,
    difficulty: '중',
    topic: '정적분의 활용',
    correctAnswer: 3,
    choices: ['18/5', '7/2', '17/5', '33/10', '16/5'],
  };

  const handleZoomIn = () => setScale(prev => Math.min(prev + 0.25, 2.5));
  const handleZoomOut = () => setScale(prev => Math.max(prev - 0.25, 0.5));
  const handleReset = () => setScale(1);

  const handleSubmit = () => {
    if (selectedAnswer !== null) {
      setShowResult(true);
    }
  };

  const isCorrect = selectedAnswer === problem.correctAnswer;

  // 카카오톡 채팅 화면 (웰컴 카드)
  const KakaoChat = () => (
    <div className="bg-[#B2C7D9] min-h-screen p-4">
      {/* 카톡 헤더 */}
      <div className="flex items-center mb-4 -mx-4 -mt-4 px-4 py-3 bg-[#B2C7D9]">
        <svg className="w-6 h-6 mr-3" fill="none" stroke="#333" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        <div className="flex items-center flex-1">
          <div className="w-10 h-10 bg-yellow-400 rounded-full flex items-center justify-center mr-3">
            <span className="text-lg">📐</span>
          </div>
          <div>
            <div className="font-semibold text-gray-800">수능수학 튜터</div>
            <div className="text-xs text-gray-600">응답률 99%</div>
          </div>
        </div>
        <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>

      {/* 날짜 구분선 */}
      <div className="text-center text-xs text-gray-500 my-4">2026년 2월 6일 목요일</div>

      {/* 봇 메시지 - 인사 */}
      <div className="flex items-end mb-3">
        <div className="w-10 h-10 bg-yellow-400 rounded-full flex items-center justify-center mr-2 flex-shrink-0">
          <span className="text-lg">📐</span>
        </div>
        <div className="max-w-[75%]">
          <div className="bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
            <p className="text-sm text-gray-800">
              안녕하세요 Jay님! 👋<br/>
              오늘의 수학 문제가 도착했어요.
            </p>
          </div>
          <div className="text-xs text-gray-500 mt-1 ml-1">오전 9:00</div>
        </div>
      </div>

      {/* 봇 메시지 - 문제 카드 (웰컴 카드) */}
      <div className="flex items-end mb-3">
        <div className="w-10 h-10 bg-yellow-400 rounded-full flex items-center justify-center mr-2 flex-shrink-0 opacity-0">
          <span className="text-lg">📐</span>
        </div>
        <div className="max-w-[80%]">
          {/* 리치 메시지 카드 */}
          <div className="bg-white rounded-2xl overflow-hidden shadow-lg">
            {/* 카드 썸네일 - 문제 미리보기 */}
            <div className="bg-gradient-to-br from-blue-500 to-indigo-600 p-4 text-white relative overflow-hidden">
              {/* 배경 패턴 */}
              <div className="absolute inset-0 opacity-10">
                <div className="absolute top-2 right-2 text-6xl">∫</div>
                <div className="absolute bottom-2 left-2 text-4xl">π</div>
                <div className="absolute top-1/2 left-1/2 text-3xl">Σ</div>
              </div>
              
              <div className="relative">
                <div className="flex items-center justify-between mb-2">
                  <span className="bg-white/20 px-2 py-0.5 rounded text-xs font-medium">
                    {problem.year} {problem.type}
                  </span>
                  <span className="bg-yellow-400 text-yellow-900 px-2 py-0.5 rounded text-xs font-bold">
                    {problem.points}점
                  </span>
                </div>
                
                <div className="text-3xl font-bold mb-1">#{problem.number}</div>
                <div className="text-sm opacity-90">{problem.topic}</div>
                
                <div className="mt-3 flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    problem.difficulty === '상' ? 'bg-red-400/30' :
                    problem.difficulty === '중' ? 'bg-yellow-400/30' : 'bg-green-400/30'
                  }`}>
                    난이도 {problem.difficulty}
                  </span>
                  <span className="px-2 py-0.5 bg-white/20 rounded text-xs">
                    정적분
                  </span>
                </div>
              </div>
            </div>
            
            {/* 카드 본문 */}
            <div className="p-4">
              <h3 className="font-bold text-gray-800 mb-2">
                두 곡선과 직선으로 둘러싸인 넓이
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                정적분을 활용한 넓이 계산 문제입니다.
                그래프를 보고 두 곡선 사이의 넓이를 구하세요.
              </p>
              
              {/* 미니 프리뷰 */}
              <div className="bg-gray-50 rounded-lg p-3 mb-3 border border-gray-100">
                <div className="text-xs text-gray-500 mb-2">문제 미리보기</div>
                <div className="text-sm text-gray-700 font-mono">
                  y = x² + 3, y = -⅕x² + 3
                </div>
                <div className="text-sm text-gray-700 font-mono">
                  직선 x = 2
                </div>
              </div>
              
              {/* CTA 버튼 */}
              <button
                onClick={() => setCurrentView('viewer')}
                className="w-full bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-bold py-3 px-4 rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                <span>문제 풀기</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>
          <div className="text-xs text-gray-500 mt-1 ml-1">오전 9:00</div>
        </div>
      </div>

      {/* 빠른 응답 버튼들 */}
      <div className="flex gap-2 mt-4 overflow-x-auto pb-2">
        <button className="flex-shrink-0 bg-white px-4 py-2 rounded-full text-sm text-gray-700 shadow-sm">
          📊 학습 현황
        </button>
        <button className="flex-shrink-0 bg-white px-4 py-2 rounded-full text-sm text-gray-700 shadow-sm">
          📝 오답 노트
        </button>
        <button className="flex-shrink-0 bg-white px-4 py-2 rounded-full text-sm text-gray-700 shadow-sm">
          ⏰ 알림 설정
        </button>
      </div>

      {/* 하단 입력창 (비활성) */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t p-2 flex items-center gap-2">
        <button className="p-2 text-gray-400">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
        <input 
          type="text" 
          placeholder="메시지 입력" 
          className="flex-1 bg-gray-100 rounded-full px-4 py-2 text-sm"
          disabled
        />
        <button className="p-2 text-gray-400">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>
      </div>
    </div>
  );

  // 문제 뷰어 (웹뷰)
  const ProblemViewer = () => (
    <div className="bg-gray-100 min-h-screen flex flex-col">
      {/* 뷰어 헤더 */}
      <div className="bg-white border-b sticky top-0 z-50">
        <div className="flex items-center justify-between px-4 py-3">
          <button 
            onClick={() => {
              setCurrentView('kakao');
              setSelectedAnswer(null);
              setShowResult(false);
              setScale(1);
            }}
            className="flex items-center gap-1 text-gray-600"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          
          <div className="text-center">
            <div className="font-bold text-gray-800">#{problem.number}</div>
            <div className="text-xs text-gray-500">{problem.year} {problem.type}</div>
          </div>
          
          <button className="text-gray-600">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z" />
            </svg>
          </button>
        </div>
        
        {/* 문제 정보 태그 */}
        <div className="px-4 pb-3 flex items-center gap-2 overflow-x-auto">
          <span className="flex-shrink-0 bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs font-medium">
            {problem.points}점
          </span>
          <span className="flex-shrink-0 bg-orange-100 text-orange-700 px-2 py-1 rounded text-xs font-medium">
            난이도 {problem.difficulty}
          </span>
          <span className="flex-shrink-0 bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs font-medium">
            {problem.topic}
          </span>
        </div>
      </div>

      {/* 문제 이미지 영역 (확대/축소 가능) */}
      <div 
        ref={viewerRef}
        className="flex-1 overflow-auto bg-gray-200 relative"
        style={{ touchAction: 'pan-x pan-y pinch-zoom' }}
      >
        <div 
          className="min-h-full flex items-start justify-center p-4 transition-transform duration-200"
          style={{ transform: `scale(${scale})`, transformOrigin: 'top center' }}
        >
          {/* 문제 이미지 (실제로는 추출된 PNG) */}
          <div className="bg-white rounded-lg shadow-lg p-6 max-w-md">
            {/* 문제 본문 */}
            <div className="mb-6">
              <div className="font-bold text-lg mb-4">
                7. 두 곡선 y = x² + 3, y = -⅕x² + 3과 직선 x = 2로 둘러싸인 부분의 넓이는? [3점]
              </div>
            </div>
            
            {/* 그래프 영역 */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <svg viewBox="0 0 200 180" className="w-full h-48">
                {/* 좌표축 */}
                <line x1="30" y1="150" x2="180" y2="150" stroke="#333" strokeWidth="1.5"/>
                <line x1="30" y1="10" x2="30" y2="150" stroke="#333" strokeWidth="1.5"/>
                
                {/* 축 레이블 */}
                <text x="175" y="165" fontSize="12" fill="#333">x</text>
                <text x="15" y="20" fontSize="12" fill="#333">y</text>
                <text x="25" y="165" fontSize="10" fill="#333">O</text>
                
                {/* 그리드 */}
                <line x1="90" y1="150" x2="90" y2="145" stroke="#666" strokeWidth="1"/>
                <line x1="150" y1="150" x2="150" y2="145" stroke="#666" strokeWidth="1"/>
                <text x="145" y="165" fontSize="10" fill="#666">x=2</text>
                
                {/* y = x² + 3 곡선 */}
                <path 
                  d="M 30 95 Q 60 120 90 87 Q 120 40 150 -20" 
                  fill="none" 
                  stroke="#3B82F6" 
                  strokeWidth="2"
                  clipPath="url(#graphClip)"
                />
                <text x="155" y="50" fontSize="10" fill="#3B82F6">y=x²+3</text>
                
                {/* y = -1/5 x² + 3 곡선 */}
                <path 
                  d="M 30 95 Q 60 98 90 102 Q 120 108 150 115" 
                  fill="none" 
                  stroke="#EF4444" 
                  strokeWidth="2"
                />
                <text x="155" y="125" fontSize="9" fill="#EF4444">y=-⅕x²+3</text>
                
                {/* x = 2 직선 */}
                <line x1="150" y1="10" x2="150" y2="150" stroke="#10B981" strokeWidth="1.5" strokeDasharray="4,2"/>
                
                {/* 영역 표시 (음영) */}
                <path 
                  d="M 30 95 Q 60 120 90 87 Q 110 60 150 40 L 150 115 Q 120 108 90 102 Q 60 98 30 95 Z" 
                  fill="#8B5CF6" 
                  fillOpacity="0.2"
                  stroke="#8B5CF6"
                  strokeWidth="1"
                />
                
                <defs>
                  <clipPath id="graphClip">
                    <rect x="0" y="0" width="200" height="150"/>
                  </clipPath>
                </defs>
              </svg>
            </div>

            {/* 선택지 */}
            <div className="space-y-2">
              {problem.choices.map((choice, index) => {
                const choiceNum = index + 1;
                const isSelected = selectedAnswer === choiceNum;
                const showCorrectness = showResult;
                const isCorrectChoice = choiceNum === problem.correctAnswer;
                
                let bgColor = 'bg-white border-gray-200';
                let textColor = 'text-gray-700';
                
                if (showCorrectness) {
                  if (isCorrectChoice) {
                    bgColor = 'bg-green-50 border-green-500';
                    textColor = 'text-green-700';
                  } else if (isSelected && !isCorrectChoice) {
                    bgColor = 'bg-red-50 border-red-500';
                    textColor = 'text-red-700';
                  }
                } else if (isSelected) {
                  bgColor = 'bg-blue-50 border-blue-500';
                  textColor = 'text-blue-700';
                }
                
                return (
                  <button
                    key={choiceNum}
                    onClick={() => !showResult && setSelectedAnswer(choiceNum)}
                    disabled={showResult}
                    className={`w-full p-3 rounded-lg border-2 text-left flex items-center gap-3 transition-all ${bgColor} ${textColor} ${!showResult && 'hover:border-blue-300'}`}
                  >
                    <span className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      isSelected ? 'bg-blue-500 text-white' : 
                      showCorrectness && isCorrectChoice ? 'bg-green-500 text-white' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {choiceNum}
                    </span>
                    <span className="font-medium">{choice}</span>
                    
                    {showCorrectness && isCorrectChoice && (
                      <svg className="w-5 h-5 ml-auto text-green-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                      </svg>
                    )}
                    {showCorrectness && isSelected && !isCorrectChoice && (
                      <svg className="w-5 h-5 ml-auto text-red-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
                      </svg>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* 결과 표시 */}
      {showResult && (
        <div className={`px-4 py-3 ${isCorrect ? 'bg-green-500' : 'bg-red-500'} text-white`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {isCorrect ? (
                <>
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                  </svg>
                  <span className="font-bold">정답입니다! 🎉</span>
                </>
              ) : (
                <>
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
                  </svg>
                  <span className="font-bold">오답입니다. 정답은 {problem.correctAnswer}번</span>
                </>
              )}
            </div>
            <span className="text-sm opacity-90">+{isCorrect ? problem.points * 10 : 0}점</span>
          </div>
        </div>
      )}

      {/* 줌 컨트롤 (플로팅) */}
      <div className="fixed right-4 bottom-32 flex flex-col gap-2 z-40">
        <button 
          onClick={handleZoomIn}
          className="w-10 h-10 bg-white rounded-full shadow-lg flex items-center justify-center text-gray-700 hover:bg-gray-50"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
        <div className="text-center text-xs text-gray-500 bg-white rounded px-1">
          {Math.round(scale * 100)}%
        </div>
        <button 
          onClick={handleZoomOut}
          className="w-10 h-10 bg-white rounded-full shadow-lg flex items-center justify-center text-gray-700 hover:bg-gray-50"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        </button>
        <button 
          onClick={handleReset}
          className="w-10 h-10 bg-white rounded-full shadow-lg flex items-center justify-center text-gray-700 hover:bg-gray-50 text-xs font-medium"
        >
          1:1
        </button>
      </div>

      {/* 하단 액션 바 */}
      <div className="bg-white border-t p-4 sticky bottom-0">
        {!showResult ? (
          <div className="flex gap-3">
            <button 
              onClick={() => setShowHint(!showHint)}
              className="flex-1 py-3 px-4 bg-gray-100 text-gray-700 rounded-xl font-medium flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              힌트
            </button>
            <button 
              onClick={handleSubmit}
              disabled={selectedAnswer === null}
              className={`flex-[2] py-3 px-4 rounded-xl font-bold flex items-center justify-center gap-2 ${
                selectedAnswer !== null 
                  ? 'bg-blue-500 text-white hover:bg-blue-600' 
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              정답 확인
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </button>
          </div>
        ) : (
          <div className="flex gap-3">
            <button 
              className="flex-1 py-3 px-4 bg-gray-100 text-gray-700 rounded-xl font-medium flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              해설 보기
            </button>
            <button 
              onClick={() => {
                setCurrentView('kakao');
                setSelectedAnswer(null);
                setShowResult(false);
                setScale(1);
              }}
              className="flex-[2] py-3 px-4 bg-blue-500 text-white rounded-xl font-bold flex items-center justify-center gap-2"
            >
              다음 문제
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        )}
        
        {/* 힌트 표시 */}
        {showHint && !showResult && (
          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-start gap-2">
              <span className="text-yellow-500">💡</span>
              <div className="text-sm text-yellow-800">
                <strong>힌트:</strong> 두 곡선 사이의 넓이는 
                ∫₀² (위쪽 곡선 - 아래쪽 곡선) dx 로 계산합니다.
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="max-w-md mx-auto bg-white min-h-screen shadow-2xl relative overflow-hidden">
      {/* 모드 전환 인디케이터 */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-50">
        <div className="bg-black/50 text-white px-3 py-1 rounded-full text-xs backdrop-blur">
          {currentView === 'kakao' ? '📱 카카오톡' : '📝 문제 뷰어'}
        </div>
      </div>
      
      {currentView === 'kakao' ? <KakaoChat /> : <ProblemViewer />}
    </div>
  );
}
