# 최종 검토 수정 루프 설계

**날짜:** 2026-05-04  
**상태:** 승인됨

## 개요

Checkpoint #3(최종 검토) 이후 사용자가 수정 피드백을 입력하면 Claude가 관련 섹션을 자동 판단하여 재생성하는 루프를 추가한다. 만족할 때까지 무제한 반복 가능하며, 빈 Enter 입력으로 완료한다.

## 변경 대상 파일

- `agents/synthesizer.py` — `revise()` 메서드 추가
- `agents/supervisor.py` — Checkpoint #3 while 루프로 교체

## 흐름

```
전체 제안서 표시
→ "수정할 내용 입력 (없으면 Enter로 완료)"
    [피드백 있음] → synthesizer.revise() → 제안서 업데이트 → 재표시 → 반복
    [빈 Enter]   → 저장 종료
```

## SynthesizerAgent.revise()

### 시그니처
```python
def revise(self, proposal: ResearchProposal, feedback: str) -> ResearchProposal
```

### 프롬프트 구조
기존 제안서 3개 섹션(설계 사양, 실험 계획, 시뮬레이션 방법) 전체 + 수정 요청을 Claude에 전달한다. Claude가 피드백을 분석해 변경이 필요한 섹션만 업데이트하고, 나머지는 그대로 유지한다. 결과는 기존 `_parse_sections()`로 파싱한다.

### 불변 필드
`title`, `input`, `selected_idea`, `references`는 원본 proposal에서 그대로 유지하며 3개 섹션만 교체한다.

## supervisor.py Checkpoint #3 변경

### 현재
```python
summary = "\n\n".join(f"[{p.selected_idea.title}]\n{p.design_spec[:200]}..." for p in proposals)
self.checkpoint.display("최종 검토", summary)
self.checkpoint.confirm("제안서 생성을 완료하시겠습니까?")
```

### 변경 후
각 제안서를 개별 while 루프로 처리한다.

```
for each proposal:
    round = 0
    while True:
        제목 + 3개 섹션 전체를 Rich Panel로 표시 (라운드 번호 포함)
        피드백 = ask("수정할 내용 입력 (없으면 Enter로 완료)")
        if 피드백 없음: break
        round += 1
        proposal = synthesizer.revise(proposal, 피드백)
```

## 표시 형식

```
╔══════════════════════════════════════════╗
║  Checkpoint #3: 최종 검토 [1/2] (수정 N회차) ║
║  도메인 - 아이디어 제목                    ║
╠══════════════════════════════════════════╣
║  [설계 사양]  ...전체 내용...              ║
║  [실험 계획]  ...전체 내용...              ║
║  [시뮬레이션 방법]  ...전체 내용...         ║
╚══════════════════════════════════════════╝
수정할 내용을 입력하세요 (없으면 Enter로 완료):
```

- 최초 표시: `(최초)`
- 재생성 후: `(수정 1회차)`, `(수정 2회차)` ...

## 테스트 고려사항

- `test_synthesizer.py`에 `revise()` 단위 테스트 추가
- 빈 피드백 입력 시 루프 종료 확인
- `_parse_sections()` 재사용으로 파싱 로직 중복 없음
