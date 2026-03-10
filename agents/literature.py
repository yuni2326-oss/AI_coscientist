import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'libs', 'zotero_scholar_to_local'))

from zotero_scholar_to_local import (
    search_google_scholar_recent,
    search_openalex,
    search_semantic_scholar,
    merge_and_deduplicate,
    translate_to_english,
    ScholarPaper,
)
from core.claude_runner import ClaudeRunner
from models.schemas import Idea, ResearchInput


class LiteratureAgent:
    def __init__(self):
        self.claude = ClaudeRunner()

    def find_references(self, idea: Idea, research_input: ResearchInput, limit: int = 5, years_back: int = 7) -> list[str]:
        papers = self._search_multi_source(idea, research_input, limit, years_back)
        return self._ask_claude(idea, research_input, papers)

    def _search_multi_source(self, idea: Idea, research_input: ResearchInput, limit: int, years_back: int) -> list[ScholarPaper]:
        query_ko = f"{research_input.domain} {idea.title} {research_input.objective}"
        query_en = translate_to_english(query_ko)

        scholar_papers, openalex_papers, semantic_papers = [], [], []

        try:
            scholar_papers = search_google_scholar_recent(query_en, limit=limit, years_back=years_back)
        except Exception:
            pass

        try:
            openalex_papers = search_openalex(query_en, limit=limit, years_back=years_back)
        except Exception:
            pass

        try:
            semantic_papers = search_semantic_scholar(query_en, limit=limit, years_back=years_back)
        except Exception:
            pass

        return merge_and_deduplicate(scholar_papers, openalex_papers, semantic_papers)

    def _ask_claude(self, idea: Idea, research_input: ResearchInput, papers: list[ScholarPaper]) -> list[str]:
        paper_list = "\n".join(
            f"- {p.title} / {', '.join(p.authors[:3])} ({p.year}) [{p.source}]"
            + (f" DOI: {p.doi}" if p.doi else "")
            for p in papers[:10]
        ) if papers else "검색 결과 없음"

        prompt = f"""다음 공학 연구 아이디어에 관련된 핵심 참고문헌을 정리해주세요.

아이디어: {idea.title}
도메인: {research_input.domain}
목표: {research_input.objective}

실제 검색된 논문 목록:
{paper_list}

위 검색 결과를 바탕으로 가장 관련성 높은 참고문헌 5개를 번호 목록으로 정리하세요.
형식: N. [저자] ([연도]) - [제목]
검색 결과가 부족하면 관련 분야의 대표 논문을 추가해도 됩니다.
"""
        raw = self.claude.generate(prompt)
        lines = [line.strip() for line in raw.split("\n") if line.strip() and line[0].isdigit()]
        return lines if lines else [raw[:300]]
