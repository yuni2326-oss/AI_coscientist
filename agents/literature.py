import arxiv
from core.claude_runner import ClaudeRunner
from models.schemas import Idea, ResearchInput

class LiteratureAgent:
    def __init__(self):
        self.claude = ClaudeRunner()

    def find_references(self, idea: Idea, research_input: ResearchInput) -> list[str]:
        arxiv_refs = self._search_arxiv(idea, research_input)
        claude_refs = self._ask_claude(idea, research_input, arxiv_refs)
        return claude_refs

    def _search_arxiv(self, idea: Idea, research_input: ResearchInput) -> list[str]:
        query = f"{research_input.domain} {idea.title} {research_input.objective}"
        search = arxiv.Search(query=query, max_results=5)
        refs = []
        try:
            for result in search.results():
                refs.append(f"{result.title} ({result.published.year}) - {result.entry_id}")
        except Exception:
            pass
        return refs

    def _ask_claude(self, idea: Idea, research_input: ResearchInput, arxiv_refs: list[str]) -> list[str]:
        prompt = f"""
다음 공학 연구 아이디어에 관련된 핵심 참고문헌을 제시하세요.

아이디어: {idea.title}
도메인: {research_input.domain}
목표: {research_input.objective}

arxiv 검색 결과:
{chr(10).join(arxiv_refs) if arxiv_refs else '없음'}

실제 존재할 가능성이 높은 논문/특허를 포함하여 핵심 참고문헌 5개를 번호 목록으로 작성하세요.
형식: N. [저자] ([연도]) - [제목]
"""
        raw = self.claude.generate(prompt)
        lines = [line.strip() for line in raw.split("\n") if line.strip() and line[0].isdigit()]
        return lines if lines else [raw[:300]]
