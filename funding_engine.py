"""
Perpetual futures funding rate mechanics.

A perpetual futures contract has no expiry, so funding payments are the
mechanism that keeps its price anchored to the underlying index: when
the perpetual trades above the index, longs pay shorts to push demand
back toward balance, and the reverse when it trades below. The same
mark-price-vs-index-price comparison sits right alongside the haircut and
margin logic elsewhere in this repo -- it's just another input that moves
account equity, the same way a margin call shortfall does.
"""


def premium_rate(mark_price: float, index_price: float) -> float:
    """How far the perpetual's mark price has drifted from the index,
    as a fraction of the index price."""
    return (mark_price - index_price) / index_price


def funding_rate(mark_price: float, index_price: float, interest_rate: float = 0.0001,
                  clamp_pct: float = 0.0005) -> float:
    """Funding rate for one funding interval (commonly every 8 hours).

    The interest rate component reflects the cost-of-carry difference
    between the two currencies in the pair, but it's clamped relative to
    the premium so it can only nudge the rate by a small, bounded amount
    rather than fully offsetting a large premium -- the premium itself,
    not the interest assumption, dominates when the perpetual has
    genuinely drifted from the index.
    """
    premium = premium_rate(mark_price, index_price)
    interest_component = interest_rate - premium
    clamped_interest = max(-clamp_pct, min(clamp_pct, interest_component))
    return premium + clamped_interest


def funding_payment(position_notional: float, rate: float, is_long: bool) -> float:
    """Funding cash flow for one position over one funding interval, from
    the position holder's perspective (negative means they pay, positive
    means they receive).

    A positive funding rate means the perpetual is trading rich to the
    index, so longs pay shorts. A negative rate flips that direction.
    """
    return -position_notional * rate if is_long else position_notional * rate
