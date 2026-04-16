from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Sequence

DEFAULT_LOOKBACK_YEARS = 3
DEFAULT_WINDOW_SIZES = (60, 90, 120, 180)
DEFAULT_MAX_WIDTH_RATIO = 0.30
DEFAULT_TOUCH_BAND_RATIO = 0.10
DEFAULT_MIN_TOUCHES_PER_SIDE = 2


@dataclass(frozen=True)
class PriceBar:
    date: date
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class RangeEvaluation:
    lookback_days: int
    box_low: float
    box_high: float
    width_ratio: float
    touches_top: int
    touches_bottom: int
    is_valid_box: bool


@dataclass(frozen=True)
class BoxRangeResult:
    ticker: str
    resolved_ticker: str
    as_of_date: str
    current_price: float
    box_low: float
    box_high: float
    position_ratio: float
    zone_label: str
    status: str
    hint: str
    width_ratio: float
    lookback_days: int
    touches_top: int
    touches_bottom: int
    is_valid_box: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def normalize_ticker(ticker: str, market: str = "auto") -> str:
    raw = ticker.strip().upper()
    if not raw:
        raise ValueError("심볼을 입력해주세요.")

    if market not in {"auto", "us", "kospi", "kosdaq"}:
        raise ValueError("market은 auto, us, kospi, kosdaq 중 하나여야 합니다.")

    if market in {"auto", "us"}:
        return raw

    if raw.endswith((".KS", ".KQ")):
        return raw

    suffix = ".KS" if market == "kospi" else ".KQ"
    return f"{raw}{suffix}"


def fetch_price_history(
    ticker: str,
    lookback_years: int = DEFAULT_LOOKBACK_YEARS,
) -> list[PriceBar]:
    if lookback_years <= 0:
        raise ValueError("lookback_years는 1 이상이어야 합니다.")

    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError(
            "yfinance가 설치되지 않았습니다. `pip install -r chilmyeonjo/strategies/requirements.txt`를 실행하세요."
        ) from exc

    history = yf.Ticker(ticker).history(
        period=f"{lookback_years}y",
        interval="1d",
        auto_adjust=False,
    )
    if history.empty:
        raise ValueError(f"{ticker} 시세를 불러오지 못했습니다.")

    bars: list[PriceBar] = []
    for index, row in history.iterrows():
        high = _coerce_float(row["High"])
        low = _coerce_float(row["Low"])
        close = _coerce_float(row["Close"])
        if high is None or low is None or close is None:
            continue
        if high < low:
            continue
        bars.append(PriceBar(date=index.date(), high=high, low=low, close=close))

    minimum_required = min(DEFAULT_WINDOW_SIZES) + 1
    if len(bars) < minimum_required:
        raise ValueError(
            f"{ticker} 데이터가 충분하지 않습니다. 최소 {minimum_required}거래일이 필요합니다."
        )
    return bars


def analyze_box_range(
    ticker: str,
    bars: Sequence[PriceBar],
    resolved_ticker: str | None = None,
    window_sizes: Sequence[int] = DEFAULT_WINDOW_SIZES,
    max_width_ratio: float = DEFAULT_MAX_WIDTH_RATIO,
    touch_band_ratio: float = DEFAULT_TOUCH_BAND_RATIO,
    min_touches_per_side: int = DEFAULT_MIN_TOUCHES_PER_SIDE,
) -> BoxRangeResult:
    if len(bars) < min(window_sizes) + 1:
        raise ValueError("박스권 분석에 필요한 가격 데이터가 부족합니다.")

    resolved = resolved_ticker or ticker
    latest_bar = bars[-1]
    evaluation = select_recent_range(
        bars=bars,
        window_sizes=window_sizes,
        max_width_ratio=max_width_ratio,
        touch_band_ratio=touch_band_ratio,
        min_touches_per_side=min_touches_per_side,
    )
    position_ratio = calculate_position_ratio(
        current_price=latest_bar.close,
        box_low=evaluation.box_low,
        box_high=evaluation.box_high,
    )
    status, zone_label = classify_status(
        current_price=latest_bar.close,
        box_low=evaluation.box_low,
        box_high=evaluation.box_high,
        is_valid_box=evaluation.is_valid_box,
    )
    hint = build_hint(
        status=status,
        zone_label=zone_label,
        is_valid_box=evaluation.is_valid_box,
    )

    return BoxRangeResult(
        ticker=ticker,
        resolved_ticker=resolved,
        as_of_date=latest_bar.date.isoformat(),
        current_price=round(latest_bar.close, 2),
        box_low=round(evaluation.box_low, 2),
        box_high=round(evaluation.box_high, 2),
        position_ratio=round(position_ratio, 4),
        zone_label=zone_label,
        status=status,
        hint=hint,
        width_ratio=round(evaluation.width_ratio, 4),
        lookback_days=evaluation.lookback_days,
        touches_top=evaluation.touches_top,
        touches_bottom=evaluation.touches_bottom,
        is_valid_box=evaluation.is_valid_box,
    )


def select_recent_range(
    bars: Sequence[PriceBar],
    window_sizes: Sequence[int] = DEFAULT_WINDOW_SIZES,
    max_width_ratio: float = DEFAULT_MAX_WIDTH_RATIO,
    touch_band_ratio: float = DEFAULT_TOUCH_BAND_RATIO,
    min_touches_per_side: int = DEFAULT_MIN_TOUCHES_PER_SIDE,
) -> RangeEvaluation:
    ordered_windows = sorted(set(window_sizes))
    evaluations: list[RangeEvaluation] = []

    for window in ordered_windows:
        if len(bars) <= window:
            continue
        reference_bars = bars[-(window + 1) : -1]
        evaluation = evaluate_window(
            reference_bars=reference_bars,
            lookback_days=window,
            max_width_ratio=max_width_ratio,
            touch_band_ratio=touch_band_ratio,
            min_touches_per_side=min_touches_per_side,
        )
        evaluations.append(evaluation)

    if not evaluations:
        raise ValueError("박스권을 평가할 수 있는 구간이 없습니다.")

    for evaluation in evaluations:
        if evaluation.is_valid_box:
            return evaluation
    return evaluations[0]


