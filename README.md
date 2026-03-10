# AI Co-Scientist for Engineering

공학 도메인(센서 · 광학 · 회로)에 특화된 AI 연구 보조 시스템입니다.
연구 목표를 입력하면 **설계 사양 + 실험 계획 + 시뮬레이션 방법 + 참고문헌**을 포함한 종합 연구 제안서를 자동으로 생성합니다.

---

## 주요 기능

- **아이디어 생성** — Ollama 로컬 LLM이 연구 목표에 맞는 3가지 공학적 접근 아이디어 생성
- **아이디어 평가** — 기술성숙도 · 실현가능성 · 독창성 · 제약조건충족 4개 항목 자동 채점
- **문헌 검색** — Google Scholar · OpenAlex · Semantic Scholar · Zotero 로컬 라이브러리 병합 검색
- **제안서 작성** — Claude가 설계 사양 · 실험 계획 · 시뮬레이션 방법을 마크다운으로 작성
- **Human Checkpoint** — 아이디어 선택 / 참고문헌 확인 / 최종 검토 3단계 사용자 개입

---

## 시스템 구조

```
main.py
  └── SupervisorAgent
        ├── GeneratorAgent  (Ollama 로컬 LLM)
        ├── CriticAgent     (Ollama 로컬 LLM)
        ├── LiteratureAgent (Google Scholar + OpenAlex + Semantic Scholar + Zotero)
        └── SynthesizerAgent (Claude API / CLI)
```

---

## 필요 사양

| 항목 | 최소 요구 사항 |
|------|--------------|
| OS | Windows 10/11 (macOS · Linux 가능) |
| Python | 3.11 이상 |
| RAM | 8GB 이상 (Ollama 모델에 따라 상이) |
| 디스크 | 모델 파일 포함 10GB 이상 권장 |

### 필수 소프트웨어

- **[Ollama](https://ollama.com/)** — 로컬 LLM 실행 엔진
- **[Claude Code CLI](https://docs.anthropic.com/claude-code)** — `claude` 명령어 (`claude auth login` 완료 필요)
  또는 **Anthropic API 키** (`.env`에 `ANTHROPIC_API_KEY` 설정 시 CLI 불필요)
- **[Zotero](https://www.zotero.org/)** *(선택)* — 로컬 논문 라이브러리 검색용

---

## 설치 방법

### 1. 저장소 clone

```bash
git clone --recurse-submodules https://github.com/yuni2326-oss/AI_coscientist.git
cd AI_coscientist
```

> `--recurse-submodules` 옵션이 없으면 `libs/zotero_scholar_to_local/`이 비어 있습니다.
> 이미 clone한 경우: `git submodule update --init`

### 2. 의존성 설치

```bash
python -m pip install -r requirements.txt
```

### 3. Ollama 모델 준비

```bash
# Ollama 서버 시작 (백그라운드)
ollama serve

# 모델 다운로드 (권장: qwen3.5:9b 또는 llama3.2)
ollama pull qwen3.5:9b
```

### 4. 환경 설정 (`.env` 파일 생성)

프로젝트 루트에 `.env` 파일을 생성합니다.

```env
# 사용할 Ollama 모델명
OLLAMA_MODEL=qwen3.5:9b

# Claude 호출 방식 선택 (둘 중 하나)
# 방법 A: Anthropic API 키 사용 (빠름, 유료)
ANTHROPIC_API_KEY=sk-ant-...

# 방법 B: Claude CLI 사용 (무료, claude auth login 필요)
# ANTHROPIC_API_KEY를 설정하지 않으면 자동으로 CLI 사용
CLAUDE_TIMEOUT=600
```

### 5. Claude CLI 인증 (방법 B 사용 시)

```bash
claude auth login
```

---

## 실행

```bash
python main.py
```

실행 예시:

```
연구 도메인: 광학 센서
연구 목표: 저조도 환경에서 신호 대 잡음비 개선
제약조건 (쉼표로 구분): 저전력, 소형화, 비용 50달러 이하
배경 정보: (Enter)
```

완료 시 `outputs/` 폴더에 마크다운 형식의 연구 제안서가 저장됩니다.

---

## 테스트

```bash
python -m pytest tests/ -v
```

16개 단위 테스트 포함. 외부 API 호출 없이 mock으로 실행됩니다.

---

## 프로젝트 구조

```
AI_coscientist/
├── main.py                    # 진입점
├── config.py                  # 설정 (pydantic-settings)
├── requirements.txt
├── .env                       # 환경 변수 (직접 생성)
├── agents/
│   ├── generator.py           # 아이디어 생성 (Ollama)
│   ├── critic.py              # 아이디어 평가 (Ollama)
│   ├── literature.py          # 참고문헌 검색 (멀티소스)
│   ├── synthesizer.py         # 제안서 작성 (Claude)
│   └── supervisor.py          # 전체 파이프라인 조율
├── core/
│   ├── ollama_runner.py       # Ollama 래퍼
│   ├── claude_runner.py       # Claude SDK/CLI 래퍼
│   └── checkpoint.py          # Human Checkpoint (rich UI)
├── models/
│   └── schemas.py             # Pydantic 데이터 모델
├── libs/
│   └── zotero_scholar_to_local/  # Zotero + 논문 검색 (submodule)
├── tests/                     # 단위 테스트
└── outputs/                   # 생성된 연구 제안서 저장
```

---

## 참고문헌 검색 소스

| 소스 | 방식 | 특징 |
|------|------|------|
| Zotero 로컬 | SQLite 직접 쿼리 | 내 라이브러리 우선 |
| Google Scholar | HTTP 스크래핑 | 인용수 기반 관련성 |
| OpenAlex | REST API | abstract · DOI 풍부 |
| Semantic Scholar | JSON API | AI/ML 논문 강세 |

---

## 다음 단계 (Phase 2)

- `agents/tournament.py` — Generator N회 병렬 실행
- `agents/debate.py` — 아이디어 간 교차 토론
- `agents/evolution.py` — 토론 기반 아이디어 진화
- Streamlit UI (`ui/app.py`)

---

## 라이선스

MIT
