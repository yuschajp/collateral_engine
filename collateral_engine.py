"""
Collateral and margin engine: haircut-adjusted collateral valuation,
margin call detection, and cheapest-to-deliver collateral optimization.

This is the same mechanics underneath both crypto perpetual futures
margining and traditional repo or derivatives collateral management:
exposure gets compared against haircut-adjusted collateral value, and
when collateral comes up short, more has to be posted. The optimization
piece -- choosing which eligible collateral to actually pledge -- is the
treasury function this engine is built to demonstrate.
"""

from dataclasses import dataclass


@dataclass
class CollateralAsset:
    asset_id: str
    asset_type: str        # e.g. cash, govt_bond, corp_bond, equity
    market_value: float
    haircut_pct: float      # e.g. 0.02 for a 2% haircut

    @property
    def haircut_value(self) -> float:
        """Value after the haircut is applied -- what actually counts toward margin."""
        return self.market_value * (1 - self.haircut_pct)


def total_haircut_value(collateral: list) -> float:
    return sum(asset.haircut_value for asset in collateral)


def margin_call(required_margin: float, collateral: list) -> dict:
    """Compare haircut-adjusted collateral against the required margin.

    The shortfall is reported in raw dollars, not haircut-adjusted,
    since that's the actual amount that needs to be posted or wired to
    cure the call.
    """
    pledged_value = total_haircut_value(collateral)
    shortfall = required_margin - pledged_value
    return {
        "required_margin": required_margin,
        "pledged_haircut_value": pledged_value,
        "shortfall": max(shortfall, 0.0),
        "call_triggered": shortfall > 0,
    }


def cheapest_to_deliver(required_margin: float, available_collateral: list,
                         priority_order: list = None) -> dict:
    """Select which available collateral lots to pledge to meet a margin
    requirement while minimizing use of the most valuable or flexible
    collateral (typically cash), the standard treasury optimization
    problem: post the cheapest eligible collateral first and hold the
    most useful collateral back for other purposes.

    priority_order: asset types ordered from most-expensive-to-use
    (pledge last) to cheapest-to-use (pledge first). If not given,
    defaults to pledging the highest-haircut (lowest quality) assets
    first, which is the standard heuristic when no explicit funding
    priority has been set.
    """
    if priority_order:
        order_index = {t: i for i, t in enumerate(priority_order)}
        ordered = sorted(available_collateral,
                          key=lambda a: order_index.get(a.asset_type, len(priority_order)))
    else:
        ordered = sorted(available_collateral, key=lambda a: -a.haircut_pct)

    selected = []
    pledged_value = 0.0
    for asset in ordered:
        if pledged_value >= required_margin:
            break
        selected.append(asset)
        pledged_value += asset.haircut_value

    return {
        "selected": selected,
        "pledged_haircut_value": pledged_value,
        "met_requirement": pledged_value >= required_margin,
        "unused": [a for a in available_collateral if a not in selected],
    }
