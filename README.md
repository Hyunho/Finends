# Finends

친구들끼리 주식 전략과 아이디어를 공유하기 위한 문서 레포입니다.

현재 참여자:
- 아리엘
- 꾹이
- 칠면조

## Purpose

- 각자 전략 아이디어를 기록합니다.
- 서로의 관점을 비교하고 피드백합니다.
- 종목, 매매 관점, 리스크를 문서로 남깁니다.

## Structure

각자 영어 폴더명으로 공간을 나눕니다.

- `ariel/`
- `gguki/`
- `chilmyeonjo/`

문서 형식은 강제하지 않습니다. 각자 편한 방식으로 정리하면 됩니다.

## Recommended Flow

추천 방식은 아래 정도만 참고하면 충분합니다.

1. 친구 본인 폴더에 새 문서를 만듭니다.
2. 전략 이름이나 날짜가 드러나는 파일명으로 저장합니다.
3. 아이디어, 근거, 리스크, 메모를 자유롭게 적습니다.
4. 필요하면 이후 결과나 회고를 같은 문서에 이어 적습니다.

## Naming Ideas

아래는 권장 예시일 뿐, 꼭 따를 필요는 없습니다.

- `2026-04-16-breakout-idea.md`
- `semiconductor-cycle.md`
- `value-screen-notes.md`

## Notes

- 문서 포맷은 자유입니다.
- 예시 문서는 시작용 샘플입니다.
- 복사해서 써도 되고, 무시하고 각자 방식으로 관리해도 됩니다.
- 개인 사용자용 에이전트 지침이 필요하면 `AGENTS.local.template.md`를 참고해 `AGENTS.local.md`를 작성합니다.

## First Strategy

칠면조의 박스권 전략 관련 파일은 `chilmyeonjo/strategies/box_range/` 아래에 모아 두었습니다.

현재 채택 전략 문서는 `chilmyeonjo/strategies/box_range/2026-04-16-box-range-strategy.md`입니다.
`v2` 시도 실패 회고는 `chilmyeonjo/strategies/box_range/2026-04-16-box-range-v2-attempt-failed.md`에 남겼습니다.

박스권 판단 CLI도 함께 추가했습니다.

```bash
pip install -r chilmyeonjo/strategies/box_range/requirements.txt
python3 -m chilmyeonjo.strategies.box_range.cli AAPL
python3 -m chilmyeonjo.strategies.box_range.cli 005930 --market kospi
```

박스권 전략 백테스트와 결과 문서 저장:

```bash
python3 -m chilmyeonjo.strategies.box_range.backtest_cli --save-report
```
