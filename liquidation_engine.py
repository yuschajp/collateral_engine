"""
Liquidation engine: cure-deadline tracking for margin calls, and forced
liquidation of collateral when a call goes uncured.

Liquidation applies a discount on top of the normal haircut to reflect
fire-sale pricing impact, and prioritizes the most liquid assets first
(lowest liquidation discount) to minimize execution risk and market
impact -- the opposite priority from cheapest-to-deliver, which
preserves liquid assets when posting collateral voluntarily rather than
force-selling it under time pressure.
"""


def cure_check(shortfall: float, additional_posted_value: float, within_deadline: bool) -> dict:
    """Check whether a margin call has been cured.

    additional_posted_value should already be haircut-adjusted, the same
    convention used everywhere else in this engine. A call only counts
    as cured if both the value requirement is met and it happened within
    the deadline -- posting enough collateral a day late still triggers
    liquidation.
    """
    remaining_shortfall = max(shortfall - additional_posted_value, 0.0)
    cured = remaining_shortfall <= 0 and within_deadline
    return {
        "remaining_shortfall": remaining_shortfall,
        "within_deadline": within_deadline,
        "cured": cured,
        "liquidation_required": not cured,
    }


def liquidation_value(asset, liquidation_discount_pct: float) -> float:
    """Net proceeds from force-selling one asset: the normal haircut
    value, further reduced by a liquidation discount reflecting
    fire-sale pricing impact."""
    return asset.haircut_value * (1 - liquidation_discount_pct)


def trigger_liquidation(shortfall: float, collateral: list, liquidation_discounts: dict) -> dict:
    """Force-liquidate collateral to cover an uncured shortfall.

    liquidation_discounts: {asset_type: discount_pct}, e.g. cash needs no
    discount since it's already liquid, government bonds trade with a
    small discount, equities with a larger one. Liquidates the most
    liquid (lowest discount) assets first.
    """
    ordered = sorted(collateral, key=lambda a: liquidation_discounts.get(a.asset_type, 1.0))

    liquidated = []
    proceeds = 0.0
    for asset in ordered:
        if proceeds >= shortfall:
            break
        discount = liquidation_discounts.get(asset.asset_type, 0.0)
        net = liquidation_value(asset, discount)
        liquidated.append({"asset": asset, "liquidation_discount": discount, "net_proceeds": net})
        proceeds += net

    residual_shortfall = max(shortfall - proceeds, 0.0)
    return {
        "liquidated": liquidated,
        "total_proceeds": proceeds,
        "residual_shortfall": residual_shortfall,
        "fully_covered": residual_shortfall <= 0,
    }
