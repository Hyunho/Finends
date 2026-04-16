from __future__ import annotations

import argparse
import json
import sys

from chilmyeonjo.strategies.box_range.src.analysis import (
    DEFAULT_LOOKBACK_YEARS,
    analyze_box_range,
    fetch_price_history,
    format_text_result,
    normalize_ticker,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="종목 심볼을 받아 최근 박스권 여부와 현재 위치를 요약합니다."
    )
    parser.add_argument("ticker", help="예: AAPL, TSLA, 005930")
    parser.add_argument(
        "--market",
        choices=["auto", "us", "kospi", "kosdaq"],
        default="auto",
        help="국내 숫자 심볼이면 kospi/kosdaq를 지정해 접미사를 붙일 수 있습니다.",
    )
    parser.add_argument(
        "--lookback-years",
        type=int,
        default=DEFAULT_LOOKBACK_YEARS,
        help="시세 조회 기간입니다. 기본값은 3년입니다.",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="출력 형식입니다.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        resolved_ticker = normalize_ticker(args.ticker, market=args.market)
        bars = fetch_price_history(
            ticker=resolved_ticker,
            lookback_years=args.lookback_years,
        )
        result = analyze_box_range(
            ticker=args.ticker,
            resolved_ticker=resolved_ticker,
            bars=bars,
        )
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1

    if args.output == "json":
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(format_text_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
