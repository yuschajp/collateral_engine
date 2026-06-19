"""
Demo: perpetual futures funding rate mechanics, then a multi-period
funding accrual that erodes account equity, tied back into the margin
call check from collateral_engine.py to show how funding payments alone
can trigger a margin call over time.

Run with: python3 funding_demo.py
"""

from collateral_engine import CollateralAsset, margin_call
from funding_engine import premium_rate, funding_rate, funding_payment


def main():
    mark_price, index_price = 65_200, 65_000
    interest_rate = 0.0001

    premium = premium_rate(mark_price, index_price)
    rate = funding_rate(mark_price, index_price, interest_rate)
    print(f"Mark price: ${mark_price:,.2f}   Index price: ${index_price:,.2f}")
    print(f"Premium rate: {premium:.4%}")
    print(f"Funding rate (this interval): {rate:.4%}\n")

    position_notional = 500_000
    is_long = True
    payment = funding_payment(position_notional, rate, is_long)
    print(f"Long position notional: ${position_notional:,.2f}")
    direction = "pays" if payment < 0 else "receives"
    print(f"Funding payment this interval: ${payment:,.2f} ({direction})\n")

    print("Cumulative funding over 9 intervals (3 days at 8h funding) with a persistent premium:")
    account_equity = 50_000
    for i in range(1, 10):
        account_equity += funding_payment(position_notional, rate, is_long)
        print(f"  Interval {i}: equity = ${account_equity:,.2f}")

    print()
    print("Checking whether accumulated funding alone has triggered a margin call:")
    maintenance_margin = 40_000
    pledged = [CollateralAsset("EQUITY", "cash", account_equity, 0.00)]
    result = margin_call(maintenance_margin, pledged)
    print(f"  Maintenance margin required: ${result['required_margin']:,.2f}")
    print(f"  Current equity (haircut-adjusted): ${result['pledged_haircut_value']:,.2f}")
    print(f"  Shortfall: ${result['shortfall']:,.2f}")
    print(f"  Margin call triggered: {result['call_triggered']}")


if __name__ == "__main__":
    main()
