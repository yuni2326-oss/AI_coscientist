# AI Co-Scientist for Engineering — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 공학 도메인(센서, 광학, 회로)에 특화된 AI Co-Scientist 시스템 구축 — 연구 목표 입력 시 설계 사양 + 실험 계획 + 시뮬레이션 방법 + 참고문헌을 포함한 종합 연구 제안서를 자동 생성한다.

**Architecture:** Supervisor가 4개의 역할 분리 에이전트(Generator, Critic, Literature, Synthesizer)를 조율하며, 각 단계마다 Human Checkpoint를 통해 사용자 피드백을 반영한다. Generator/Critic은 Ollama(로컬), Literature/Synthesizer/Supervisor는 Claude Code CLI 서브프로세스를 사용한다.

**Tech Stack:** Python 3.11+, Ollama Python SDK, subprocess(Claude CLI), arxiv, pypdf, pydantic-settings, rich

---

## 사전 준비

### 환경 확인 사항
- Ollama 설치 및 실행 중 (`ollama serve`)
- 로컬 모델 다운로드: `ollama pull llama3.2` 또는 `ollama pull qwen2.5:14b`
- Claude Code CLI 로그인 완료 (`claude` 명령어 실행 가능)
- Python 3.11+ 설치

---

### Task 1: 프로젝트 초기화 & 의존성 설치

**Files:**
- Create: `requirements.txt`
- Create: `config.py`
- Create: `models/schemas.py`
- Create: `models/__init__.py`

**Step 1: requirements.txt 작성**

```
ollama>=0.4.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
arxiv>=2.1.0
pypdf>=4.0.0
rich>=13.0.0
python-dotenv>=1.0.0
```

**Step 2: 의존성 설치**

```bash
pip install -r requirements.txt
```

Expected: 모든 패키지 설치 완료, 오류 없음

**Step 3: config.py 작성**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"
    claude_timeout: int = 120
    max_ideas: int = 5
    output_dir: str = "outputs"

    class Config:
        env_file = ".env"

settings = Settings()
```

**Step 4: models/schemas.py 작성**

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ResearchInput(BaseModel):
    domain: str          # 예: "광학 센서"
    objective: str       # 예: "저조도 환경 고감도 측정"
    constraints: list[str]  # 예: ["저전력", "소형화"]
    background: Optional[str] = None

class Idea(BaseModel):
    title: str
    description: str
    approach: str
    scores: dict[str, int] = {}  # 기술성숙도, 실현가능성, 독창성, 제약조건충족

class ResearchProposal(BaseModel):
    title: str
    input: ResearchInput
    selected_idea: Idea
    design_spec: str
    experiment_plan: str
    simulation_suggestion: str
    references: list[str]
    created_at: str = ""

    def __init__(self, **data):
        super().__init__(**data)
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
```

**Step 5: 테스트 — schemas import 확인**

```bash
python -c "from models.schemas import ResearchInput, Idea, ResearchProposal; print('OK')"
```

Expected: `OK` 출력

**Step 6: Commit**

```bash
git init
git add requirements.txt config.py models/
git commit -m "feat: project init with schemas and config"
```

---

### Task 2: core/ollama_runner.py — Ollama 래퍼

**Files:**
- Create: `core/__init__.py`
- Create: `core/ollama_runner.py`
- Create: `tests/test_ollama_runner.py`

**Step 1: 테스트 작성**

```python
# tests/test_ollama_runner.py
import pytest
from unittest.mock import patch, MagicMock
from core.ollama_runner import OllamaRunner

def test_generate_returns_string():
    runner = OllamaRunner()
    with patch("core.ollama_runner.ollama.chat") as mock_chat:
        mock_chat.return_value = {"message": {"content": "테스트 응답"}}
        result = runner.generate("테스트 프롬프트")
    assert isinstance(result, str)
    assert len(result) > 0

def test_generate_passes_prompt():
    runner = OllamaRunner()
    with patch("core.ollama_runner.ollama.chat") as mock_chat:
        mock_chat.return_value = {"message": {"content": "응답"}}
        runner.generate("내 프롬프트")
    call_args = mock_chat.call_args
    assert "내 프롬프트" in str(call_args)
```

