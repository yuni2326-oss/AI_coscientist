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
    mock_proposal = MagicMock()
    mock_proposal.design_spec = "## 설계 사양\n내용..."
    agent.synthesizer.synthesize.return_value = mock_proposal

    ri = ResearchInput(domain="센서", objective="목표", constraints=[])
    result = agent.run(ri)
    assert result is not None
