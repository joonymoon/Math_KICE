// 수능 문제 뷰어 - 카카오톡 웹뷰용
// Props: problemData (from server)

// Toast notification component
function Toast({ message, type, onClose }) {
  React.useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const bgColor = type === 'error' ? '#ef4444' : type === 'success' ? '#22c55e' : '#3b82f6';

  return (
    <div
      style={{
        position: 'fixed', top: 16, left: '50%', transform: 'translateX(-50%)',
        background: bgColor, color: 'white', padding: '10px 20px',
        borderRadius: 10, fontSize: 14, fontWeight: 600, zIndex: 100,
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        animation: 'toastIn 0.3s ease-out',
      }}
    >
      {message}
    </div>
  );
}

function ProblemViewer({ problemData }) {
  const [scale, setScale] = React.useState(1);
  const [selectedAnswer, setSelectedAnswer] = React.useState(null);
  const [userAnswer, setUserAnswer] = React.useState('');
  const [showResult, setShowResult] = React.useState(false);
  const [hintLevel, setHintLevel] = React.useState(0);
  const [result, setResult] = React.useState(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [toast, setToast] = React.useState(null);
  const [resultVisible, setResultVisible] = React.useState(false);

  const handleZoomIn = () => setScale(prev => Math.min(prev + 0.25, 2.5));
  const handleZoomOut = () => setScale(prev => Math.max(prev - 0.25, 0.5));
  const handleReset = () => setScale(1);

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
  };

  // C4: webview-safe close/back
  const handleClose = () => {
    if (window.history.length > 1) {
      window.history.back();
    } else {
      try { window.close(); } catch (e) { /* ignore */ }
    }
  };

  const handleSubmit = async () => {
    const answer = problemData.is_multiple_choice ? selectedAnswer : userAnswer;

    if (!answer) {
      // H4: toast instead of alert
      showToast('답을 선택하거나 입력해주세요.', 'error');
      return;
    }

    // Race condition prevention: set flag synchronously
    setIsSubmitting(true);

    try {
      const response = await fetch('/problem/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          problem_id: problemData.problem_id,
          user_answer: String(answer)
        })
      });

      const data = await response.json();
      setResult(data);
      setShowResult(true);
      // Trigger fade-in animation
      requestAnimationFrame(() => setResultVisible(true));
    } catch (error) {
      console.error('Submit error:', error);
      // H4: toast instead of alert
      showToast('제출 중 오류가 발생했습니다.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleShowHint = () => {
    const nextLevel = hintLevel + 1;
    if (nextLevel <= 3) {
      setHintLevel(nextLevel);
    }
  };

  // C2: Get ALL hints up to current level (accumulate)
  const getHints = () => {
    const hints = [];
    if (hintLevel >= 1 && problemData.hint1) hints.push({ level: 1, text: problemData.hint1 });
    if (hintLevel >= 2 && problemData.hint2) hints.push({ level: 2, text: problemData.hint2 });
    if (hintLevel >= 3 && problemData.hint3) hints.push({ level: 3, text: problemData.hint3 });
    return hints;
  };

  const examName = {
    'CSAT': '수능',
    'KICE6': '6월 평가원',
    'KICE9': '9월 평가원'
  }[problemData.exam] || problemData.exam;

  // M2: Single difficulty display combining score and level
  const difficultyLabel = {
    '2점': '하',
    '3점': '중',
    '4점': '상'
  }[problemData.difficulty] || '중';

  const difficultyColor = {
    '하': { bg: '#dbeafe', text: '#1d4ed8' },
    '중': { bg: '#fef3c7', text: '#b45309' },
    '상': { bg: '#fee2e2', text: '#dc2626' },
  }[difficultyLabel] || { bg: '#e5e7eb', text: '#4b5563' };

  const hints = getHints();

  return (
    <div className="bg-gray-100 min-h-screen flex flex-col">
      {/* Toast */}
      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
      )}

      {/* Animation styles */}
      <style>{`
        @keyframes toastIn {
          from { opacity: 0; transform: translateX(-50%) translateY(-10px); }
          to { opacity: 1; transform: translateX(-50%) translateY(0); }
        }
        @keyframes resultSlideUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .result-enter { animation: resultSlideUp 0.4s ease-out forwards; }
      `}</style>

      {/* 헤더 */}
      <div className="bg-white border-b sticky top-0 z-50">
        <div className="flex items-center justify-between px-4 py-3">
          {/* C4: webview-safe close */}
          <button onClick={handleClose} className="flex items-center gap-1 text-gray-600">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <div className="text-center">
            <div className="font-bold text-gray-800">#{problemData.number}</div>
            <div className="text-xs text-gray-500">{problemData.year} {examName}</div>
          </div>

          <div className="w-5"></div>
        </div>

        {/* M2: Single combined difficulty tag + unit */}
        <div className="px-4 pb-3 flex items-center gap-2 overflow-x-auto">
          <span
            className="flex-shrink-0 px-2 py-1 rounded text-xs font-medium"
            style={{ background: difficultyColor.bg, color: difficultyColor.text }}
          >
            {problemData.difficulty} ({difficultyLabel})
          </span>
          {problemData.unit && (
            <span className="flex-shrink-0 bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs font-medium">
              {problemData.unit}
            </span>
          )}
        </div>
      </div>

      {/* 문제 이미지 영역 */}
      <div className="flex-1 overflow-auto bg-gray-200 relative">
        <div
          className="min-h-full flex items-start justify-center p-4 transition-transform duration-200"
          style={{ transform: `scale(${scale})`, transformOrigin: 'top center' }}
        >
          {problemData.image_url ? (
            <img
              src={problemData.image_url}
              alt="문제 이미지"
              className="max-w-full h-auto bg-white rounded-lg shadow-lg"
            />
          ) : (
            <div className="bg-white rounded-lg shadow-lg p-6 max-w-md">
              <div className="text-gray-500 text-center">문제 이미지가 없습니다.</div>
            </div>
          )}
        </div>

        {/* M1: Zoom controls inside image area, not overlapping bottom UI */}
        <div className="absolute right-3 top-3 flex flex-col gap-2 z-40">
          <button
            onClick={handleZoomIn}
            className="w-9 h-9 bg-white/90 rounded-full shadow flex items-center justify-center text-gray-700"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
          <div className="text-center text-xs text-gray-600 bg-white/90 rounded px-1 py-0.5 shadow">
            {Math.round(scale * 100)}%
          </div>
          <button
            onClick={handleZoomOut}
            className="w-9 h-9 bg-white/90 rounded-full shadow flex items-center justify-center text-gray-700"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>
          {scale !== 1 && (
            <button
              onClick={handleReset}
              className="w-9 h-9 bg-white/90 rounded-full shadow flex items-center justify-center text-gray-700 text-xs font-medium"
            >
              1:1
            </button>
          )}
        </div>
      </div>

      {/* C3: Hints visible BOTH before and after submission */}
      {hints.length > 0 && (
        <div className="bg-yellow-50 border-t border-yellow-200 px-4 py-3 space-y-2">
          {hints.map(h => (
            <div key={h.level} className="flex items-start gap-2">
              <span className="flex-shrink-0 w-5 h-5 rounded-full bg-yellow-400 text-white text-xs font-bold flex items-center justify-center mt-0.5">
                {h.level}
              </span>
              <div className="text-sm text-yellow-900">{h.text}</div>
            </div>
          ))}
        </div>
      )}

      {/* 결과 표시 - L3: fade-in animation */}
      {showResult && result && (
        <div className={`px-4 py-3 text-white ${resultVisible ? 'result-enter' : ''} ${result.is_correct ? 'bg-green-500' : 'bg-red-500'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {result.is_correct ? (
                <>
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                  </svg>
                  <span className="font-bold">정답입니다!</span>
                </>
              ) : (
                <>
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
                  </svg>
                  <span className="font-bold">
                    오답입니다. 정답은 {result.correct_answer}{problemData.is_multiple_choice ? '번' : ''}
                  </span>
                </>
              )}
            </div>
            <span className="text-sm opacity-90">+{result.score}점</span>
          </div>

          {/* H5: Learning feedback on wrong answer */}
          {!result.is_correct && (
            <div className="mt-2 pt-2 border-t border-white/30 text-sm">
              {result.solution ? (
                <div>
                  <div className="font-bold mb-1">풀이:</div>
                  <div className="opacity-90">{result.solution}</div>
                </div>
              ) : (
                <div className="opacity-90">
                  힌트를 다시 확인하고, 풀이 과정을 복습해보세요.
                </div>
              )}
              {hintLevel < 3 && (
                <button
                  onClick={handleShowHint}
                  className="mt-2 px-3 py-1 bg-white/20 rounded text-xs font-medium hover:bg-white/30 transition"
                >
                  힌트 더 보기 ({hintLevel + 1}/3)
                </button>
              )}
            </div>
          )}

          {/* Show solution for correct answers too */}
          {result.is_correct && result.solution && (
            <div className="mt-2 pt-2 border-t border-white/30">
              <div className="text-sm font-bold mb-1">풀이:</div>
              <div className="text-sm opacity-90">{result.solution}</div>
            </div>
          )}
        </div>
      )}

      {/* 답안 입력/선택 영역 - visible even after submit (disabled) */}
      <div className="bg-white p-4 border-t">
        {problemData.is_multiple_choice && problemData.choices && problemData.choices.length > 0 ? (
          <div className="space-y-2 mb-3">
            <div className="text-sm font-bold text-gray-700 mb-2">
              {showResult ? '선택한 답:' : '답을 선택하세요:'}
            </div>
            <div className="grid grid-cols-5 gap-2">
              {problemData.choices.map((choice, index) => {
                const choiceNum = index + 1;
                const isSelected = selectedAnswer === choiceNum;
                const isCorrectAnswer = showResult && result && Number(result.correct_answer) === choiceNum;
                const isWrongSelected = showResult && isSelected && !result?.is_correct;

                let btnClass = 'bg-white text-gray-700 border-gray-200';
                if (showResult) {
                  if (isCorrectAnswer) btnClass = 'bg-green-500 text-white border-green-600';
                  else if (isWrongSelected) btnClass = 'bg-red-400 text-white border-red-500';
                  else btnClass = 'bg-gray-100 text-gray-400 border-gray-200';
                } else if (isSelected) {
                  btnClass = 'bg-blue-500 text-white border-blue-600';
                }

                return (
                  <button
                    key={choiceNum}
                    onClick={() => !showResult && setSelectedAnswer(choiceNum)}
                    disabled={showResult}
                    className={`p-3 rounded-lg border-2 text-center font-bold transition-all ${btnClass}`}
                  >
                    {choiceNum}
                  </button>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="mb-3">
            <label className="block text-sm font-bold text-gray-700 mb-2">
              {showResult ? '입력한 답:' : '답을 입력하세요:'}
            </label>
            {/* H6: numeric inputmode for subjective questions */}
            <input
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              value={userAnswer}
              onChange={(e) => !showResult && setUserAnswer(e.target.value)}
              readOnly={showResult}
              placeholder="답 입력"
              className={`w-full px-4 py-3 border-2 rounded-lg focus:outline-none ${
                showResult
                  ? 'border-gray-200 bg-gray-50 text-gray-500'
                  : 'border-gray-200 focus:border-blue-500'
              }`}
            />
          </div>
        )}
      </div>

      {/* 하단 액션 바 */}
      <div className="bg-white border-t p-4 sticky bottom-0 z-30">
        {!showResult ? (
          <div className="flex gap-3">
            {hintLevel < 3 && (
              <button
                onClick={handleShowHint}
                className="flex-1 py-3 px-4 bg-gray-100 text-gray-700 rounded-xl font-medium flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                힌트 {hintLevel + 1}/3
              </button>
            )}
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || (!problemData.is_multiple_choice ? !userAnswer : !selectedAnswer)}
              className={`flex-[2] py-3 px-4 rounded-xl font-bold flex items-center justify-center gap-2 ${
                (!problemData.is_multiple_choice ? userAnswer : selectedAnswer) && !isSubmitting
                  ? 'bg-blue-500 text-white hover:bg-blue-600'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              {isSubmitting ? '제출 중...' : '정답 확인'}
              {!isSubmitting && (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              )}
            </button>
          </div>
        ) : (
          <button
            onClick={handleClose}
            className="w-full py-3 px-4 bg-gray-100 text-gray-700 rounded-xl font-medium"
          >
            닫기
          </button>
        )}
      </div>
    </div>
  );
}