**Step 2: 테스트 실패 확인**

```bash
pytest tests/test_ollama_runner.py -v
```

Expected: FAIL (ImportError — 파일 없음)

**Step 3: core/ollama_runner.py 구현**

```python
import ollama
from config import settings

class OllamaRunner:
    def __init__(self, model: str = None):
        self.model = model or settings.ollama_model

    def generate(self, prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = ollama.chat(
            model=self.model,
            messages=messages
        )
        return response["message"]["content"]
```

**Step 4: 테스트 통과 확인**

```bash
pytest tests/test_ollama_runner.py -v
```

Expected: PASSED (2 tests)

**Step 5: Commit**

```bash
git add core/ tests/test_ollama_runner.py
git commit -m "feat: add Ollama runner wrapper"
```

---

### Task 3: core/claude_runner.py — Claude CLI 래퍼

**Files:**
- Create: `core/claude_runner.py`
- Create: `tests/test_claude_runner.py`

**Step 1: 테스트 작성**

```python
# tests/test_claude_runner.py
import pytest
from unittest.mock import patch, MagicMock
from core.claude_runner import ClaudeRunner

def test_generate_returns_string():
    runner = ClaudeRunner()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout="Claude 응답 텍스트",
            returncode=0
        )
        result = runner.generate("테스트 프롬프트")
    assert isinstance(result, str)
    assert len(result) > 0

def test_generate_raises_on_error():
    runner = ClaudeRunner()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout="",
            returncode=1,
            stderr="error"
        )
        with pytest.raises(RuntimeError):
            runner.generate("프롬프트")
```

**Step 2: 테스트 실패 확인**

```bash
pytest tests/test_claude_runner.py -v
```

Expected: FAIL

**Step 3: core/claude_runner.py 구현**

```python
import subprocess
from config import settings

class ClaudeRunner:
    def generate(self, prompt: str) -> str:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=settings.claude_timeout,
            encoding="utf-8"
        )
        if result.returncode != 0:
            raise RuntimeError(f"Claude CLI error: {result.stderr}")
        return result.stdout.strip()
```

**Step 4: 테스트 통과 확인**

```bash
pytest tests/test_claude_runner.py -v
```

Expected: PASSED (2 tests)

**Step 5: Commit**

```bash
git add core/claude_runner.py tests/test_claude_runner.py
git commit -m "feat: add Claude CLI subprocess runner"
```

---

### Task 4: core/checkpoint.py — Human Checkpoint

**Files:**
- Create: `core/checkpoint.py`
- Create: `tests/test_checkpoint.py`

**Step 1: 테스트 작성**

```python
# tests/test_checkpoint.py
from unittest.mock import patch
from core.checkpoint import HumanCheckpoint

def test_ask_returns_user_input():
    cp = HumanCheckpoint()
    with patch("builtins.input", return_value="B를 선택"):
        result = cp.ask("어떤 아이디어를 선택하시겠습니까?")
    assert result == "B를 선택"

def test_confirm_yes():
    cp = HumanCheckpoint()
    with patch("builtins.input", return_value="y"):
        result = cp.confirm("계속하시겠습니까?")
    assert result is True

def test_confirm_no():
    cp = HumanCheckpoint()
    with patch("builtins.input", return_value="n"):
        result = cp.confirm("계속하시겠습니까?")
    assert result is False
```

**Step 2: 테스트 실패 확인**

```bash
pytest tests/test_checkpoint.py -v
```

Expected: FAIL

**Step 3: core/checkpoint.py 구현**

