"""Box range strategy tools for chilmyeonjo."""

from .analysis import (
    DEFAULT_LOOKBACK_YEARS,
    BoxRangeResult,
    PriceBar,
    analyze_box_range,
    fetch_price_history,
    format_text_result,
    normalize_ticker,
)
from .backtest import (
    DEFAULT_BACKTEST_TICKERS,
    DEFAULT_ROUND_TRIP_COST,
    BacktestResult,
    BacktestTrade,
    build_markdown_report,
    default_report_path,
    format_backtest_summary,
    run_backtest_for_ticker,
    save_markdown_report,
)

__all__ = [
    "DEFAULT_BACKTEST_TICKERS",
    "DEFAULT_LOOKBACK_YEARS",
    "DEFAULT_ROUND_TRIP_COST",
    "BacktestResult",
    "BacktestTrade",
    "BoxRangeResult",
    "PriceBar",
    "analyze_box_range",
    "build_markdown_report",
    "default_report_path",
    "fetch_price_history",
    "format_backtest_summary",
    "format_text_result",
    "normalize_ticker",
    "run_backtest_for_ticker",
    "save_markdown_report",
]
