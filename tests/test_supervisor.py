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
    # ask() is called: (1) idea selection, (2) CP#3 revision prompt → empty to exit loop
    agent.checkpoint.ask.side_effect = ["A를 선택", ""]
    agent.checkpoint.confirm.return_value = True
    agent.literature.find_references.return_value = ["ref1", "ref2"]
    mock_proposal = MagicMock()
    mock_proposal.title = "테스트 제안서"
    mock_proposal.design_spec = "## 설계 사양\n내용..."
    mock_proposal.experiment_plan = "## 실험 계획\n내용..."
    mock_proposal.simulation_suggestion = "## 시뮬레이션 방법\n내용..."
    agent.synthesizer.synthesize.return_value = mock_proposal

    ri = ResearchInput(domain="센서", objective="목표", constraints=[])
    result = agent.run(ri)
    assert isinstance(result, list)
    assert len(result) >= 1


def test_supervisor_returns_list_of_proposals():
    agent = SupervisorAgent()
    agent.generator = MagicMock()
    agent.critic = MagicMock()
    agent.literature = MagicMock()
    agent.synthesizer = MagicMock()
    agent.checkpoint = MagicMock()

    agent.generator.generate.return_value = [make_idea("A"), make_idea("B"), make_idea("C")]
    agent.critic.score_all.return_value = [make_idea("A"), make_idea("B"), make_idea("C")]
    # ask() is called: (1) idea selection, (2) CP#3 revision for proposal 1, (3) CP#3 for proposal 2
    agent.checkpoint.ask.side_effect = ["1,2", "", ""]
    agent.checkpoint.confirm.return_value = True
    agent.literature.find_references.return_value = ["ref1", "ref2"]
    mock_proposal = MagicMock()
    mock_proposal.title = "테스트 제안서"
    mock_proposal.design_spec = "## 설계 사양\n내용..."
    mock_proposal.experiment_plan = "## 실험 계획\n내용..."
    mock_proposal.simulation_suggestion = "## 시뮬레이션 방법\n내용..."
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
    selected = agent._select_ideas(ideas, "없는아이디어")
    assert len(selected) == 1


def test_supervisor_cp3_revision_calls_revise():
    """CP#3에서 피드백 입력 시 synthesizer.revise()가 호출되고 반환값이 결과에 반영되는지 검증"""
    agent = SupervisorAgent()
    ri = ResearchInput(domain="광학", objective="고감도", constraints=["저전력"])

    mock_idea = MagicMock()
    mock_idea.title = "테스트 아이디어"
    mock_idea.scores = {"기술성숙도": 5, "실현가능성": 5, "독창성": 5}

    mock_proposal = MagicMock()
    mock_proposal.title = "테스트 제안서"
    mock_proposal.design_spec = "## 설계 사양\n내용..."
    mock_proposal.experiment_plan = "## 실험 계획\n내용..."
    mock_proposal.simulation_suggestion = "## 시뮬레이션 방법\n내용..."
    mock_proposal.selected_idea = mock_idea

    revised_proposal = MagicMock()
    revised_proposal.title = "수정된 제안서"
    revised_proposal.design_spec = "## 설계 사양\n수정된 내용..."
    revised_proposal.experiment_plan = "## 실험 계획\n수정된 내용..."
    revised_proposal.simulation_suggestion = "## 시뮬레이션 방법\n수정된 내용..."
    revised_proposal.selected_idea = mock_idea

    agent.generator = MagicMock()
    agent.critic = MagicMock()
    agent.literature = MagicMock()
    agent.synthesizer = MagicMock()
    agent.checkpoint = MagicMock()

    agent.generator.generate = MagicMock(return_value=[mock_idea])
    agent.critic.score_all = MagicMock(return_value=[mock_idea])
    agent.literature.find_references = MagicMock(return_value=["ref1"])
    agent.synthesizer.synthesize = MagicMock(return_value=mock_proposal)
    agent.synthesizer.revise = MagicMock(return_value=revised_proposal)
    # CP#1: 아이디어 선택, CP#3: 피드백 → revise 호출, 다음 입력 → 빈 입력으로 종료
    agent.checkpoint.ask = MagicMock(side_effect=["1", "수정 요청", ""])
    agent.checkpoint.confirm = MagicMock(return_value=True)

    result = agent.run(ri)

    agent.synthesizer.revise.assert_called_once_with(mock_proposal, "수정 요청")
    assert result[0] is revised_proposal
