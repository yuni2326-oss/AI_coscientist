# Multi-Idea Selection & Literature Limit 20 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 문헌 검색 결과를 20개로 늘리고, 아이디어를 복수 선택해 각각 독립적인 제안서를 생성한다.

**Architecture:** `supervisor.run()`이 `list[ResearchProposal]`을 반환하도록 변경. 각 선택된 아이디어에 대해 문헌검색 → Checkpoint #2 → 합성을 순차 반복. `main.py`는 반환된 리스트를 루프로 저장.

**Tech Stack:** Python 3.12, pydantic, rich, pytest

---

### Task 1: literature.py — 검색 한도 20개로 변경

**Files:**
- Modify: `agents/literature.py`
- Test: `tests/test_literature.py`

**Step 1: 기존 테스트 실행 (현재 상태 확인)**

```bash
python -m pytest tests/test_literature.py -v
```
Expected: 기존 테스트 통과 확인

**Step 2: limit 기본값 및 관련 상수 변경**

`agents/literature.py` 에서 아래 3곳을 수정:

1. `find_references` 시그니처 (line 23):
```python
def find_references(self, idea: Idea, research_input: ResearchInput, limit: int = 20, years_back: int = 7) -> list[str]:
```

2. `_ask_claude` 내 슬라이싱 (line 151):
```python
paper_list = "\n".join(fmt(p) for p in papers[:20]) if papers else "검색 결과 없음"
```

3. `_ask_claude` 내 프롬프트 (line 162):
```
가장 관련성 높은 참고문헌 20개를 번호 목록으로 정리하세요.
```

**Step 3: 테스트 통과 확인**

```bash
python -m pytest tests/test_literature.py -v
```
Expected: PASS

**Step 4: Commit**

```bash
git add agents/literature.py
git commit -m "feat: increase literature search limit from 10 to 20"
```

---

### Task 2: supervisor.py — 다중 아이디어 선택 및 루프 처리

**Files:**
- Modify: `agents/supervisor.py`
- Test: `tests/test_supervisor.py`

**Step 1: 실패할 테스트 작성**

`tests/test_supervisor.py`에 아래 테스트 추가:

```python
def test_supervisor_returns_list_of_proposals():
    agent = SupervisorAgent()
    agent.generator = MagicMock()
    agent.critic = MagicMock()
    agent.literature = MagicMock()
    agent.synthesizer = MagicMock()
    agent.checkpoint = MagicMock()

    agent.generator.generate.return_value = [make_idea("A"), make_idea("B"), make_idea("C")]
    agent.critic.score_all.return_value = [make_idea("A"), make_idea("B"), make_idea("C")]
    agent.checkpoint.ask.return_value = "1,2"  # 두 아이디어 선택
    agent.checkpoint.confirm.return_value = True
    agent.literature.find_references.return_value = ["ref1", "ref2"]
    mock_proposal = MagicMock()
    mock_proposal.design_spec = "## 설계 사양\n내용..."
    agent.synthesizer.synthesize.return_value = mock_proposal

    ri = ResearchInput(domain="센서", objective="목표", constraints=[])
    result = agent.run(ri)
    assert isinstance(result, list)
    assert len(result) == 2
    assert agent.literature.find_references.call_count == 2
    assert agent.synthesizer.synthesize.call_count == 2


def test_supervisor_select_ideas_by_comma():
    agent = SupervisorAgent()
    ideas = [make_idea("A"), make_idea("B"), make_idea("C")]
    selected = agent._select_ideas(ideas, "1,3")
    assert len(selected) == 2
    assert selected[0].title == "A"
    assert selected[1].title == "C"


def test_supervisor_select_ideas_by_space():
    agent = SupervisorAgent()
    ideas = [make_idea("A"), make_idea("B"), make_idea("C")]
    selected = agent._select_ideas(ideas, "1 2")
    assert len(selected) == 2
    assert selected[0].title == "A"
    assert selected[1].title == "B"


def test_supervisor_select_ideas_fallback_to_best():
    agent = SupervisorAgent()
    ideas = [make_idea("A"), make_idea("B")]
    # 매칭 안 되는 입력 → 최고점 1개 반환
    selected = agent._select_ideas(ideas, "없는아이디어")
    assert len(selected) == 1
```

**Step 2: 테스트 실패 확인**

```bash
python -m pytest tests/test_supervisor.py::test_supervisor_returns_list_of_proposals -v
python -m pytest tests/test_supervisor.py::test_supervisor_select_ideas_by_comma -v
```
Expected: FAIL (`_select_ideas` not found, `run()` returns single proposal)

**Step 3: supervisor.py 구현**

