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