def evaluate_window(
    reference_bars: Sequence[PriceBar],
    lookback_days: int,
    max_width_ratio: float = DEFAULT_MAX_WIDTH_RATIO,
    touch_band_ratio: float = DEFAULT_TOUCH_BAND_RATIO,
    min_touches_per_side: int = DEFAULT_MIN_TOUCHES_PER_SIDE,
) -> RangeEvaluation:
    if not reference_bars:
        raise ValueError("평가할 기준 구간이 비어 있습니다.")

    box_high = max(bar.high for bar in reference_bars)
    box_low = min(bar.low for bar in reference_bars)
    if box_high <= box_low:
        raise ValueError("가격 범위를 계산할 수 없습니다.")

    midpoint = (box_high + box_low) / 2
    width_ratio = (box_high - box_low) / midpoint
    touch_band = (box_high - box_low) * touch_band_ratio

    touches_top = sum(1 for bar in reference_bars if bar.high >= box_high - touch_band)
    touches_bottom = sum(
        1 for bar in reference_bars if bar.low <= box_low + touch_band
    )
    is_valid_box = (
        width_ratio <= max_width_ratio
        and touches_top >= min_touches_per_side
        and touches_bottom >= min_touches_per_side
    )

    return RangeEvaluation(
        lookback_days=lookback_days,
        box_low=box_low,
        box_high=box_high,
        width_ratio=width_ratio,
        touches_top=touches_top,
        touches_bottom=touches_bottom,
        is_valid_box=is_valid_box,
    )


def calculate_position_ratio(current_price: float, box_low: float, box_high: float) -> float:
    if box_high <= box_low:
        raise ValueError("박스 상단은 하단보다 커야 합니다.")
    return (current_price - box_low) / (box_high - box_low)


def classify_status(
    current_price: float,
    box_low: float,
    box_high: float,
    is_valid_box: bool,
) -> tuple[str, str]:
    ratio = calculate_position_ratio(current_price, box_low, box_high)
    if not is_valid_box:
        return "박스권 아님", classify_zone(ratio)
    if current_price > box_high:
        return "상단 돌파", "상단 돌파"
    if current_price < box_low:
        return "하단 이탈", "하단 이탈"
    return "박스 내부", classify_zone(ratio)


def classify_zone(position_ratio: float) -> str:
    if position_ratio < 0:
        return "하단 아래"
    if position_ratio <= 0.20:
        return "하단 근처"
    if position_ratio <= 0.40:
        return "하단-중단"
    if position_ratio <= 0.60:
        return "중단"
    if position_ratio <= 0.80:
        return "중단-상단"
    if position_ratio <= 1.00:
        return "상단 근처"
    return "상단 위"


def build_hint(status: str, zone_label: str, is_valid_box: bool) -> str:
    if not is_valid_box:
        return (
            f"현재 최근 범위 기준 {zone_label}에 있지만, 변동폭이 크거나 지지/저항 반복이 "
            "충분하지 않아 깔끔한 박스권으로 보기는 어렵습니다."
        )
    if status == "상단 돌파":
        return (
            "현재 박스 상단을 돌파한 상태입니다. 박스 매매만 믿고 추격하기보다 "
            "돌파 지속 여부와 거래량 확인이 필요한 구간입니다."
        )
    if status == "하단 이탈":
        return (
            "현재 박스 하단을 이탈한 상태입니다. 박스 하단 방어 실패 가능성을 열어 두고 "
            "재진입보다 안정화 확인이 먼저인 구간입니다."
        )
    if zone_label == "하단 근처":
        return "현재 박스 하단 근처로, 분할매수 검토 구간에 가깝습니다."
    if zone_label == "하단-중단":
        return "현재 하단과 중단 사이로, 분할 접근과 반등 확인을 함께 볼 구간입니다."
    if zone_label == "중단":
        return "현재 박스 중단 부근으로, 신규 진입보다 관찰 비중이 높은 구간입니다."
    if zone_label == "중단-상단":
        return "현재 중단과 상단 사이로, 보유 관찰 또는 일부 차익 준비를 볼 수 있는 구간입니다."
    return "현재 박스 상단 근처로, 분할매도 검토 구간에 가깝습니다."


def format_text_result(result: BoxRangeResult) -> str:
    lines = [
        f"심볼: {result.ticker}",
        f"조회 심볼: {result.resolved_ticker}",
        f"기준일: {result.as_of_date}",
        f"현재가: {result.current_price:.2f}",
        f"박스 하단: {result.box_low:.2f}",
        f"박스 상단: {result.box_high:.2f}",
        f"최근 박스 판단 구간: {result.lookback_days}거래일",
        f"박스 폭 비율: {result.width_ratio * 100:.2f}%",
        f"현재 위치 비율: {result.position_ratio * 100:.2f}%",
        f"상단 접촉 횟수: {result.touches_top}",
        f"하단 접촉 횟수: {result.touches_bottom}",
        f"판정: {result.status}",
        f"현재 구간: {result.zone_label}",
        f"해석: {result.hint}",
    ]
    return "\n".join(lines)


def _coerce_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return number
