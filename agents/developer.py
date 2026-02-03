"""
Developer 에이전트 - 개발 담당
카카오 API, Next.js, DB 개발
"""

from typing import Optional, Dict, List, Any
from .base import BaseAgent, Task, TaskStatus, AgentMessage


class DeveloperAgent(BaseAgent):
    """
    개발 에이전트

    역할:
    - 카카오 API 연동 개발
    - Next.js 웹 애플리케이션 개발
    - 데이터베이스 설계 및 구현
    - 백엔드 서비스 개발
    """

    def __init__(self):
        super().__init__(
            name="developer",
            role="개발",
            capabilities=[
                "카카오 API 연동",
                "Next.js 개발",
                "Supabase DB 연동",
                "REST API 개발",
                "인증/인가",
                "서버 배포",
            ]
        )
        self.codebase: Dict[str, str] = {}
        self.api_specs: Dict[str, Dict] = {}
        self.db_schema: Dict[str, Dict] = {}

    def develop_kakao_api_integration(self) -> Dict[str, Any]:
        """카카오 API 연동 개발"""
        self.log("카카오 API 연동 개발")

        code = '''
// lib/kakao.ts
import axios from 'axios';

const KAKAO_API_URL = 'https://kapi.kakao.com';

interface KakaoTokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export class KakaoService {
  private accessToken: string;
  private refreshToken: string;

  constructor(tokens: KakaoTokens) {
    this.accessToken = tokens.access_token;
    this.refreshToken = tokens.refresh_token;
  }

  // 나에게 메시지 보내기
  async sendMessageToMe(templateId: string, templateArgs: object) {
    const response = await axios.post(
      `${KAKAO_API_URL}/v2/api/talk/memo/send`,
      {
        template_id: templateId,
        template_args: JSON.stringify(templateArgs),
      },
      {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );
    return response.data;
  }

  // 친구에게 메시지 보내기
  async sendMessageToFriend(receiverUuid: string, templateId: string, templateArgs: object) {
    const response = await axios.post(
      `${KAKAO_API_URL}/v1/api/talk/friends/message/send`,
      {
        receiver_uuids: JSON.stringify([receiverUuid]),
        template_id: templateId,
        template_args: JSON.stringify(templateArgs),
      },
      {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );
    return response.data;
  }

  // 토큰 갱신
  async refreshAccessToken() {
    const response = await axios.post(
      'https://kauth.kakao.com/oauth/token',
      {
        grant_type: 'refresh_token',
        client_id: process.env.KAKAO_CLIENT_ID,
        refresh_token: this.refreshToken,
      },
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );
    this.accessToken = response.data.access_token;
    return response.data;
  }
}
'''
        self.codebase["lib/kakao.ts"] = code

        api_spec = {
            "endpoints": {
                "send_to_me": "/v2/api/talk/memo/send",
                "send_to_friend": "/v1/api/talk/friends/message/send",
                "refresh_token": "/oauth/token",
            },
            "authentication": "Bearer Token",
            "rate_limits": {
                "per_day": 1000,
                "per_user_per_day": 5,
            },
        }

        self.api_specs["kakao"] = api_spec
        return {"code": code, "api_spec": api_spec}

    def develop_nextjs_pages(self) -> Dict[str, Any]:
        """Next.js 페이지 개발"""
        self.log("Next.js 페이지 개발")

        pages = {
            "app/page.tsx": '''
// 홈페이지
import { ProblemCard } from '@/components/ProblemCard';
import { Stats } from '@/components/Stats';

export default async function Home() {
  const todayProblem = await getTodayProblem();
  const userStats = await getUserStats();

  return (
    <main className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">오늘의 수학문제</h1>

      <ProblemCard problem={todayProblem} />

      <Stats data={userStats} />
    </main>
  );
}
''',
            "app/solve/[id]/page.tsx": '''
// 문제 풀이 페이지
import { ProblemSolver } from '@/components/ProblemSolver';
import { HintPanel } from '@/components/HintPanel';
import { Timer } from '@/components/Timer';

export default async function SolvePage({ params }: { params: { id: string } }) {
  const problem = await getProblem(params.id);

  return (
    <main className="container mx-auto px-4 py-8">
      <Timer startTime={Date.now()} />

      <ProblemSolver problem={problem} />

      <HintPanel problemId={params.id} />
    </main>
  );
}
''',
            "app/dashboard/page.tsx": '''
// 대시보드 페이지
import { ProgressChart } from '@/components/ProgressChart';
import { WeakUnits } from '@/components/WeakUnits';
import { History } from '@/components/History';

export default async function DashboardPage() {
  const analytics = await getUserAnalytics();

  return (
    <main className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">학습 현황</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ProgressChart data={analytics.progress} />
        <WeakUnits units={analytics.weakUnits} />
      </div>

      <History items={analytics.history} />
    </main>
  );
}
''',
            "app/api/problems/route.ts": '''
// 문제 API
import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const year = searchParams.get('year');
  const exam = searchParams.get('exam');

  let query = supabase.from('problems').select('*').eq('status', 'ready');

  if (year) query = query.eq('year', parseInt(year));
  if (exam) query = query.eq('exam', exam);

  const { data, error } = await query;

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(data);
}
''',
            "app/api/submit/route.ts": '''
// 답안 제출 API
import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';
import { auth } from '@/lib/auth';

export async function POST(request: Request) {
  const session = await auth();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { problemId, answer, timeSpent } = await request.json();

  // 정답 확인
  const { data: problem } = await supabase
    .from('problems')
    .select('answer_verified, answer')
    .eq('problem_id', problemId)
    .single();

  const correctAnswer = problem?.answer_verified || problem?.answer;
  const isCorrect = answer.trim() === correctAnswer?.trim();

  // 결과 저장
  const { data, error } = await supabase.from('deliveries').insert({
    user_id: session.user.id,
    problem_id: problemId,
    user_answer: answer,
    is_correct: isCorrect,
    time_spent_seconds: timeSpent,
    status: 'answered',
  });

  return NextResponse.json({
    isCorrect,
    correctAnswer: isCorrect ? null : correctAnswer,
    timeSpent,
  });
}
''',
        }

        for path, code in pages.items():
            self.codebase[path] = code

        return {"pages": list(pages.keys()), "codebase": pages}

    def develop_components(self) -> Dict[str, Any]:
        """React 컴포넌트 개발"""
        self.log("React 컴포넌트 개발")

        components = {
            "components/ProblemCard.tsx": '''
'use client';
import Image from 'next/image';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';

interface Problem {
  problem_id: string;
  year: number;
  exam: string;
  question_no: number;
  score: number;
  unit: string;
  problem_image_url: string;
}

export function ProblemCard({ problem }: { problem: Problem }) {
  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Badge variant="secondary">{problem.year} {problem.exam}</Badge>
          <span className="text-2xl font-bold">{problem.question_no}번</span>
        </div>
        <Badge variant="primary">{problem.score}점</Badge>
      </div>

      <div className="relative aspect-[4/3] mb-4">
        <Image
          src={problem.problem_image_url}
          alt={`${problem.year} ${problem.exam} ${problem.question_no}번`}
          fill
          className="object-contain"
        />
      </div>

      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-500">단원: {problem.unit}</span>
        <Button href={`/solve/${problem.problem_id}`}>
          문제 풀기
        </Button>
      </div>
    </div>
  );
}
''',
            "components/Timer.tsx": '''
'use client';
import { useState, useEffect } from 'react';

export function Timer({ startTime }: { startTime: number }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [startTime]);

  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;

  return (
    <div className="fixed top-4 right-4 bg-white rounded-full px-4 py-2 shadow-lg">
      <span className="text-lg font-mono">
        {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
      </span>
    </div>
  );
}
''',
            "components/HintPanel.tsx": '''
'use client';
import { useState, useEffect } from 'react';
import { Button } from './ui/Button';

interface Hint {
  stage: number;
  hint_text: string;
  available_at: string;
}

export function HintPanel({ problemId }: { problemId: string }) {
  const [hints, setHints] = useState<Hint[]>([]);
  const [visibleHints, setVisibleHints] = useState<number[]>([]);
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);

  useEffect(() => {
    fetchHints();
  }, [problemId]);

  const fetchHints = async () => {
    const res = await fetch(`/api/hints/${problemId}`);
    const data = await res.json();
    setHints(data);
  };

  const showHint = (stage: number) => {
    setVisibleHints([...visibleHints, stage]);
  };

  return (
    <div className="mt-6 p-4 bg-gray-50 rounded-xl">
      <h3 className="text-lg font-semibold mb-4">힌트</h3>

      {hints.map((hint) => (
        <div key={hint.stage} className="mb-4">
          {visibleHints.includes(hint.stage) ? (
            <div className="p-4 bg-yellow-50 rounded-lg">
              <span className="text-sm text-yellow-600">힌트 {hint.stage}</span>
              <p className="mt-2">{hint.hint_text}</p>
            </div>
          ) : (
            <Button
              variant="outline"
              onClick={() => showHint(hint.stage)}
              disabled={hint.stage > 1 && !visibleHints.includes(hint.stage - 1)}
            >
              힌트 {hint.stage} 보기
            </Button>
          )}
        </div>
      ))}
    </div>
  );
}
''',
        }

        for path, code in components.items():
            self.codebase[path] = code

        return {"components": list(components.keys())}

    def develop_supabase_integration(self) -> Dict[str, Any]:
        """Supabase 연동 개발"""
        self.log("Supabase 연동 개발")

        code = '''
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseKey);

// 타입 정의
export interface Problem {
  id: string;
  problem_id: string;
  year: number;
  exam: string;
  question_no: number;
  subject: string;
  unit: string;
  score: number;
  answer: string;
  answer_verified: string;
  problem_image_url: string;
  status: string;
}

export interface User {
  id: string;
  email: string;
  nickname: string;
  grade: string;
  current_level: number;
  total_solved: number;
  correct_count: number;
}

export interface Delivery {
  id: string;
  user_id: string;
  problem_id: string;
  delivered_at: string;
  user_answer: string;
  is_correct: boolean;
  time_spent_seconds: number;
  status: string;
}

// 헬퍼 함수들
export async function getTodayProblem(userId: string): Promise<Problem | null> {
  // 적응형 문제 추천
  const { data, error } = await supabase
    .rpc('recommend_next_problem', { p_user_id: userId });

  if (error || !data || data.length === 0) return null;
  return data[0];
}

export async function getUserStats(userId: string) {
  const { data } = await supabase
    .from('user_learning_dashboard')
    .select('*')
    .eq('user_id', userId)
    .single();

  return data;
}

export async function submitAnswer(
  userId: string,
  problemId: string,
  answer: string,
  timeSpent: number
) {
  const { data, error } = await supabase
    .rpc('process_answer', {
      p_delivery_id: null, // 새 제출
      p_user_answer: answer,
      p_time_spent: timeSpent,
    });

  return { data, error };
}
'''
        self.codebase["lib/supabase.ts"] = code

        return {"code": code}

    def develop_auth_system(self) -> Dict[str, Any]:
        """인증 시스템 개발"""
        self.log("인증 시스템 개발")

        code = '''
// lib/auth.ts
import NextAuth from 'next-auth';
import KakaoProvider from 'next-auth/providers/kakao';
import { supabase } from './supabase';

export const {
  handlers: { GET, POST },
  auth,
  signIn,
  signOut,
} = NextAuth({
  providers: [
    KakaoProvider({
      clientId: process.env.KAKAO_CLIENT_ID!,
      clientSecret: process.env.KAKAO_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async signIn({ user, account, profile }) {
      // Supabase에 사용자 정보 저장/업데이트
      const { error } = await supabase
        .from('users')
        .upsert({
          kakao_id: profile?.id,
          email: user.email,
          nickname: profile?.properties?.nickname,
          kakao_access_token: account?.access_token,
          kakao_refresh_token: account?.refresh_token,
        }, {
          onConflict: 'kakao_id',
        });

      return !error;
    },
    async session({ session, token }) {
      // 세션에 사용자 ID 추가
      if (session.user) {
        const { data } = await supabase
          .from('users')
          .select('id')
          .eq('email', session.user.email)
          .single();

        session.user.id = data?.id;
      }
      return session;
    },
  },
});
'''
        self.codebase["lib/auth.ts"] = code

        auth_routes = '''
// app/api/auth/[...nextauth]/route.ts
import { GET, POST } from '@/lib/auth';
export { GET, POST };
'''
        self.codebase["app/api/auth/[...nextauth]/route.ts"] = auth_routes

        return {"files": ["lib/auth.ts", "app/api/auth/[...nextauth]/route.ts"]}

    def generate_project_structure(self) -> Dict[str, Any]:
        """프로젝트 구조 생성"""
        self.log("프로젝트 구조 생성")

        structure = {
            "directories": [
                "app",
                "app/api",
                "app/api/auth/[...nextauth]",
                "app/api/problems",
                "app/api/submit",
                "app/api/hints",
                "app/solve/[id]",
                "app/dashboard",
                "app/pricing",
                "components",
                "components/ui",
                "lib",
                "public",
                "public/assets",
                "styles",
            ],
            "config_files": {
                "package.json": {
                    "name": "kice-math-kakao",
                    "version": "1.0.0",
                    "scripts": {
                        "dev": "next dev",
                        "build": "next build",
                        "start": "next start",
                        "lint": "next lint",
                    },
                    "dependencies": {
                        "next": "14.x",
                        "react": "18.x",
                        "react-dom": "18.x",
                        "@supabase/supabase-js": "^2.x",
                        "next-auth": "^5.x",
                        "axios": "^1.x",
                        "tailwindcss": "^3.x",
                    },
                },
                "next.config.js": "module.exports = { images: { domains: ['*.supabase.co'] } }",
                ".env.local": """
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
KAKAO_CLIENT_ID=
KAKAO_CLIENT_SECRET=
NEXTAUTH_SECRET=
NEXTAUTH_URL=http://localhost:3000
""",
            },
        }

        return structure

    def process_task(self, task: Task) -> Any:
        """작업 처리"""
        self.log(f"작업 처리: {task.title}")
        task.status = TaskStatus.IN_PROGRESS

        title_lower = task.title.lower()

        try:
            if "카카오" in task.title or "kakao" in title_lower:
                result = self.develop_kakao_api_integration()
                task.update_status(TaskStatus.COMPLETED, result=result)
                return result

            if "next" in title_lower or "페이지" in task.title:
                result = self.develop_nextjs_pages()
                task.update_status(TaskStatus.COMPLETED, result=result)
                return result

            if "컴포넌트" in task.title or "component" in title_lower:
                result = self.develop_components()
                task.update_status(TaskStatus.COMPLETED, result=result)
                return result

            if "supabase" in title_lower or "db" in title_lower:
                result = self.develop_supabase_integration()
                task.update_status(TaskStatus.COMPLETED, result=result)
                return result

            if "인증" in task.title or "auth" in title_lower:
                result = self.develop_auth_system()
                task.update_status(TaskStatus.COMPLETED, result=result)
                return result

            if "프로젝트" in task.title or "구조" in task.title:
                result = self.generate_project_structure()
                task.update_status(TaskStatus.COMPLETED, result=result)
                return result

            # 기본 처리
            result = {"status": "processed", "task": task.title}
            task.update_status(TaskStatus.COMPLETED, result=result)
            return result

        except Exception as e:
            task.update_status(TaskStatus.FAILED, error=str(e))
            return {"error": str(e)}

    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """메시지 처리"""
        self.log(f"메시지 처리: {message.message_type}")

        if message.message_type == "code_request":
            file_path = message.content.get("file_path")
            code = self.codebase.get(file_path, "// File not found")
            return self.send_message(
                message.sender,
                "code_response",
                {"file_path": file_path, "code": code}
            )

        if message.message_type == "api_spec_request":
            api_name = message.content.get("api_name")
            spec = self.api_specs.get(api_name, {})
            return self.send_message(
                message.sender,
                "api_spec_response",
                {"api_name": api_name, "spec": spec}
            )

        return None

    def get_codebase(self) -> Dict[str, str]:
        """전체 코드베이스 조회"""
        return self.codebase
