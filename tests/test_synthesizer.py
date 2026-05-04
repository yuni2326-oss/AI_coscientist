from unittest.mock import MagicMock
from agents.synthesizer import SynthesizerAgent
from models.schemas import Idea, ResearchInput, ResearchProposal

_MOCK_RESPONSE = """\
## 설계 사양
APD 기반 고감도 수광부 설계...

## 실험 계획
1단계: 기초 특성 측정...

## 시뮬레이션 방법
LTspice로 APD 바이어스 회로 시뮬레이션...\
"""

def _make_agent():
    agent = SynthesizerAgent()
    agent.claude = MagicMock()
    agent.claude.generate.return_value = _MOCK_RESPONSE
    return agent

def _make_inputs():
    idea = Idea(title="APD 센서", description="설명", approach="접근")
    ri = ResearchInput(domain="광학", objective="고감도", constraints=["저전력"])
    refs = ["1. Smith (2023) - APD design"]
    return idea, ri, refs


def test_synthesize_returns_proposal():
    agent = _make_agent()
    idea, ri, refs = _make_inputs()
    proposal = agent.synthesize(ri, idea, refs)
    assert isinstance(proposal, ResearchProposal)


def test_synthesize_calls_generate_once():
    agent = _make_agent()
    idea, ri, refs = _make_inputs()
    agent.synthesize(ri, idea, refs)
    agent.claude.generate.assert_called_once()


def test_synthesize_parses_all_sections():
    agent = _make_agent()
    idea, ri, refs = _make_inputs()
    proposal = agent.synthesize(ri, idea, refs)
    assert "APD" in proposal.design_spec
    assert "1단계" in proposal.experiment_plan
    assert "LTspice" in proposal.simulation_suggestion


def test_synthesize_sets_references():
    agent = _make_agent()
    idea, ri, refs = _make_inputs()
    proposal = agent.synthesize(ri, idea, refs)
    assert proposal.references == refs


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
