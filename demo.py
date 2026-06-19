"""
Demo: a margin call on currently pledged collateral, then cheapest-to-
deliver optimization showing how to cover the requirement while
preserving cash for other uses.

Run with: python3 demo.py
"""

from collateral_engine import CollateralAsset, margin_call, cheapest_to_deliver


def main():
    required_margin = 1_000_000

    pledged = [
        CollateralAsset("C1", "cash", 300_000, 0.00),
        CollateralAsset("C2", "govt_bond", 500_000, 0.02),
    ]

    result = margin_call(required_margin, pledged)
    print("Margin call check on currently pledged collateral:")
    print(f"  Required margin: ${result['required_margin']:,.2f}")
    print(f"  Pledged (haircut-adjusted) value: ${result['pledged_haircut_value']:,.2f}")
    print(f"  Shortfall: ${result['shortfall']:,.2f}")
    print(f"  Margin call triggered: {result['call_triggered']}")

    print()
    print("Cheapest-to-deliver optimization to cover the full requirement:")
    available = [
        CollateralAsset("C1", "cash", 300_000, 0.00),
        CollateralAsset("C2", "govt_bond", 500_000, 0.02),
        CollateralAsset("C3", "corp_bond", 400_000, 0.08),
        CollateralAsset("C4", "equity", 300_000, 0.15),
    ]
    optimized = cheapest_to_deliver(required_margin, available)
    for asset in optimized["selected"]:
        print(f"  Pledge {asset.asset_id} ({asset.asset_type}): market value ${asset.market_value:,.2f}, "
              f"haircut {asset.haircut_pct:.0%}, counts as ${asset.haircut_value:,.2f}")
    print(f"  Total pledged (haircut-adjusted): ${optimized['pledged_haircut_value']:,.2f}")
    print(f"  Requirement met: {optimized['met_requirement']}")
    cash_preserved = [a.asset_id for a in optimized["unused"] if a.asset_type == "cash"]
    print(f"  Cash preserved (not pledged): {cash_preserved}")


if __name__ == "__main__":
    main()