`agents/supervisor.py` 전체를 아래와 같이 수정:

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

    def run(self, research_input: ResearchInput) -> list[ResearchProposal]:
        console.print("\n[bold green]1. 아이디어 생성 중...[/bold green]")
        ideas = self.generator.generate(research_input)

        console.print("[bold green]2. 아이디어 평가 중...[/bold green]")
        ideas = self.critic.score_all(ideas, research_input)

        self._display_ideas(ideas)

        # Checkpoint #1 — 복수 선택
        self.checkpoint.checkpoint_num = 1
        self.checkpoint.display("아이디어 선택", "위 아이디어들을 검토하세요.")
        feedback = self.checkpoint.ask(
            "어떤 아이디어를 선택하시겠습니까? (번호를 쉼표/공백으로 구분, 예: 1,3 또는 1 2)"
        )
        selected_ideas = self._select_ideas(ideas, feedback)

        proposals = []
        for i, selected in enumerate(selected_ideas, 1):
            console.print(f"\n[bold green]3-{i}. [{selected.title}] 문헌 검색 중...[/bold green]")
            references = self.literature.find_references(selected, research_input)

            # Checkpoint #2 — 아이디어별
            self.checkpoint.checkpoint_num = 2
            self.checkpoint.display(
                f"참고문헌 확인 [{selected.title}]", "\n".join(references)
            )
            if not self.checkpoint.confirm("이 참고문헌으로 계속하시겠습니까?"):
                extra = self.checkpoint.ask("추가할 참고문헌이 있으면 입력하세요 (없으면 Enter)")
                if extra:
                    references.append(extra)

            console.print(f"[bold green]4-{i}. [{selected.title}] 제안서 작성 중...[/bold green]")
            proposal = self.synthesizer.synthesize(research_input, selected, references)
            proposals.append(proposal)

        # Checkpoint #3 — 전체 완료 후 한 번
        self.checkpoint.checkpoint_num = 3
        summary = "\n\n".join(
            f"[{p.selected_idea.title}]\n{p.design_spec[:200]}..." for p in proposals
        )
        self.checkpoint.display("최종 검토", summary)
        self.checkpoint.confirm("제안서 생성을 완료하시겠습니까?")

        return proposals

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

    def _select_ideas(self, ideas: list[Idea], feedback: str) -> list[Idea]:
        import re
        # 번호 파싱 (쉼표 또는 공백 구분)
        nums = [int(n) for n in re.findall(r'\d+', feedback) if 1 <= int(n) <= len(ideas)]
        if nums:
            # 중복 제거, 순서 유지
            seen = set()
            result = []
            for n in nums:
                if n not in seen:
                    seen.add(n)
                    result.append(ideas[n - 1])
            return result
        # 제목 매칭
        matched = [idea for idea in ideas if idea.title in feedback]
        if matched:
            return matched
        # fallback: 최고점 1개
        return [max(ideas, key=lambda x: sum(x.scores.values()), default=ideas[0])]
```

**Step 4: 테스트 통과 확인**

```bash
python -m pytest tests/test_supervisor.py -v
```
Expected: 전체 PASS (기존 `test_supervisor_returns_proposal` 포함)

**Step 5: Commit**

```bash
git add agents/supervisor.py tests/test_supervisor.py
git commit -m "feat: support multiple idea selection, supervisor returns list[ResearchProposal]"
```

---

### Task 3: main.py — 복수 제안서 저장

**Files:**
- Modify: `main.py`
- Test: `tests/test_main.py`

**Step 1: 기존 테스트 실행 확인**

```bash
python -m pytest tests/test_main.py -v
```
Expected: PASS (save_proposal 자체는 변경 없음)

**Step 2: main() 함수 수정**

`main.py`의 `main()` 함수를 아래로 교체:

```python
def main():
    research_input = collect_input()
    supervisor = SupervisorAgent()
    proposals = supervisor.run(research_input)
    console.print(f"\n[bold green]제안서 {len(proposals)}개 저장 완료![/bold green]")
    for proposal in proposals:
        md_path, docx_path = save_proposal(proposal)
        console.print(f"\n  [cyan]{proposal.selected_idea.title}[/cyan]")
        console.print(f"    Markdown : {md_path}")
        console.print(f"    Word     : {docx_path}")
```

**Step 3: test_main.py에 복수 제안서 저장 테스트 추가**

```python
def test_main_saves_multiple_proposals(tmp_path):
    proposals = [_make_proposal(), _make_proposal()]
    paths = []
    for p in proposals:
        md_path, docx_path = save_proposal(p, output_dir=str(tmp_path))
        paths.append(md_path)
    assert len(paths) == 2
    for p in paths:
        assert p.exists()
```

**Step 4: 테스트 통과 확인**

```bash
python -m pytest tests/test_main.py -v
```
Expected: PASS

**Step 5: 전체 테스트 통과 확인**

```bash
python -m pytest -v
```
Expected: 전체 PASS

**Step 6: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: save multiple proposals in main loop"
```

---

### Task 4: 기존 test_supervisor 호환성 확인 및 정리

**Files:**
- Modify: `tests/test_supervisor.py`

**Step 1: 기존 `test_supervisor_returns_proposal` 수정**

Task 2에서 `run()`이 `list`를 반환하므로 기존 테스트도 업데이트:

```python
def test_supervisor_returns_proposal():
    # ... (기존 setup 동일) ...
    result = agent.run(ri)
    assert isinstance(result, list)
    assert len(result) >= 1  # 최소 1개 반환
```

**Step 2: 전체 테스트 최종 확인**

```bash
python -m pytest -v
```
Expected: 전체 PASS

**Step 3: Final commit**

```bash
git add tests/test_supervisor.py
git commit -m "test: update test_supervisor_returns_proposal for list return type"
```
