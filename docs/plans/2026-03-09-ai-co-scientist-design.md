# AI Co-Scientist for Engineering — Design Document

**Date:** 2026-03-09
**Reference:** "Towards an AI Co-Scientist" (Google, 2025, arXiv:2502.18864)
**Status:** Approved

---

## 1. 프로젝트 개요

논문의 AI Co-Scientist 시스템에서 영감을 받아, 공학 분야(센서, 광학 시스템, 회로 설계)에 특화된 연구 제안서 자동 생성 시스템을 구축한다.

**핵심 출력물:** 설계 사양 + 실험 계획 + 시뮬레이션 방법 + 참고문헌을 포함한 종합 연구 제안서

---

## 2. 개발 전략: 2단계 접근

- **1단계 (MVP):** 역할 분리 Multi-agent + Human Checkpoint 파이프라인
- **2단계 (확장):** Tournament + Debate + Evolution 추가로 자율 가설 진화

---

## 3. 아키텍처 (1단계)

```
사용자 입력
  (연구 목표, 도메인, 제약조건)
        ↓
  [Supervisor Agent]  ← Claude Code CLI
  작업 분배 & 조율
        ↓
  ┌─────────────────────────────────┐
  │  [Generator Agent]   (Ollama)   │  아이디어 초안 3~5개 생성
  ├─────────────────────────────────┤
  │  [Critic Agent]      (Ollama)   │  기술성, 실현가능성, 독창성 점수화
  ├─────────────────────────────────┤
  │  [Literature Agent]  (Claude)   │  논문/특허 참조 & 근거 보강
  ├─────────────────────────────────┤
  │  [Synthesizer Agent] (Claude)   │  최종 연구 제안서 통합 작성
  └─────────────────────────────────┘
        ↓
  Human Checkpoint (3회)
        ↓
  최종 연구 제안서 (Markdown 저장)
```

### 모델 분배 전략

| 에이전트 | 모델 | 이유 |
|---------|------|------|
| Generator | Ollama (로컬) | 반복적 초안 생성, 비용 절감 |
| Critic | Ollama (로컬) | 반복 검토, 빠른 응답 |
| Literature | Claude Code CLI | 복잡한 추론 필요 |
| Synthesizer | Claude Code CLI | 고품질 최종 출력 |
| Supervisor | Claude Code CLI | 전체 조율 |

---

## 4. 데이터 흐름 & Human Checkpoint

```
1. 사용자 입력
   { domain, objective, constraints, background }

2. Generator → 아이디어 3~5개 초안

3. Critic → 각 아이디어 점수화
   [기술성숙도, 실현가능성, 제약조건 충족, 독창성] 1~5점

4. ★ Human Checkpoint #1
   → 아이디어 선택 / 피드백 / 조합 요청

5. Literature Agent → 관련 논문/특허 검색 및 근거 보강

6. ★ Human Checkpoint #2
   → 참고문헌 적절성 확인, 추가 자료 제공

7. Synthesizer → 최종 연구 제안서 생성

8. ★ Human Checkpoint #3
   → 최종 검토 & 수정 요청 → 승인 시 파일 저장
```

Human Checkpoint는 CLI 인터랙티브 프롬프트로 구현 (MVP), 이후 Streamlit UI로 업그레이드 가능.

---

## 5. 기술 스택

| 역할 | 도구 |
|------|------|
| Claude 연동 | `claude` CLI 서브프로세스 (`subprocess`) |
| 로컬 LLM | Ollama Python SDK (`ollama`) |
| 에이전트 오케스트레이션 | 직접 구현 (LangChain 없이) |
| 논문 검색 | `arxiv` Python 패키지 + `pypdf` |
| 터미널 UI | `rich` 라이브러리 |
| 설정 관리 | `pydantic-settings` + `.env` |
| 출력 저장 | Markdown 파일 |

---

## 6. 파일 구조

```
AI Co Sciencist/
├── main.py                  # 진입점, CLI 인터페이스
├── config.py                # 설정 (Ollama 모델명, 경로 등)
├── agents/
│   ├── supervisor.py        # 작업 분배 & 조율
│   ├── generator.py         # 아이디어 초안 생성 (Ollama)
│   ├── critic.py            # 타당성 검토 & 점수화 (Ollama)
│   ├── literature.py        # 논문/특허 참조 (Claude CLI)
│   └── synthesizer.py       # 최종 제안서 통합 (Claude CLI)
├── core/
│   ├── claude_runner.py     # Claude CLI 서브프로세스 래퍼
│   ├── ollama_runner.py     # Ollama SDK 래퍼
│   └── checkpoint.py        # Human Checkpoint 인터랙션
├── models/
│   └── schemas.py           # 입출력 데이터 구조 (Pydantic)
├── outputs/                 # 생성된 연구 제안서 저장
├── docs/
│   └── plans/
└── requirements.txt
```

---

## 7. 2단계 확장 계획 (Tournament)

**전환 시점:** 1단계가 안정적으로 유용한 제안서를 생성할 때

**추가 컴포넌트:**

```
[Tournament Manager]   Generator를 N번 병렬 실행
[Debate Agent]         아이디어 간 교차 토론 (Claude CLI)
[Evolution Agent]      상위 아이디어 선택 & 조합 후 다음 라운드
```

**확장 파일:**
```
agents/
├── tournament.py
├── debate.py
└── evolution.py
```

기존 1단계 코드를 수정하지 않고 `tournament.py`가 기존 에이전트를 감싸는 방식으로 확장.

---

## 8. 성공 기준 (1단계)

- 공학 연구 목표 입력 → 10분 이내 연구 제안서 초안 생성
- Human Checkpoint 3회로 사용자 의도 반영
- 출력물: Markdown 형식의 종합 연구 제안서
