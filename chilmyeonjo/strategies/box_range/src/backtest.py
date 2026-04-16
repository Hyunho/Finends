from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Sequence

from chilmyeonjo.strategies.box_range.src.analysis import (
    DEFAULT_LOOKBACK_YEARS,
    DEFAULT_WINDOW_SIZES,
    BoxRangeResult,
    PriceBar,
    analyze_box_range,
    fetch_price_history,
    normalize_ticker,
)

DEFAULT_BACKTEST_TICKERS = ("TSLA", "263750.KQ")
DEFAULT_ROUND_TRIP_COST = 0.003
DEFAULT_REPORT_DIR = "strategies/box_range"
PACKAGE_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class BacktestTrade:
    entry_signal_date: str
    entry_fill_date: str
    entry_price: float
    entry_reason: str
    exit_signal_date: str
    exit_fill_date: str
    exit_price: float
    exit_reason: str
    gross_return: float
    net_return: float
    holding_days: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class BacktestResult:
    ticker: str
    resolved_ticker: str
    period_start: str
    period_end: str
    strategy_return: float
    buy_and_hold_return: float
    excess_return: float
    max_drawdown: float
    trade_count: int
    win_rate: float
    average_holding_days: float
    trades: list[BacktestTrade]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["trades"] = [trade.to_dict() for trade in self.trades]
        return data


@dataclass(frozen=True)
class _ClosedTrade:
    entry_signal_date: str
    entry_fill_date: str
    entry_fill_index: int
    entry_price: float
    entry_reason: str
    exit_signal_date: str
    exit_fill_date: str
    exit_fill_index: int
    exit_price: float
    exit_reason: str
    gross_return: float
    net_return: float
    holding_days: int

    def to_public(self) -> BacktestTrade:
        return BacktestTrade(
            entry_signal_date=self.entry_signal_date,
            entry_fill_date=self.entry_fill_date,
            entry_price=round(self.entry_price, 2),
            entry_reason=self.entry_reason,
            exit_signal_date=self.exit_signal_date,
            exit_fill_date=self.exit_fill_date,
            exit_price=round(self.exit_price, 2),
            exit_reason=self.exit_reason,
            gross_return=round(self.gross_return, 4),
            net_return=round(self.net_return, 4),
            holding_days=self.holding_days,
        )


@dataclass
class _OpenPosition:
    entry_signal_date: date
    entry_fill_index: int
    entry_price: float
    entry_reason: str


def run_backtest_for_ticker(
    ticker: str,
    market: str = "auto",
    lookback_years: int = DEFAULT_LOOKBACK_YEARS,
    round_trip_cost: float = DEFAULT_ROUND_TRIP_COST,
) -> BacktestResult:
    resolved_ticker = normalize_ticker(ticker, market=market)
    bars = fetch_price_history(resolved_ticker, lookback_years=lookback_years)
    return run_backtest_from_bars(
        ticker=ticker,
        resolved_ticker=resolved_ticker,
        bars=bars,
        round_trip_cost=round_trip_cost,
    )