```python
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()

class HumanCheckpoint:
    def __init__(self, checkpoint_num: int = 0):
        self.checkpoint_num = checkpoint_num

    def display(self, title: str, content: str):
        console.print(Panel(content, title=f"[bold cyan]Checkpoint #{self.checkpoint_num}: {title}[/bold cyan]"))

    def ask(self, question: str) -> str:
        return Prompt.ask(f"\n[yellow]{question}[/yellow]")

    def confirm(self, question: str) -> bool:
        return Confirm.ask(f"\n[yellow]{question}[/yellow]")
```

**Step 4: 테스트 통과 확인**

```bash
pytest tests/test_checkpoint.py -v
```

Expected: PASSED (3 tests)

**Step 5: Commit**

```bash
git add core/checkpoint.py tests/test_checkpoint.py
git commit -m "feat: add human checkpoint interaction"
```

---

### Task 5: agents/generator.py — 아이디어 생성 에이전트

**Files:**
- Create: `agents/__init__.py`
- Create: `agents/generator.py`
- Create: `tests/test_generator.py`

**Step 1: 테스트 작성**

```python
# tests/test_generator.py
from unittest.mock import MagicMock, patch
from agents.generator import GeneratorAgent
from models.schemas import ResearchInput, Idea

def make_input():
    return ResearchInput(
        domain="광학 센서",
        objective="저조도 환경 고감도 측정",
        constraints=["저전력", "소형화"]
    )

def test_generate_returns_ideas():
    agent = GeneratorAgent()
    agent.runner = MagicMock()
    agent.runner.generate.return_value = """
    아이디어 1: APD 기반 설계
    설명: 아발란체 포토다이오드를 활용한 고감도 수광부
    접근법: APD 바이어스 회로 최적화로 증폭률 향상
    ---
    아이디어 2: SPAD 어레이
    설명: 단일 광자 검출 어레이 구성
    접근법: 시간 상관 광자 계수법 적용
    """
    ideas = agent.generate(make_input())
    assert isinstance(ideas, list)
    assert len(ideas) >= 1
    assert isinstance(ideas[0], Idea)
```

**Step 2: 테스트 실패 확인**

```bash
pytest tests/test_generator.py -v
```

Expected: FAIL

**Step 3: agents/generator.py 구현**

```python
from core.ollama_runner import OllamaRunner
from models.schemas import ResearchInput, Idea
import re

SYSTEM_PROMPT = """당신은 공학 연구 아이디어 생성 전문가입니다.
센서, 광학 시스템, 회로 설계 분야에 깊은 지식을 가지고 있습니다.
주어진 연구 목표와 제약조건에 맞는 창의적이고 실현 가능한 아이디어를 생성하세요."""

class GeneratorAgent:
    def __init__(self):
        self.runner = OllamaRunner()

    def generate(self, research_input: ResearchInput) -> list[Idea]:
        prompt = f"""
다음 연구 목표에 대해 {3}가지 서로 다른 공학적 접근 아이디어를 생성하세요.

도메인: {research_input.domain}
목표: {research_input.objective}
제약조건: {', '.join(research_input.constraints)}
배경정보: {research_input.background or '없음'}

각 아이디어를 다음 형식으로 작성하세요:
아이디어 N: [제목]
설명: [구체적인 설명]
접근법: [기술적 접근 방법]
---
"""
        raw = self.runner.generate(prompt, system=SYSTEM_PROMPT)
        return self._parse_ideas(raw)

    def _parse_ideas(self, raw: str) -> list[Idea]:
        ideas = []
        blocks = raw.split("---")
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            title_match = re.search(r"아이디어\s*\d+[:\.]?\s*(.+)", block)
            desc_match = re.search(r"설명[:\s]+(.+?)(?=접근법|$)", block, re.DOTALL)
            approach_match = re.search(r"접근법[:\s]+(.+?)$", block, re.DOTALL)
            if title_match:
                ideas.append(Idea(
                    title=title_match.group(1).strip(),
                    description=desc_match.group(1).strip() if desc_match else "",
                    approach=approach_match.group(1).strip() if approach_match else ""
                ))
        return ideas if ideas else [Idea(title="생성된 아이디어", description=raw[:200], approach="")]
```

