from unittest.mock import MagicMock, patch
from agents.literature import LiteratureAgent
from models.schemas import Idea, ResearchInput

def test_search_returns_references():
    agent = LiteratureAgent()
    agent.claude = MagicMock()
    agent.claude.generate.return_value = "1. Smith et al. (2023) - APD sensor design\n2. Kim et al. (2024)"

    with patch("agents.literature.arxiv.Search") as mock_search:
        mock_search.return_value.results.return_value = iter([])
        idea = Idea(title="APD 센서", description="설명", approach="접근")
        research_input = ResearchInput(
            domain="광학", objective="고감도", constraints=[]
        )
        refs = agent.find_references(idea, research_input)
    assert isinstance(refs, list)
    assert len(refs) > 0
