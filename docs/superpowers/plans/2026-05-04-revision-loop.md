# Revision Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Checkpoint #3(최종 검토) 이후 사용자가 피드백을 입력하면 Claude가 관련 섹션을 자동 판단해 재생성하는 루프를 추가한다.

**Architecture:** `SynthesizerAgent`에 `revise(proposal, feedback)` 메서드를 추가해 기존 제안서 + 피드백을 Claude에 전달하고 섹션을 재생성한다. `supervisor.py`의 Checkpoint #3을 while 루프로 교체해 빈 Enter 입력 시 종료, 피드백 입력 시 `revise()` 호출 후 전체 제안서를 다시 표시한다.

**Tech Stack:** Python 3.12, pydantic, rich, anthropic SDK (ClaudeRunner), pytest

---

## File Map

| 파일 | 변경 유형 | 내용 |
|------|-----------|------|
| `agents/synthesizer.py` | 수정 | `revise()` 메서드 추가 |
| `agents/supervisor.py` | 수정 | Checkpoint #3 while 루프로 교체 |
| `tests/test_synthesizer.py` | 수정 | `revise()` 단위 테스트 추가 |

---

## Task 1: SynthesizerAgent.revise() — 테스트 작성

**Files:**
- Modify: `tests/test_synthesizer.py`

- [ ] **Step 1: 실패 테스트 작성**

`tests/test_synthesizer.py` 파일 하단에 다음 테스트를 추가한다:

```python
def _make_proposal():
    idea, ri, refs = _make_inputs()
    return ResearchProposal(
        title="광학 - APD 센서",
        input=ri,
        selected_idea=idea,
        design_spec="기존 설계 사양 내용",
        experiment_plan="기존 실험 계획 내용",
        simulation_suggestion="기존 시뮬레이션 내용",
        references=refs,
    )


def test_revise_returns_proposal():
    agent = _make_agent()
    proposal = _make_proposal()
    revised = agent.revise(proposal, "설계 사양에서 소비전력 목표를 1mW 이하로 수정해줘")
    assert isinstance(revised, ResearchProposal)


def test_revise_calls_generate_once():
    agent = _make_agent()
    proposal = _make_proposal()
    agent.revise(proposal, "실험 계획 3단계를 더 구체적으로")
    agent.claude.generate.assert_called_once()


def test_revise_preserves_immutable_fields():
    agent = _make_agent()
    proposal = _make_proposal()
    revised = agent.revise(proposal, "시뮬레이션 도구를 FDTD로 변경해줘")
    assert revised.title == proposal.title
    assert revised.input == proposal.input
    assert revised.selected_idea == proposal.selected_idea
    assert revised.references == proposal.references


def test_revise_prompt_contains_feedback():
    agent = _make_agent()
    proposal = _make_proposal()
    feedback = "독특한_피드백_문자열"
    agent.revise(proposal, feedback)
    call_args = agent.claude.generate.call_args[0][0]
    assert feedback in call_args


def test_revise_prompt_contains_existing_sections():
    agent = _make_agent()
    proposal = _make_proposal()
    agent.revise(proposal, "수정 요청")
    call_args = agent.claude.generate.call_args[0][0]
    assert proposal.design_spec in call_args
    assert proposal.experiment_plan in call_args
    assert proposal.simulation_suggestion in call_args
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```
python -m pytest tests/test_synthesizer.py::test_revise_returns_proposal -v
```

Expected: `FAILED` — `AttributeError: 'SynthesizerAgent' object has no attribute 'revise'`

---

## Task 2: SynthesizerAgent.revise() — 구현

**Files:**
- Modify: `agents/synthesizer.py`

- [ ] **Step 1: `revise()` 메서드와 `_build_revise_prompt()` 추가**

`agents/synthesizer.py`의 `synthesize()` 메서드 바로 아래에 추가한다:

```python
def revise(self, proposal: ResearchProposal, feedback: str) -> ResearchProposal:
    raw = self.claude.generate(self._build_revise_prompt(proposal, feedback))
    design_spec, experiment_plan, simulation = self._parse_sections(raw)

    return ResearchProposal(
        title=proposal.title,
        input=proposal.input,
        selected_idea=proposal.selected_idea,
        design_spec=design_spec or proposal.design_spec,
        experiment_plan=experiment_plan or proposal.experiment_plan,
        simulation_suggestion=simulation or proposal.simulation_suggestion,
        references=proposal.references,
    )