def run_backtest_from_bars(
    ticker: str,
    resolved_ticker: str,
    bars: Sequence[PriceBar],
    round_trip_cost: float = DEFAULT_ROUND_TRIP_COST,
) -> BacktestResult:
    if round_trip_cost < 0 or round_trip_cost >= 1:
        raise ValueError("round_trip_cost는 0 이상 1 미만이어야 합니다.")

    signal_start_index = min(DEFAULT_WINDOW_SIZES)
    first_fill_index = signal_start_index + 1
    if len(bars) <= first_fill_index:
        raise ValueError("백테스트를 수행하기에 가격 데이터가 부족합니다.")

    closed_trades = _simulate_trades(
        ticker=ticker,
        resolved_ticker=resolved_ticker,
        bars=bars,
        round_trip_cost=round_trip_cost,
        signal_start_index=signal_start_index,
    )
    equity_curve = build_equity_curve(
        bars=bars,
        closed_trades=closed_trades,
        start_index=first_fill_index,
        round_trip_cost=round_trip_cost,
    )
    strategy_return = equity_curve[-1] - 1.0
    buy_and_hold_return = calculate_buy_and_hold_return(
        bars=bars,
        start_index=first_fill_index,
        round_trip_cost=round_trip_cost,
    )
    max_drawdown = calculate_max_drawdown(equity_curve)
    public_trades = [trade.to_public() for trade in closed_trades]
    trade_count = len(public_trades)
    winning_trades = sum(1 for trade in public_trades if trade.net_return > 0)
    average_holding_days = (
        sum(trade.holding_days for trade in public_trades) / trade_count
        if trade_count
        else 0.0
    )

    return BacktestResult(
        ticker=ticker,
        resolved_ticker=resolved_ticker,
        period_start=bars[first_fill_index].date.isoformat(),
        period_end=bars[-1].date.isoformat(),
        strategy_return=round(strategy_return, 4),
        buy_and_hold_return=round(buy_and_hold_return, 4),
        excess_return=round(strategy_return - buy_and_hold_return, 4),
        max_drawdown=round(max_drawdown, 4),
        trade_count=trade_count,
        win_rate=round(winning_trades / trade_count, 4) if trade_count else 0.0,
        average_holding_days=round(average_holding_days, 2),
        trades=public_trades,
    )


def build_equity_curve(
    bars: Sequence[PriceBar],
    closed_trades: Sequence[_ClosedTrade],
    start_index: int,
    round_trip_cost: float,
) -> list[float]:
    half_cost = round_trip_cost / 2
    cash = 1.0
    shares = 0.0
    equity_curve: list[float] = []
    active_trade: _ClosedTrade | None = None
    next_trade_index = 0

    for index in range(start_index, len(bars)):
        if active_trade is None and next_trade_index < len(closed_trades):
            candidate = closed_trades[next_trade_index]
            if index == candidate.entry_fill_index:
                shares = cash * (1 - half_cost) / candidate.entry_price
                cash = 0.0
                active_trade = candidate

        if active_trade is not None and index == active_trade.exit_fill_index:
            cash = shares * active_trade.exit_price * (1 - half_cost)
            shares = 0.0
            active_trade = None
            next_trade_index += 1

        equity = cash if active_trade is None else shares * bars[index].close
        equity_curve.append(equity)

    return equity_curve


def calculate_buy_and_hold_return(
    bars: Sequence[PriceBar],
    start_index: int,
    round_trip_cost: float,
) -> float:
    half_cost = round_trip_cost / 2
    entry_price = bars[start_index].close
    exit_price = bars[-1].close
    return (exit_price * (1 - half_cost)) / (entry_price * (1 + half_cost)) - 1


def calculate_max_drawdown(equity_curve: Sequence[float]) -> float:
    peak = equity_curve[0]
    max_drawdown = 0.0
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        drawdown = (peak - equity) / peak if peak else 0.0
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    return max_drawdown


