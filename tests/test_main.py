from unittest.mock import MagicMock, patch
from main import save_proposal, collect_input
from models.schemas import ResearchInput, ResearchProposal, Idea


def _make_proposal():
    idea = Idea(title="테스트", description="설명", approach="접근")
    ri = ResearchInput(domain="센서", objective="목표", constraints=["저전력"])
    return ResearchProposal(
        title="테스트 제안서",
        input=ri,
        selected_idea=idea,
        design_spec="## 설계\n내용",
        experiment_plan="## 실험\n내용",
        simulation_suggestion="## 시뮬레이션\n내용",
        references=["ref1"]
    )


def test_save_proposal_creates_md_file(tmp_path):
    md_path, docx_path = save_proposal(_make_proposal(), output_dir=str(tmp_path))
    assert md_path.exists()
    content = md_path.read_text(encoding="utf-8")
    assert "테스트 제안서" in content


def test_save_proposal_creates_docx_file(tmp_path):
    md_path, docx_path = save_proposal(_make_proposal(), output_dir=str(tmp_path))
    assert docx_path.exists()
    assert docx_path.suffix == ".docx"


def test_save_proposal_returns_both_paths(tmp_path):
    md_path, docx_path = save_proposal(_make_proposal(), output_dir=str(tmp_path))
    assert md_path.suffix == ".md"
    assert docx_path.suffix == ".docx"
    assert md_path.stem == docx_path.stem  # 같은 파일명 기반
