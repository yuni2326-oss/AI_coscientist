import sys
import os
import sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'libs', 'zotero_scholar_to_local'))

from zotero_scholar_to_local import (
    search_google_scholar_recent,
    search_openalex,
    search_semantic_scholar,
    merge_and_deduplicate,
    translate_to_english,
    resolve_zotero_paths,
    ScholarPaper,
)
from core.claude_runner import ClaudeRunner
from models.schemas import Idea, ResearchInput


class LiteratureAgent:
    def __init__(self):
        self.claude = ClaudeRunner()

    def find_references(self, idea: Idea, research_input: ResearchInput, limit: int = 10, years_back: int = 7) -> list[str]:
        query_ko = f"{research_input.domain} {idea.title} {research_input.objective}"
        try:
            query_en = translate_to_english(query_ko)
        except Exception:
            query_en = query_ko  # 번역 실패 시 원본 쿼리 사용

        papers = self._search_multi_source(query_en, limit, years_back)
        zotero_papers = self._search_zotero(query_en, limit)

        # Zotero 결과를 온라인 결과와 병합 (Zotero가 최우선)
        all_papers = merge_and_deduplicate(zotero_papers, papers, [])

        return self._ask_claude(idea, research_input, all_papers)

    def _search_multi_source(self, query_en: str, limit: int, years_back: int) -> list[ScholarPaper]:
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

    def _search_zotero(self, query_en: str, limit: int) -> list[ScholarPaper]:
        """로컬 Zotero 라이브러리에서 키워드 검색"""
        try:
            paths = resolve_zotero_paths()
            db_path = paths.db_path
        except Exception:
            return []

        keywords = [w for w in query_en.lower().split() if len(w) > 3]
        if not keywords:
            return []

        try:
            with sqlite3.connect(str(db_path)) as con:
                con.row_factory = sqlite3.Row

                # 제목 기준 키워드 검색 (첫 3개 키워드 OR 조건)
                kw_conditions = " OR ".join(
                    "LOWER(idv.value) LIKE ?" for _ in keywords[:3]
                )
                kw_params = [f"%{kw}%" for kw in keywords[:3]]

                item_ids = [
                    row[0] for row in con.execute(
                        f"""
                        SELECT DISTINCT i.itemID FROM items i
                        JOIN itemData id ON id.itemID = i.itemID AND id.fieldID = 1
                        JOIN itemDataValues idv ON idv.valueID = id.valueID
                        WHERE i.libraryID = 1
                          AND i.itemTypeID NOT IN (1, 14)
                          AND ({kw_conditions})
                        LIMIT ?
                        """,
                        kw_params + [limit]
                    ).fetchall()
                ]

                papers = []
                for item_id in item_ids:
                    # 필드 값 수집 (title, year, DOI, abstract, venue)
                    fields = {
                        row[0]: row[1]
                        for row in con.execute(
                            "SELECT id.fieldID, idv.value "
                            "FROM itemData id JOIN itemDataValues idv ON idv.valueID = id.valueID "
                            "WHERE id.itemID = ? AND id.fieldID IN (1, 6, 8, 10, 27, 41)",
                            (item_id,)
                        ).fetchall()
                    }
                    title = fields.get(1, "")
                    if not title:
                        continue

                    # 저자 수집
                    authors = [
                        f"{row[0]} {row[1]}".strip()
                        for row in con.execute(
                            """
                            SELECT c.lastName, c.firstName FROM itemCreators ic
                            JOIN creators c ON c.creatorID = ic.creatorID
                            WHERE ic.itemID = ? ORDER BY ic.orderIndex LIMIT 5
                            """,
                            (item_id,)
                        ).fetchall()
                    ]

                    year_raw = fields.get(6, "")
                    year = year_raw[:4] if year_raw else None

                    papers.append(ScholarPaper(
                        title=title,
                        url=fields.get(10, ""),
                        authors=authors,
                        year=year,
                        venue=fields.get(41),
                        abstract=fields.get(27),
                        doi=fields.get(8),
                        source="zotero",
                    ))

                return papers

        except Exception as e:
            print(f"[WARN] Zotero 검색 오류: {e}")
            return []

    def _ask_claude(self, idea: Idea, research_input: ResearchInput, papers: list[ScholarPaper]) -> list[str]:
        def fmt(p: ScholarPaper) -> str:
            src_tag = f"[{p.source}]" if p.source else ""
            doi_str = f" DOI:{p.doi}" if p.doi else ""
            authors = ", ".join(p.authors[:3]) if p.authors else "Unknown"
            return f"- {p.title} / {authors} ({p.year}) {src_tag}{doi_str}"

        paper_list = "\n".join(fmt(p) for p in papers[:15]) if papers else "검색 결과 없음"

        prompt = f"""다음 공학 연구 아이디어에 관련된 핵심 참고문헌을 정리해주세요.

아이디어: {idea.title}
도메인: {research_input.domain}
목표: {research_input.objective}

검색된 논문 목록 (출처: [zotero]=내 라이브러리, [scholar/openalex/semantic_scholar]=온라인):
{paper_list}

위 검색 결과를 바탕으로 가장 관련성 높은 참고문헌 10개를 번호 목록으로 정리하세요.
[zotero] 출처 논문을 우선적으로 포함하세요.
형식: N. [저자] ([연도]) - [제목]
검색 결과가 부족하면 관련 분야의 대표 논문을 추가해도 됩니다.
"""
        raw = self.claude.generate(prompt)
        lines = [line.strip() for line in raw.split("\n") if line.strip() and line[0].isdigit()]
        return lines if lines else [raw[:500]]
