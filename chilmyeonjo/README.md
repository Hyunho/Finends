# 칠면조

칠면조는 개인 트레이딩 전략을 정리하고 검증하기 위한 저장소입니다.
전략 문서, Python 기반 분석 및 백테스트 코드, Rails 기반 읽기 전용 웹 뷰어를 함께 관리합니다.

## 구성

- `strategies/`: 전략별 문서, 구현 코드, 테스트
- `strategies/box_range/`: 현재 구현된 박스권 전략과 백테스트 결과, 회고 문서
- `web/`: `strategies/` 아래 문서를 브라우저에서 읽기 좋게 보여주는 Rails 앱
- `example-strategy.md`: 새 전략 문서를 시작할 때 참고할 수 있는 템플릿

## 현재 포함된 기능

- 최근 3년 일봉 데이터를 기준으로 박스권 여부와 현재 위치를 요약하는 CLI
- 박스권 규칙을 과거 데이터에 적용해 성과를 비교하는 백테스트 CLI
- 전략 문서, 히스토리, 소스 파일, 테스트 파일을 탐색하는 웹 뷰어

## 빠른 시작

### Python 전략 코드

현재 디렉토리가 패키지 루트라서, 여기에서 바로 실행할 때는 `PYTHONPATH=..`가 필요합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r strategies/requirements.txt
export PYTHONPATH=..
```

박스권 분석 예시:

```bash
python3 -m chilmyeonjo.strategies.box_range.src.cli AAPL
python3 -m chilmyeonjo.strategies.box_range.src.cli 005930 --market kospi
python3 -m chilmyeonjo.strategies.box_range.src.cli TSLA --output json
```

백테스트 예시:

```bash
python3 -m chilmyeonjo.strategies.box_range.src.backtest_cli --save-report
python3 -m chilmyeonjo.strategies.box_range.src.backtest_cli TSLA
python3 -m chilmyeonjo.strategies.box_range.src.backtest_cli 263750.KQ --output md
```

## 테스트

Python 테스트:

```bash
PYTHONPATH=.. python3 -m unittest \
  strategies.box_range.tests.test_box_range \
  strategies.box_range.tests.test_box_range_backtest
```

## 웹 뷰어

`web/`은 전략 문서를 읽기 위한 Rails 앱입니다. Python 전략 코드를 실행하지 않고 저장소 파일만 읽습니다.

- Ruby: `4.0.2`
- Rails: `8.1.3`

실행:

```bash
cd web
bundle install
bin/rails server
```

기본 주소는 `http://127.0.0.1:3000`입니다.

테스트:

```bash
cd web
bin/rails test
```

## 문서 운영 방식

- 전략 문서는 전략 폴더 아래에 날짜 기반 파일명으로 저장합니다.
- 백테스트 결과는 같은 전략 폴더에 별도 마크다운 문서로 남깁니다.
- 실패한 시도나 회고는 `history/` 아래에 보관합니다.

현재 박스권 전략 관련 문서는 아래 파일들에 있습니다.

- `strategies/box_range/2026-04-16-box-range-strategy.md`
- `strategies/box_range/2026-04-16-box-range-backtest.md`
- `strategies/box_range/history/2026-04-16-box-range-v2-attempt-failed.md`

## 참고

- 현재 Python 의존성은 `yfinance` 하나입니다.
- 웹 앱은 로컬에 `ruby-4.0.2`가 설치되어 있어야 실행 및 테스트가 가능합니다.