def build_markdown_report(
    results: Sequence[BacktestResult],
    lookback_years: int = DEFAULT_LOOKBACK_YEARS,
    round_trip_cost: float = DEFAULT_ROUND_TRIP_COST,
    generated_on: date | None = None,
) -> str:
    today = generated_on or date.today()
    lines = [
        "# 박스권 전략 백테스트 결과",
        "",
        f"- 생성일: {today.isoformat()}",
        f"- 대상 종목: {', '.join(result.ticker for result in results)}",
        f"- 테스트 기간: 최근 {lookback_years}년",
        f"- 거래 규칙: `박스 내부 + 하단 근처`에서 진입, `상단 근처`에서 청산",
        f"- 체결 기준: 신호 다음 거래일 종가",
        f"- 거래 비용: 왕복 {round_trip_cost * 100:.2f}%",
        f"- 비교 기준: 같은 기간 단순 보유",
        "",
        "## 종목별 요약",
        "",
        "| 종목 | 기간 | 전략 수익률 | 단순 보유 | 초과수익 | 최대낙폭 | 거래 수 | 승률 | 평균 보유일 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for result in results:
        lines.append(
            "| {ticker} | {start} ~ {end} | {strategy} | {hold} | {excess} | {mdd} | {trades} | {win_rate} | {holding} |".format(
                ticker=result.ticker,
                start=result.period_start,
                end=result.period_end,
                strategy=format_pct(result.strategy_return),
                hold=format_pct(result.buy_and_hold_return),
                excess=format_pct(result.excess_return),
                mdd=format_pct(result.max_drawdown),
                trades=result.trade_count,
                win_rate=format_pct(result.win_rate),
                holding=f"{result.average_holding_days:.2f}",
            )
        )

    for result in results:
        lines.extend(
            [
                "",
                f"## {result.ticker}",
                "",
                f"- 조회 심볼: `{result.resolved_ticker}`",
                f"- 테스트 기간: `{result.period_start}` ~ `{result.period_end}`",
                f"- 전략 수익률: {format_pct(result.strategy_return)}",
                f"- 단순 보유 수익률: {format_pct(result.buy_and_hold_return)}",
                f"- 초과수익: {format_pct(result.excess_return)}",
                f"- 최대낙폭: {format_pct(result.max_drawdown)}",
                f"- 거래 수: {result.trade_count}",
                f"- 승률: {format_pct(result.win_rate)}",
                f"- 평균 보유일: {result.average_holding_days:.2f} 거래일",
                f"- 해석: {build_result_comment(result)}",
                "",
                "### 거래 내역",
                "",
            ]
        )
        if not result.trades:
            lines.append("거래가 발생하지 않았습니다.")
            continue

        lines.extend(
            [
                "| 진입 신호일 | 진입 체결일 | 진입가 | 청산 신호일 | 청산 체결일 | 청산가 | 순수익률 | 보유일 | 청산 사유 |",
                "| --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- |",
            ]
        )
        for trade in result.trades:
            lines.append(
                "| {entry_signal} | {entry_fill} | {entry_price:.2f} | {exit_signal} | {exit_fill} | {exit_price:.2f} | {net} | {days} | {reason} |".format(
                    entry_signal=trade.entry_signal_date,
                    entry_fill=trade.entry_fill_date,
                    entry_price=trade.entry_price,
                    exit_signal=trade.exit_signal_date,
                    exit_fill=trade.exit_fill_date,
                    exit_price=trade.exit_price,
                    net=format_pct(trade.net_return),
                    days=trade.holding_days,
                    reason=trade.exit_reason,
                )
            )

    lines.extend(
        [
            "",
            "## 해석 주의",
            "",
            "- 이 결과는 일봉 종가 기준 단순 규칙 백테스트입니다.",
            "- 장중 체결, 거래량, 슬리피지 변화, 세금, 뉴스 이벤트는 반영하지 않았습니다.",
            "- `하단 이탈` 손절 규칙은 넣지 않았으므로, 박스 하단 붕괴 시 손실이 커질 수 있습니다.",
        ]
    )
    return "\n".join(lines) + "\n"


def save_markdown_report(markdown: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return path


def default_report_path(base_dir: Path | None = None, generated_on: date | None = None) -> Path:
    root = base_dir or PACKAGE_ROOT
    today = generated_on or date.today()
    return root / DEFAULT_REPORT_DIR / f"{today.isoformat()}-box-range-backtest.md"


def format_backtest_summary(results: Sequence[BacktestResult]) -> str:
    lines = []
    for result in results:
        lines.extend(
            [
                f"심볼: {result.ticker}",
                f"조회 심볼: {result.resolved_ticker}",
                f"기간: {result.period_start} ~ {result.period_end}",
                f"전략 수익률: {format_pct(result.strategy_return)}",
                f"단순 보유 수익률: {format_pct(result.buy_and_hold_return)}",
                f"초과수익: {format_pct(result.excess_return)}",
                f"최대낙폭: {format_pct(result.max_drawdown)}",
                f"거래 수: {result.trade_count}",
                f"승률: {format_pct(result.win_rate)}",
                f"평균 보유일: {result.average_holding_days:.2f} 거래일",
                f"해석: {build_result_comment(result)}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def build_result_comment(result: BacktestResult) -> str:
    if result.trade_count == 0:
        return "최근 3년 동안 이 규칙으로는 진입 기회가 없었습니다."
    if result.excess_return > 0:
        return "단순 보유보다 성과가 좋았지만, 거래 수와 최대낙폭을 함께 봐야 합니다."
    if result.excess_return < 0:
        return "단순 보유보다 성과가 낮아, 박스권 규칙만으로는 기회를 놓쳤을 가능성이 큽니다."
    return "전략 수익률과 단순 보유 수익률이 거의 비슷했습니다."


def format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def is_entry_signal(result: BoxRangeResult) -> bool:
    return result.status == "박스 내부" and result.zone_label == "하단 근처"


def is_exit_signal(result: BoxRangeResult) -> bool:
    return result.status == "박스 내부" and result.zone_label == "상단 근처"


def _simulate_trades(
    ticker: str,
    resolved_ticker: str,
    bars: Sequence[PriceBar],
    round_trip_cost: float,
    signal_start_index: int,
) -> list[_ClosedTrade]:
    open_position: _OpenPosition | None = None
    closed_trades: list[_ClosedTrade] = []

    for signal_index in range(signal_start_index, len(bars) - 1):
        signal = analyze_box_range(
            ticker=ticker,
            resolved_ticker=resolved_ticker,
            bars=bars[: signal_index + 1],
        )
        fill_index = signal_index + 1
        if open_position is None:
            if fill_index < len(bars) - 1 and is_entry_signal(signal):
                open_position = _OpenPosition(
                    entry_signal_date=bars[signal_index].date,
                    entry_fill_index=fill_index,
                    entry_price=bars[fill_index].close,
                    entry_reason="박스 내부 + 하단 근처",
                )
            continue

        if fill_index <= open_position.entry_fill_index:
            continue
        if is_exit_signal(signal):
            closed_trades.append(
                _close_position(
                    open_position=open_position,
                    bars=bars,
                    exit_signal_date=bars[signal_index].date,
                    exit_fill_index=fill_index,
                    exit_reason="상단 근처 도달",
                    round_trip_cost=round_trip_cost,
                )
            )
            open_position = None

    if open_position is not None and len(bars) - 1 > open_position.entry_fill_index:
        closed_trades.append(
            _close_position(
                open_position=open_position,
                bars=bars,
                exit_signal_date=bars[-1].date,
                exit_fill_index=len(bars) - 1,
                exit_reason="백테스트 종료 정리",
                round_trip_cost=round_trip_cost,
            )
        )

    return closed_trades


def _close_position(
    open_position: _OpenPosition,
    bars: Sequence[PriceBar],
    exit_signal_date: date,
    exit_fill_index: int,
    exit_reason: str,
    round_trip_cost: float,
) -> _ClosedTrade:
    exit_price = bars[exit_fill_index].close
    gross_return = exit_price / open_position.entry_price - 1
    half_cost = round_trip_cost / 2
    net_return = (exit_price * (1 - half_cost)) / (
        open_position.entry_price * (1 + half_cost)
    ) - 1

    return _ClosedTrade(
        entry_signal_date=open_position.entry_signal_date.isoformat(),
        entry_fill_date=bars[open_position.entry_fill_index].date.isoformat(),
        entry_fill_index=open_position.entry_fill_index,
        entry_price=open_position.entry_price,
        entry_reason=open_position.entry_reason,
        exit_signal_date=exit_signal_date.isoformat(),
        exit_fill_date=bars[exit_fill_index].date.isoformat(),
        exit_fill_index=exit_fill_index,
        exit_price=exit_price,
        exit_reason=exit_reason,
        gross_return=gross_return,
        net_return=net_return,
        holding_days=exit_fill_index - open_position.entry_fill_index,
    )