**Step 4: 테스트 통과 확인**

```bash
pytest tests/test_generator.py -v
```

Expected: PASSED

**Step 5: Commit**

```bash
git add agents/ tests/test_generator.py
git commit -m "feat: add Generator agent with Ollama"
```

---

### Task 6: agents/critic.py — 검토 에이전트

**Files:**
- Create: `agents/critic.py`
- Create: `tests/test_critic.py`

**Step 1: 테스트 작성**

```python
# tests/test_critic.py
from unittest.mock import MagicMock
from agents.critic import CriticAgent
from models.schemas import Idea, ResearchInput

def test_critic_adds_scores():
    agent = CriticAgent()
    agent.runner = MagicMock()
    agent.runner.generate.return_value = """
    기술성숙도: 4
    실현가능성: 3
    독창성: 5
    제약조건충족: 4
    """
    idea = Idea(title="테스트", description="설명", approach="접근")
    research_input = ResearchInput(
        domain="센서", objective="목표", constraints=["저전력"]
    )
    scored = agent.score(idea, research_input)
    assert "기술성숙도" in scored.scores
    assert 1 <= scored.scores["기술성숙도"] <= 5
```

**Step 2: 테스트 실패 확인**

```bash
pytest tests/test_critic.py -v
```

Expected: FAIL

**Step 3: agents/critic.py 구현**

```python
from core.ollama_runner import OllamaRunner
from models.schemas import Idea, ResearchInput
import re

SCORE_KEYS = ["기술성숙도", "실현가능성", "독창성", "제약조건충족"]

class CriticAgent:
    def __init__(self):
        self.runner = OllamaRunner()

    def score(self, idea: Idea, research_input: ResearchInput) -> Idea:
        prompt = f"""
다음 공학 연구 아이디어를 평가하세요 (각 항목 1~5점):

아이디어: {idea.title}
설명: {idea.description}
접근법: {idea.approach}
제약조건: {', '.join(research_input.constraints)}

각 항목을 다음 형식으로 점수만 작성하세요:
기술성숙도: [1-5]
실현가능성: [1-5]
독창성: [1-5]
제약조건충족: [1-5]
"""
        raw = self.runner.generate(prompt)
        idea.scores = self._parse_scores(raw)
        return idea

    def score_all(self, ideas: list[Idea], research_input: ResearchInput) -> list[Idea]:
        return [self.score(idea, research_input) for idea in ideas]

    def _parse_scores(self, raw: str) -> dict[str, int]:
        scores = {}
        for key in SCORE_KEYS:
            match = re.search(rf"{key}[:\s]+([1-5])", raw)
            scores[key] = int(match.group(1)) if match else 3
        return scores
```

**Step 4: 테스트 통과 확인**

```bash
pytest tests/test_critic.py -v
```

Expected: PASSED

**Step 5: Commit**

```bash
git add agents/critic.py tests/test_critic.py
git commit -m "feat: add Critic agent with scoring"
```

---

### Task 7: agents/literature.py — 문헌 검색 에이전트

**Files:**
- Create: `agents/literature.py`
- Create: `tests/test_literature.py`

**Step 1: 테스트 작성**

```python
# tests/test_literature.py
from unittest.mock import MagicMock, patch
from agents.literature import LiteratureAgent
from models.schemas import Idea, ResearchInput

def test_search_returns_references():
    agent = LiteratureAgent()
    agent.claude = MagicMock()
    agent.claude.generate.return_value = "1. Smith et al. (2023) - APD sensor design\n2. Kim et al. (2024)"

    with patch("agents.literature.arxiv.Search") as mock_search:
        mock_search.return_value.results.return_value = iter([])
        idea = Idea(title="APD 센서", description="설명", approach="접근")
        research_input = ResearchInput(
            domain="광학", objective="고감도", constraints=[]
        )
        refs = agent.find_references(idea, research_input)
    assert isinstance(refs, list)
    assert len(refs) > 0
```

**Step 2: 테스트 실패 확인**