def _build_revise_prompt(self, proposal: ResearchProposal, feedback: str) -> str:
    return f"""다음은 기존 연구 제안서입니다. 사용자의 수정 요청을 반영하여 필요한 섹션만 업데이트해주세요.

[기존 제안서]

## 설계 사양
{proposal.design_spec}

## 실험 계획
{proposal.experiment_plan}

## 시뮬레이션 방법
{proposal.simulation_suggestion}

[수정 요청]
{feedback}

수정이 필요 없는 섹션도 반드시 그대로 포함하여 아래 형식으로 전체 출력하세요:

## 설계 사양
(내용)

## 실험 계획
(내용)

## 시뮬레이션 방법
(내용)
"""
```

- [ ] **Step 2: 테스트 실행 — 통과 확인**

```
python -m pytest tests/test_synthesizer.py -v
```

Expected: 모든 테스트 PASS (기존 4개 + 신규 5개 = 9개)

- [ ] **Step 3: 커밋**

```
git add agents/synthesizer.py tests/test_synthesizer.py
git commit -m "feat: add SynthesizerAgent.revise() for feedback-driven regeneration"
```

---

## Task 3: supervisor.py Checkpoint #3 수정

**Files:**
- Modify: `agents/supervisor.py`

- [ ] **Step 1: `_display_proposal()` 헬퍼 메서드 추가**

`supervisor.py`의 `_select_ideas()` 메서드 아래에 추가한다:

```python
def _display_proposal(self, proposal: ResearchProposal, idx: int, total: int, round_num: int):
    round_label = "최초" if round_num == 0 else f"수정 {round_num}회차"
    title = f"Checkpoint #3: 최종 검토 [{idx}/{total}] ({round_label})"
    content = (
        f"[bold]{proposal.title}[/bold]\n\n"
        f"[cyan]── 설계 사양 ──[/cyan]\n{proposal.design_spec}\n\n"
        f"[cyan]── 실험 계획 ──[/cyan]\n{proposal.experiment_plan}\n\n"
        f"[cyan]── 시뮬레이션 방법 ──[/cyan]\n{proposal.simulation_suggestion}"
    )
    console.print(Panel(content, title=f"[bold cyan]{title}[/bold cyan]"))
```

`supervisor.py` 상단 import에 `Panel`이 없다면 추가한다:

```python
from rich.panel import Panel
```

- [ ] **Step 2: Checkpoint #3 while 루프로 교체**

`supervisor.py`에서 아래 블록을 찾아 교체한다.

**기존 코드 (57~63번 줄):**
```python
        # Checkpoint #3 — 전체 완료 후 한 번
        self.checkpoint.checkpoint_num = 3
        summary = "\n\n".join(
            f"[{p.selected_idea.title}]\n{p.design_spec[:200]}..." for p in proposals
        )
        self.checkpoint.display("최종 검토", summary)
        self.checkpoint.confirm("제안서 생성을 완료하시겠습니까?")
```

**교체 코드:**
```python
        # Checkpoint #3 — 아이디어별 수정 루프
        self.checkpoint.checkpoint_num = 3
        total = len(proposals)
        for idx, proposal in enumerate(proposals, 1):
            round_num = 0
            while True:
                self._display_proposal(proposal, idx, total, round_num)
                feedback = self.checkpoint.ask(
                    "수정할 내용을 입력하세요 (없으면 Enter로 완료)"
                )
                if not feedback.strip():
                    break
                console.print(f"[bold green]재생성 중...[/bold green]")
                proposal = self.synthesizer.revise(proposal, feedback)
                round_num += 1
            proposals[idx - 1] = proposal
```

- [ ] **Step 3: 테스트 실행**

```
python -m pytest tests/ -v
```

Expected: 전체 PASS

- [ ] **Step 4: 커밋**

```
git add agents/supervisor.py
git commit -m "feat: replace Checkpoint #3 with revision loop for iterative feedback"
```

---

## Self-Review

**Spec coverage:**
- `revise()` 메서드 추가 → Task 1~2 ✅
- Claude 자동 섹션 판단 → `_build_revise_prompt()` 프롬프트에서 Claude에게 위임 ✅
- 전체 제안서 표시 → `_display_proposal()` ✅
- while 루프 + 빈 Enter 종료 → Task 3 ✅
- 무제한 반복 → while True 루프 ✅
- 불변 필드 유지 → `revise()`에서 title/input/selected_idea/references 원본 유지 ✅

**Placeholder scan:** 없음

**Type consistency:**
- `revise(proposal: ResearchProposal, feedback: str) -> ResearchProposal` — Task 1 시그니처와 Task 2 구현 일치
- `proposals[idx - 1] = proposal` — proposals는 `list[ResearchProposal]`, 타입 일치
