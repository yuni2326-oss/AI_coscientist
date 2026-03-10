from unittest.mock import MagicMock, patch
from agents.literature import LiteratureAgent
from models.schemas import Idea, ResearchInput


def _make_inputs():
    idea = Idea(title="APD 센서", description="설명", approach="접근")
    ri = ResearchInput(domain="광학", objective="고감도", constraints=[])
    return idea, ri


def test_search_returns_references():
    agent = LiteratureAgent()
    agent.claude = MagicMock()
    agent.claude.generate.return_value = "1. Smith et al. (2023) - APD sensor design\n2. Kim et al. (2024)"

    with patch("agents.literature.search_google_scholar_recent", return_value=[]), \
         patch("agents.literature.search_openalex", return_value=[]), \
         patch("agents.literature.search_semantic_scholar", return_value=[]), \
         patch("agents.literature.merge_and_deduplicate", return_value=[]), \
         patch("agents.literature.translate_to_english", return_value="APD sensor optical"), \
         patch.object(agent, "_search_zotero", return_value=[]):

        refs = agent.find_references(*_make_inputs())

    assert isinstance(refs, list)
    assert len(refs) > 0


def test_multi_source_failure_graceful():
    """각 소스가 실패해도 Claude 결과 반환"""
    agent = LiteratureAgent()
    agent.claude = MagicMock()
    agent.claude.generate.return_value = "1. Lee (2022) - Sensor fusion\n2. Park (2023) - NIR"

    with patch("agents.literature.search_google_scholar_recent", side_effect=Exception("fail")), \
         patch("agents.literature.search_openalex", side_effect=Exception("fail")), \
         patch("agents.literature.search_semantic_scholar", side_effect=Exception("fail")), \
         patch("agents.literature.merge_and_deduplicate", return_value=[]), \
         patch("agents.literature.translate_to_english", return_value="sensor"), \
         patch.object(agent, "_search_zotero", return_value=[]):

        refs = agent.find_references(*_make_inputs())

    assert isinstance(refs, list)
    assert len(refs) > 0


def test_zotero_unavailable_graceful():
    """Zotero가 없어도 온라인 결과만으로 동작"""
    agent = LiteratureAgent()
    agent.claude = MagicMock()
    agent.claude.generate.return_value = "1. Park (2024) - NIR sensor"

    with patch("agents.literature.resolve_zotero_paths", side_effect=FileNotFoundError("no zotero")), \
         patch("agents.literature.search_google_scholar_recent", return_value=[]), \
         patch("agents.literature.search_openalex", return_value=[]), \
         patch("agents.literature.search_semantic_scholar", return_value=[]), \
         patch("agents.literature.merge_and_deduplicate", return_value=[]), \
         patch("agents.literature.translate_to_english", return_value="sensor"):

        refs = agent.find_references(*_make_inputs())

    assert isinstance(refs, list)
    assert len(refs) > 0
