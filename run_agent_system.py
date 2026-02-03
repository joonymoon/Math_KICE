#!/usr/bin/env python3
"""
KICE 수학 카카오톡 발송 서비스
5개 에이전트 시스템 실행 스크립트

사용법:
    python run_agent_system.py              # 데모 실행
    python run_agent_system.py --mode run   # 프로젝트 실행
    python run_agent_system.py --mode capabilities  # 에이전트 역량 조회
    python run_agent_system.py --mode task --agent designer --task-type 템플릿  # 단일 작업
"""

import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.run_agents import main

if __name__ == "__main__":
    main()