```bash
pytest tests/test_literature.py -v
```

Expected: FAIL

**Step 3: agents/literature.py 구현**

```python
import arxiv
from core.claude_runner import ClaudeRunner
from models.schemas import Idea, ResearchInput

class LiteratureAgent:
    def __init__(self):
        self.claude = ClaudeRunner()

    def find_references(self, idea: Idea, research_input: ResearchInput) -> list[str]:
        arxiv_refs = self._search_arxiv(idea, research_input)
        claude_refs = self._ask_claude(idea, research_input, arxiv_refs)
        return claude_refs

    def _search_arxiv(self, idea: Idea, research_input: ResearchInput) -> list[str]:
        query = f"{research_input.domain} {idea.title} {research_input.objective}"
        search = arxiv.Search(query=query, max_results=5)
        refs = []
        try:
            for result in search.results():
                refs.append(f"{result.title} ({result.published.year}) - {result.entry_id}")
        except Exception:
            pass
        return refs

    def _ask_claude(self, idea: Idea, research_input: ResearchInput, arxiv_refs: list[str]) -> list[str]:
        prompt = f"""
다음 공학 연구 아이디어에 관련된 핵심 참고문헌을 제시하세요.

아이디어: {idea.title}
도메인: {research_input.domain}
목표: {research_input.objective}

arxiv 검색 결과:
{chr(10).join(arxiv_refs) if arxiv_refs else '없음'}

실제 존재할 가능성이 높은 논문/특허를 포함하여 핵심 참고문헌 5개를 번호 목록으로 작성하세요.
형식: N. [저자] ([연도]) - [제목]
"""
        raw = self.claude.generate(prompt)
        lines = [line.strip() for line in raw.split("\n") if line.strip() and line[0].isdigit()]
        return lines if lines else [raw[:300]]
```

**Step 4: 테스트 통과 확인**

```bash
pytest tests/test_literature.py -v
```

Expected: PASSED

**Step 5: Commit**

```bash
git add agents/literature.py tests/test_literature.py
git commit -m "feat: add Literature agent with arxiv + Claude"
```

---

### Task 8: agents/synthesizer.py — 최종 제안서 통합 에이전트

**Files:**
- Create: `agents/synthesizer.py`
- Create: `tests/test_synthesizer.py`

**Step 1: 테스트 작성**

```python
# tests/test_synthesizer.py
from unittest.mock import MagicMock
from agents.synthesizer import SynthesizerAgent
from models.schemas import Idea, ResearchInput, ResearchProposal

def test_synthesize_returns_proposal():
    agent = SynthesizerAgent()
    agent.claude = MagicMock()
    agent.claude.generate.side_effect = [
        "## 설계 사양\nAPD 기반 고감도 수광부 설계...",
        "## 실험 계획\n1단계: 기초 특성 측정...",
        "## 시뮬레이션\nLTspice로 APD 바이어스 회로 시뮬레이션..."
    ]
    idea = Idea(title="APD 센서", description="설명", approach="접근")
    research_input = ResearchInput(
        domain="광학", objective="고감도", constraints=["저전력"]
    )
    refs = ["1. Smith (2023) - APD design"]
    proposal = agent.synthesize(research_input, idea, refs)
    assert isinstance(proposal, ResearchProposal)
    assert len(proposal.design_spec) > 0
```

**Step 2: 테스트 실패 확인**

```bash
pytest tests/test_synthesizer.py -v
```

Expected: FAIL

**Step 3: agents/synthesizer.py 구현**

