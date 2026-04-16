from __future__ import annotations

from datetime import date, timedelta
import unittest

from chilmyeonjo.box_range.analysis import PriceBar
from chilmyeonjo.box_range.backtest import (
    build_markdown_report,
    run_backtest_from_bars,
)


def make_tradable_bars() -> list[PriceBar]:
    start = date(2026, 1, 1)
    bars: list[PriceBar] = []

    for index in range(60):
        current_date = start + timedelta(days=index)
        pattern = index % 10
        if pattern == 0:
            high, low, close = 121.0, 118.0, 120.0
        elif pattern == 5:
            high, low, close = 102.0, 99.0, 100.0
        else:
            base = 110.0 + float((index % 4) - 2)
            high, low, close = base + 1.0, base - 1.0, base
        bars.append(PriceBar(date=current_date, high=high, low=low, close=close))

    bars.append(PriceBar(date=start + timedelta(days=60), high=104.0, low=102.0, close=103.0))
    bars.append(PriceBar(date=start + timedelta(days=61), high=105.0, low=103.0, close=104.0))

    for index in range(62, 69):
        current_date = start + timedelta(days=index)
        base = 111.0 + float((index % 3) - 1)
        bars.append(PriceBar(date=current_date, high=base + 1.0, low=base - 1.0, close=base))

    bars.append(PriceBar(date=start + timedelta(days=69), high=120.0, low=118.0, close=119.0))
    bars.append(PriceBar(date=start + timedelta(days=70), high=119.0, low=117.0, close=118.0))
    bars.append(PriceBar(date=start + timedelta(days=71), high=112.0, low=110.0, close=111.0))
    return bars


def make_forced_exit_bars() -> list[PriceBar]:
    bars = make_tradable_bars()[:64]
    replacement_date = bars[-1].date
    bars[-1] = PriceBar(date=replacement_date, high=109.0, low=107.0, close=108.0)
    return bars


def make_no_trade_bars() -> list[PriceBar]:
    start = date(2026, 1, 1)
    bars: list[PriceBar] = []
    for index in range(75):
        current_date = start + timedelta(days=index)
        if index % 12 == 0:
            high, low, close = 150.0, 140.0, 148.0
        elif index % 12 == 6:
            high, low, close = 100.0, 90.0, 92.0
        else:
            base = 120.0 + float((index % 5) - 2)
            high, low, close = base + 4.0, base - 4.0, base
        bars.append(PriceBar(date=current_date, high=high, low=low, close=close))
    return bars


class BoxRangeBacktestTests(unittest.TestCase):
    def test_backtest_executes_single_trade(self) -> None:
        result = run_backtest_from_bars(
            ticker="TEST",
            resolved_ticker="TEST",
            bars=make_tradable_bars(),
        )

        self.assertEqual(result.trade_count, 1)
        self.assertGreater(result.strategy_return, 0)
        self.assertEqual(result.trades[0].exit_reason, "상단 근처 도달")

    def test_backtest_forces_exit_at_end(self) -> None:
        result = run_backtest_from_bars(
            ticker="TEST",
            resolved_ticker="TEST",
            bars=make_forced_exit_bars(),
        )

        self.assertEqual(result.trade_count, 1)
        self.assertEqual(result.trades[0].exit_reason, "백테스트 종료 정리")

    def test_backtest_handles_no_trade(self) -> None:
        result = run_backtest_from_bars(
            ticker="TEST",
            resolved_ticker="TEST",
            bars=make_no_trade_bars(),
        )

        self.assertEqual(result.trade_count, 0)
        self.assertEqual(result.strategy_return, 0.0)

    def test_markdown_report_contains_summary(self) -> None:
        result = run_backtest_from_bars(
            ticker="TEST",
            resolved_ticker="TEST",
            bars=make_tradable_bars(),
        )

        markdown = build_markdown_report([result])

        self.assertIn("# 박스권 전략 백테스트 결과", markdown)
        self.assertIn("## TEST", markdown)
        self.assertIn("### 거래 내역", markdown)


if __name__ == "__main__":
    unittest.main()
