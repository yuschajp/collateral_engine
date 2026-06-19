"""
Demo: a margin call cure-deadline scenario (cured vs not cured), and
forced liquidation when a call goes uncured, prioritizing the most
liquid assets first.

Run with: python3 liquidation_demo.py
"""

from collateral_engine import CollateralAsset
from liquidation_engine import cure_check, trigger_liquidation


def main():
    available = [
        CollateralAsset("C1", "cash", 300_000, 0.00),
        CollateralAsset("C2", "govt_bond", 500_000, 0.02),
        CollateralAsset("C3", "corp_bond", 400_000, 0.08),
        CollateralAsset("C4", "equity", 300_000, 0.15),
    ]

    shortfall = 900_000
    print(f"Margin call shortfall: ${shortfall:,.2f}\n")

    print("Scenario A -- additional collateral posted in time:")
    cured = cure_check(shortfall, additional_posted_value=950_000, within_deadline=True)
    print(f"  Remaining shortfall: ${cured['remaining_shortfall']:,.2f}")
    print(f"  Cured: {cured['cured']}")
    print(f"  Liquidation required: {cured['liquidation_required']}\n")

    print("Scenario B -- deadline missed, nothing posted in time:")
    uncured = cure_check(shortfall, additional_posted_value=0, within_deadline=False)
    print(f"  Remaining shortfall: ${uncured['remaining_shortfall']:,.2f}")
    print(f"  Cured: {uncured['cured']}")
    print(f"  Liquidation required: {uncured['liquidation_required']}\n")

    print("Triggering liquidation, most liquid assets first:")
    liquidation_discounts = {"cash": 0.00, "govt_bond": 0.01, "corp_bond": 0.04, "equity": 0.10}
    result = trigger_liquidation(shortfall, available, liquidation_discounts)
    for item in result["liquidated"]:
        a = item["asset"]
        print(f"  Liquidate {a.asset_id} ({a.asset_type}): haircut value ${a.haircut_value:,.2f}, "
              f"liquidation discount {item['liquidation_discount']:.0%}, "
              f"net proceeds ${item['net_proceeds']:,.2f}")
    print(f"  Total proceeds: ${result['total_proceeds']:,.2f}")
    print(f"  Residual shortfall: ${result['residual_shortfall']:,.2f}")
    print(f"  Fully covered: {result['fully_covered']}")


if __name__ == "__main__":
    main()