```python
from core.claude_runner import ClaudeRunner
from models.schemas import Idea, ResearchInput, ResearchProposal

class SynthesizerAgent:
    def __init__(self):
        self.claude = ClaudeRunner()

    def synthesize(self, research_input: ResearchInput, idea: Idea, references: list[str]) -> ResearchProposal:
        design_spec = self._generate_design_spec(research_input, idea)
        experiment_plan = self._generate_experiment_plan(research_input, idea)
        simulation = self._generate_simulation(research_input, idea)

        return ResearchProposal(
            title=f"{research_input.domain} - {idea.title}",
            input=research_input,
            selected_idea=idea,
            design_spec=design_spec,
            experiment_plan=experiment_plan,
            simulation_suggestion=simulation,
            references=references
        )

    def _generate_design_spec(self, ri: ResearchInput, idea: Idea) -> str:
        return self.claude.generate(f"""
공학 설계 사양서를 작성하세요.

도메인: {ri.domain}
목표: {ri.objective}
제약조건: {', '.join(ri.constraints)}
선택된 접근법: {idea.title} - {idea.approach}

다음을 포함한 상세 설계 사양서 (마크다운):
- 핵심 부품/재료 사양
- 성능 목표 수치
- 구조/회로 설명
- 예상 도전 과제
""")

    def _generate_experiment_plan(self, ri: ResearchInput, idea: Idea) -> str:
        return self.claude.generate(f"""
실험 계획서를 작성하세요.

아이디어: {idea.title}
목표: {ri.objective}

다음을 포함한 단계별 실험 계획 (마크다운):
- 1단계: 기초 특성 검증
- 2단계: 성능 최적화 실험
- 3단계: 환경 내성 테스트
- 측정 장비 및 방법
""")

    def _generate_simulation(self, ri: ResearchInput, idea: Idea) -> str:
        return self.claude.generate(f"""
시뮬레이션 방법을 제안하세요.

도메인: {ri.domain}
아이디어: {idea.title} - {idea.approach}

다음을 포함:
- 추천 시뮬레이션 도구 (SPICE, FDTD, FEM, Python 등)
- 핵심 시뮬레이션 파라미터
- 예시 Python 코드 스니펫 (있으면)
""")
```

**Step 4: 테스트 통과 확인**

```bash
pytest tests/test_synthesizer.py -v
```

Expected: PASSED

**Step 5: Commit**

```bash
git add agents/synthesizer.py tests/test_synthesizer.py
git commit -m "feat: add Synthesizer agent for final proposal"
```

---

### Task 9: agents/supervisor.py — 전체 파이프라인 조율

**Files:**
- Create: `agents/supervisor.py`
- Create: `tests/test_supervisor.py`

**Step 1: 테스트 작성**

```python
# tests/test_supervisor.py
from unittest.mock import MagicMock, patch
from agents.supervisor import SupervisorAgent
from models.schemas import ResearchInput, Idea, ResearchProposal

def make_idea(title="테스트"):
    return Idea(title=title, description="설명", approach="접근",
                scores={"기술성숙도": 4, "실현가능성": 4, "독창성": 3, "제약조건충족": 5})

def test_supervisor_returns_proposal():
    agent = SupervisorAgent()
    agent.generator = MagicMock()
    agent.critic = MagicMock()
    agent.literature = MagicMock()
    agent.synthesizer = MagicMock()
    agent.checkpoint = MagicMock()

    agent.generator.generate.return_value = [make_idea("A"), make_idea("B")]
    agent.critic.score_all.return_value = [make_idea("A"), make_idea("B")]
    agent.checkpoint.ask.return_value = "A를 선택"
    agent.checkpoint.confirm.return_value = True
    agent.literature.find_references.return_value = ["ref1", "ref2"]
    agent.synthesizer.synthesize.return_value = MagicMock(spec=ResearchProposal)

    ri = ResearchInput(domain="센서", objective="목표", constraints=[])
    result = agent.run(ri)
    assert result is not None
```

**Step 2: 테스트 실패 확인**

```bash
pytest tests/test_supervisor.py -v
```

Expected: FAIL

**Step 3: agents/supervisor.py 구현**

