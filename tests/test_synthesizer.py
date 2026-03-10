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
