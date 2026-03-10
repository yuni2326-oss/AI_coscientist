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