```python
from rich.console import Console
from rich.table import Table
from agents.generator import GeneratorAgent
from agents.critic import CriticAgent
from agents.literature import LiteratureAgent
from agents.synthesizer import SynthesizerAgent
from core.checkpoint import HumanCheckpoint
from models.schemas import ResearchInput, Idea, ResearchProposal

console = Console()

class SupervisorAgent:
    def __init__(self):
        self.generator = GeneratorAgent()
        self.critic = CriticAgent()
        self.literature = LiteratureAgent()
        self.synthesizer = SynthesizerAgent()
        self.checkpoint = HumanCheckpoint()

    def run(self, research_input: ResearchInput) -> ResearchProposal:
        console.print("\n[bold green]1. 아이디어 생성 중...[/bold green]")
        ideas = self.generator.generate(research_input)

        console.print("[bold green]2. 아이디어 평가 중...[/bold green]")
        ideas = self.critic.score_all(ideas, research_input)

        self._display_ideas(ideas)

        # Checkpoint #1
        self.checkpoint.checkpoint_num = 1
        self.checkpoint.display("아이디어 선택", "위 아이디어들을 검토하세요.")
        feedback = self.checkpoint.ask("어떤 아이디어를 선택/수정하시겠습니까? (제목 또는 피드백 입력)")
        selected = self._select_idea(ideas, feedback)

        console.print("\n[bold green]3. 문헌 검색 중...[/bold green]")
        references = self.literature.find_references(selected, research_input)

        # Checkpoint #2
        self.checkpoint.checkpoint_num = 2
        self.checkpoint.display("참고문헌 확인", "\n".join(references))
        if not self.checkpoint.confirm("이 참고문헌으로 계속하시겠습니까?"):
            extra = self.checkpoint.ask("추가할 참고문헌이 있으면 입력하세요 (없으면 Enter)")
            if extra:
                references.append(extra)

        console.print("\n[bold green]4. 최종 제안서 작성 중...[/bold green]")
        proposal = self.synthesizer.synthesize(research_input, selected, references)

        # Checkpoint #3
        self.checkpoint.checkpoint_num = 3
        self.checkpoint.display("최종 검토", proposal.design_spec[:300] + "...")
        self.checkpoint.confirm("제안서 생성을 완료하시겠습니까?")

        return proposal

    def _display_ideas(self, ideas: list[Idea]):
        table = Table(title="생성된 아이디어")
        table.add_column("번호", style="cyan")
        table.add_column("제목", style="white")
        table.add_column("기술성숙도", justify="center")
        table.add_column("실현가능성", justify="center")
        table.add_column("독창성", justify="center")
        for i, idea in enumerate(ideas, 1):
            table.add_row(
                str(i), idea.title,
                str(idea.scores.get("기술성숙도", "-")),
                str(idea.scores.get("실현가능성", "-")),
                str(idea.scores.get("독창성", "-"))
            )
        console.print(table)

    def _select_idea(self, ideas: list[Idea], feedback: str) -> Idea:
        for idea in ideas:
            if idea.title in feedback:
                return idea
        for i, idea in enumerate(ideas, 1):
            if str(i) in feedback:
                return idea
        # 점수 합계 기준 최고 아이디어 반환
        return max(ideas, key=lambda x: sum(x.scores.values()), default=ideas[0])
```

**Step 4: 테스트 통과 확인**

```bash
pytest tests/test_supervisor.py -v
```

Expected: PASSED

**Step 5: Commit**

```bash
git add agents/supervisor.py tests/test_supervisor.py
git commit -m "feat: add Supervisor agent orchestrating full pipeline"
```

---

### Task 10: main.py — 진입점 & 출력 저장

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

**Step 1: 테스트 작성**

```python
# tests/test_main.py
from unittest.mock import MagicMock, patch
from main import save_proposal, collect_input
from models.schemas import ResearchInput, ResearchProposal, Idea

def test_save_proposal_creates_file(tmp_path):
    idea = Idea(title="테스트", description="설명", approach="접근")
    ri = ResearchInput(domain="센서", objective="목표", constraints=["저전력"])
    proposal = ResearchProposal(
        title="테스트 제안서",
        input=ri,
        selected_idea=idea,
        design_spec="## 설계\n내용",
        experiment_plan="## 실험\n내용",
        simulation_suggestion="## 시뮬레이션\n내용",
        references=["ref1"]
    )
    output_file = save_proposal(proposal, output_dir=str(tmp_path))
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert "테스트 제안서" in content
```

