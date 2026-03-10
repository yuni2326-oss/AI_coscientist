from unittest.mock import MagicMock, patch
from agents.literature import LiteratureAgent
from models.schemas import Idea, ResearchInput


def test_search_returns_references():
    agent = LiteratureAgent()
    agent.claude = MagicMock()
    agent.claude.generate.return_value = "1. Smith et al. (2023) - APD sensor design\n2. Kim et al. (2024)"

    with patch("agents.literature.search_google_scholar_recent", return_value=[]), \
         patch("agents.literature.search_openalex", return_value=[]), \
         patch("agents.literature.search_semantic_scholar", return_value=[]), \
         patch("agents.literature.merge_and_deduplicate", return_value=[]), \
         patch("agents.literature.translate_to_english", return_value="APD sensor optical high sensitivity"):

        idea = Idea(title="APD 센서", description="설명", approach="접근")
        research_input = ResearchInput(domain="광학", objective="고감도", constraints=[])
        refs = agent.find_references(idea, research_input)

    assert isinstance(refs, list)
    assert len(refs) > 0


def test_multi_source_failure_graceful():
    """각 소스가 실패해도 Claude 결과 반환"""
    agent = LiteratureAgent()
    agent.claude = MagicMock()
    agent.claude.generate.return_value = "1. Lee (2022) - Sensor fusion\n2. Park (2023) - NIR spectroscopy"

    with patch("agents.literature.search_google_scholar_recent", side_effect=Exception("network error")), \
         patch("agents.literature.search_openalex", side_effect=Exception("api error")), \
         patch("agents.literature.search_semantic_scholar", side_effect=Exception("timeout")), \
         patch("agents.literature.merge_and_deduplicate", return_value=[]), \
         patch("agents.literature.translate_to_english", return_value="sensor"):

        idea = Idea(title="센서", description="설명", approach="접근")
        research_input = ResearchInput(domain="센서", objective="목표", constraints=[])
        refs = agent.find_references(idea, research_input)

    assert isinstance(refs, list)
    assert len(refs) > 0
