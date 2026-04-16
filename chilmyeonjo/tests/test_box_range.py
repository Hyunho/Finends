from __future__ import annotations

from datetime import date, timedelta
import unittest

from chilmyeonjo.box_range.analysis import (
    analyze_box_range,
    normalize_ticker,
    PriceBar,
)


def make_box_bars(current_close: float) -> list[PriceBar]:
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

    bars.append(
        PriceBar(
            date=start + timedelta(days=60),
            high=max(current_close + 1.0, current_close),
            low=current_close - 1.0,
            close=current_close,
        )
    )
    return bars


def make_wide_range_bars(current_close: float) -> list[PriceBar]:
    start = date(2026, 1, 1)
    bars: list[PriceBar] = []

    for index in range(60):
        current_date = start + timedelta(days=index)
        if index % 12 == 0:
            high, low, close = 150.0, 140.0, 148.0
        elif index % 12 == 6:
            high, low, close = 100.0, 90.0, 92.0
        else:
            base = 118.0 + float((index % 6) - 3)
            high, low, close = base + 4.0, base - 4.0, base
        bars.append(PriceBar(date=current_date, high=high, low=low, close=close))

    bars.append(
        PriceBar(
            date=start + timedelta(days=60),
            high=current_close + 2.0,
            low=current_close - 2.0,
            close=current_close,
        )
    )
    return bars


class BoxRangeTests(unittest.TestCase):
    def test_normalize_ticker_for_kospi(self) -> None:
        self.assertEqual(normalize_ticker("005930", market="kospi"), "005930.KS")

    def test_detects_box_and_lower_zone(self) -> None:
        bars = make_box_bars(current_close=103.0)
        result = analyze_box_range(ticker="TEST", resolved_ticker="TEST", bars=bars)

        self.assertEqual(result.status, "박스 내부")
        self.assertEqual(result.zone_label, "하단 근처")
        self.assertTrue(result.is_valid_box)
        self.assertEqual(result.lookback_days, 60)

    def test_detects_breakout_against_prior_box(self) -> None:
        bars = make_box_bars(current_close=125.0)
        result = analyze_box_range(ticker="TEST", resolved_ticker="TEST", bars=bars)

        self.assertEqual(result.status, "상단 돌파")
        self.assertEqual(result.zone_label, "상단 돌파")

    def test_reports_not_a_box_when_range_is_too_wide(self) -> None:
        bars = make_wide_range_bars(current_close=118.0)
        result = analyze_box_range(ticker="TEST", resolved_ticker="TEST", bars=bars)

        self.assertEqual(result.status, "박스권 아님")
        self.assertFalse(result.is_valid_box)


if __name__ == "__main__":
    unittest.main()