**Step 2: 테스트 실패 확인**

```bash
pytest tests/test_main.py -v
```

Expected: FAIL

**Step 3: main.py 구현**

```python
import os
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt
from models.schemas import ResearchInput, ResearchProposal
from agents.supervisor import SupervisorAgent
from config import settings

console = Console()

def collect_input() -> ResearchInput:
    console.print("\n[bold cyan]=== AI Co-Scientist for Engineering ===[/bold cyan]\n")
    domain = Prompt.ask("[white]연구 도메인[/white]", default="광학 센서")
    objective = Prompt.ask("[white]연구 목표[/white]")
    constraints_raw = Prompt.ask("[white]제약조건 (쉼표로 구분)[/white]", default="저전력, 소형화")
    constraints = [c.strip() for c in constraints_raw.split(",")]
    background = Prompt.ask("[white]배경 정보 (없으면 Enter)[/white]", default="")
    return ResearchInput(
        domain=domain,
        objective=objective,
        constraints=constraints,
        background=background or None
    )

def save_proposal(proposal: ResearchProposal, output_dir: str = None) -> Path:
    output_dir = Path(output_dir or settings.output_dir)
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{proposal.input.domain.replace(' ', '_')}.md"
    filepath = output_dir / filename

    content = f"""# {proposal.title}

**생성일시:** {proposal.created_at}
**도메인:** {proposal.input.domain}
**목표:** {proposal.input.objective}
**제약조건:** {', '.join(proposal.input.constraints)}

---

## 선택된 접근법

**{proposal.selected_idea.title}**

{proposal.selected_idea.description}

접근법: {proposal.selected_idea.approach}

---

## 설계 사양

{proposal.design_spec}

---

## 실험 계획

{proposal.experiment_plan}

---

## 시뮬레이션 방법

{proposal.simulation_suggestion}

---

## 참고문헌

{chr(10).join(proposal.references)}
"""
    filepath.write_text(content, encoding="utf-8")
    return filepath

def main():
    research_input = collect_input()
    supervisor = SupervisorAgent()
    proposal = supervisor.run(research_input)
    output_file = save_proposal(proposal)
    console.print(f"\n[bold green]제안서 저장 완료: {output_file}[/bold green]")

if __name__ == "__main__":
    main()
```

**Step 4: 테스트 통과 확인**

```bash
pytest tests/test_main.py -v
```

Expected: PASSED

**Step 5: 전체 테스트 실행**

```bash
pytest tests/ -v
```

Expected: 모든 테스트 PASSED

**Step 6: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add main entry point and proposal file saving"
```

---

### Task 11: 통합 테스트 (실제 실행)

**사전 확인:**
- `ollama serve` 실행 중
- `ollama list`로 모델 확인
- `claude --version`으로 CLI 확인

**Step 1: 실제 실행 테스트**

```bash
python main.py
```

입력 예시:
```
연구 도메인: 광학 센서
연구 목표: 저조도 환경에서 신호 대 잡음비 개선
제약조건: 저전력, 소형화, 비용 50달러 이하
배경 정보: (Enter)
```

Expected: 제안서 파일이 `outputs/` 폴더에 생성됨

**Step 2: 출력 확인**

```bash
ls outputs/
cat outputs/*.md
```

**Step 3: Final commit**

```bash
git add .
git commit -m "feat: complete Phase 1 AI Co-Scientist MVP"
```

---

## 다음 단계 (Phase 2 힌트)

Phase 1이 안정적으로 동작하면:

1. `agents/tournament.py` - Generator를 N번 병렬 실행
2. `agents/debate.py` - 아이디어 간 교차 토론 (Claude CLI)
3. `agents/evolution.py` - 토론 결과 기반 아이디어 진화
4. Streamlit UI 추가 (`ui/app.py`)
