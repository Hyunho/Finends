from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from chilmyeonjo.strategies.box_range.src.analysis import DEFAULT_LOOKBACK_YEARS
from chilmyeonjo.strategies.box_range.src.backtest import (
    DEFAULT_BACKTEST_TICKERS,
    DEFAULT_ROUND_TRIP_COST,
    build_markdown_report,
    default_report_path,
    format_backtest_summary,
    run_backtest_for_ticker,
    save_markdown_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="박스권 전략을 과거 데이터에 적용해 백테스트하고 결과를 저장합니다."
    )
    parser.add_argument(
        "tickers",
        nargs="*",
        default=list(DEFAULT_BACKTEST_TICKERS),
        help="예: TSLA 263750.KQ. 기본값은 TSLA와 263750.KQ입니다.",
    )
    parser.add_argument(
        "--market",
        choices=["auto", "us", "kospi", "kosdaq"],
        default="auto",
        help="raw 심볼에 적용할 시장 규칙입니다. 기본값은 auto입니다.",
    )
    parser.add_argument(
        "--lookback-years",
        type=int,
        default=DEFAULT_LOOKBACK_YEARS,
        help="시세 조회 기간입니다. 기본값은 3년입니다.",
    )
    parser.add_argument(
        "--round-trip-cost",
        type=float,
        default=DEFAULT_ROUND_TRIP_COST,
        help="왕복 거래 비용 비율입니다. 기본값은 0.003(0.3%%)입니다.",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json", "md"],
        default="text",
        help="표준 출력 형식입니다.",
    )
    parser.add_argument(
        "--save-report",
        action="store_true",
        help="마크다운 결과 문서를 저장합니다.",
    )
    parser.add_argument(
        "--report-path",
        help="마크다운 결과 문서를 저장할 경로입니다.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        results = [
            run_backtest_for_ticker(
                ticker=ticker,
                market=args.market,
                lookback_years=args.lookback_years,
                round_trip_cost=args.round_trip_cost,
            )
            for ticker in args.tickers
        ]
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1

    markdown = build_markdown_report(
        results=results,
        lookback_years=args.lookback_years,
        round_trip_cost=args.round_trip_cost,
    )
    report_path: Path | None = None
    if args.save_report or args.report_path:
        report_path = Path(args.report_path) if args.report_path else default_report_path()
        save_markdown_report(markdown, report_path)

    if args.output == "json":
        payload = [result.to_dict() for result in results]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.output == "md":
        print(markdown, end="")
    else:
        print(format_backtest_summary(results))

    if report_path is not None:
        print(f"\n리포트 저장: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
