"""
Generates a static HTML dashboard from the collateral and margin engine:
a margin call, the cheapest-to-deliver collateral selection, a forced
liquidation scenario, and crypto perpetual funding accrual eroding
equity into a margin call, all on one page you open directly in a
browser, no server required.

Run with: python3 dashboard.py
Then open dashboard.html in any browser.
"""

import html

from collateral_engine import CollateralAsset, margin_call, cheapest_to_deliver
from liquidation_engine import trigger_liquidation
from funding_engine import funding_rate, funding_payment


def render_table(headers, rows):
    head = "".join(f"<th>{html.escape(str(h))}</th>" for h in headers)
    body = ""
    for row in rows:
        cells = "".join(f"<td>{html.escape('' if v is None else str(v))}</td>" for v in row)
        body += f"<tr>{cells}</tr>"
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def build_data():
    required_margin = 1_000_000
    pledged = [
        CollateralAsset("C1", "cash", 300_000, 0.00),
        CollateralAsset("C2", "govt_bond", 500_000, 0.02),
    ]
    call = margin_call(required_margin, pledged)

    available = [
        CollateralAsset("C1", "cash", 300_000, 0.00),
        CollateralAsset("C2", "govt_bond", 500_000, 0.02),
        CollateralAsset("C3", "corp_bond", 400_000, 0.08),
        CollateralAsset("C4", "equity", 300_000, 0.15),
    ]
    optimized = cheapest_to_deliver(required_margin, available)
    optimize_rows = [
        (a.asset_id, a.asset_type, f"${a.market_value:,.2f}", f"{a.haircut_pct:.0%}", f"${a.haircut_value:,.2f}")
        for a in optimized["selected"]
    ]

    shortfall = 900_000
    liquidation_discounts = {"cash": 0.00, "govt_bond": 0.01, "corp_bond": 0.04, "equity": 0.10}
    liq_result = trigger_liquidation(shortfall, available, liquidation_discounts)
    liquidation_rows = [
        (item["asset"].asset_id, item["asset"].asset_type, f"${item['asset'].haircut_value:,.2f}",
         f"{item['liquidation_discount']:.0%}", f"${item['net_proceeds']:,.2f}")
        for item in liq_result["liquidated"]
    ]

    mark_price, index_price = 65_200, 65_000
    rate = funding_rate(mark_price, index_price)
    position_notional = 500_000
    account_equity = 50_000
    funding_rows = []
    for i in range(1, 10):
        payment = funding_payment(position_notional, rate, is_long=True)
        account_equity += payment
        funding_rows.append((i, f"${payment:,.2f}", f"${account_equity:,.2f}"))

    maintenance_margin = 40_000
    funding_call = margin_call(maintenance_margin, [CollateralAsset("EQUITY", "cash", account_equity, 0.00)])

    return {
        "call": call,
        "required_margin": required_margin,
        "optimize_rows": optimize_rows,
        "optimized_value": optimized["pledged_haircut_value"],
        "shortfall": shortfall,
        "liquidation_rows": liquidation_rows,
        "liq_result": liq_result,
        "funding_rate": rate,
        "position_notional": position_notional,
        "funding_rows": funding_rows,
        "funding_call": funding_call,
        "maintenance_margin": maintenance_margin,
    }


def build_html(data):
    call = data["call"]
    liq = data["liq_result"]
    fcall = data["funding_call"]

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Collateral & Margin Engine Dashboard</title>
<style>
  body {{ font-family: -apple-system, Helvetica, Arial, sans-serif; background: #f5f6f8; color: #1a1a1a; margin: 0; padding: 32px; }}
  h1 {{ color: #1B3A5C; margin-bottom: 4px; }}
  .subtitle {{ color: #5a5a5a; margin-bottom: 28px; }}
  .card {{ background: #ffffff; border-radius: 8px; padding: 20px 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  .card h2 {{ color: #1B3A5C; font-size: 16px; margin-top: 0; border-bottom: 1px solid #e2e2e2; padding-bottom: 8px; }}
  .figure-row {{ }}
  .figure-block {{ display: inline-block; margin-right: 48px; vertical-align: top; }}
  .figure {{ font-size: 24px; font-weight: 600; color: #1B3A5C; }}
  .figure-warn {{ color: #b3401f; }}
  .figure-label {{ font-size: 12px; color: #5a5a5a; margin-bottom: 4px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; background: #1B3A5C; color: #fff; padding: 8px 10px; }}
  td {{ padding: 8px 10px; border-bottom: 1px solid #ececec; }}
  tr:nth-child(even) td {{ background: #fafafa; }}
</style>
</head>
<body>
  <h1>Collateral & Margin Engine</h1>
  <div class="subtitle">Margin calls, collateral optimization, liquidation, and crypto funding</div>

  <div class="card">
    <h2>Margin call check</h2>
    <div class="figure-row">
      <div class="figure-block">
        <div class="figure-label">Required margin</div>
        <div class="figure">${call['required_margin']:,.2f}</div>
      </div>
      <div class="figure-block">
        <div class="figure-label">Pledged (haircut-adjusted)</div>
        <div class="figure">${call['pledged_haircut_value']:,.2f}</div>
      </div>
      <div class="figure-block">
        <div class="figure-label">Shortfall</div>
        <div class="figure figure-warn">${call['shortfall']:,.2f}</div>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>Cheapest-to-deliver optimization</h2>
    {render_table(["Asset", "Type", "Market value", "Haircut", "Counts as"], data["optimize_rows"])}
    <div class="figure-row" style="margin-top: 16px;">
      <div class="figure-block">
        <div class="figure-label">Total posted (haircut-adjusted)</div>
        <div class="figure">${data['optimized_value']:,.2f}</div>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>Forced liquidation (${data['shortfall']:,.0f} shortfall, deadline missed)</h2>
    {render_table(["Asset", "Type", "Haircut value", "Liquidation discount", "Net proceeds"], data["liquidation_rows"])}
    <div class="figure-row" style="margin-top: 16px;">
      <div class="figure-block">
        <div class="figure-label">Total proceeds</div>
        <div class="figure">${liq['total_proceeds']:,.2f}</div>
      </div>
      <div class="figure-block">
        <div class="figure-label">Fully covered</div>
        <div class="figure">{liq['fully_covered']}</div>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>Crypto perpetual funding accrual</h2>
    <div class="subtitle" style="margin-bottom: 12px;">${data['position_notional']:,.0f} long position, funding rate {data['funding_rate']:.4%} per 8h interval</div>
    {render_table(["Interval", "Funding payment", "Equity after"], data["funding_rows"])}
    <div class="figure-row" style="margin-top: 16px;">
      <div class="figure-block">
        <div class="figure-label">Maintenance margin</div>
        <div class="figure">${fcall['required_margin']:,.2f}</div>
      </div>
      <div class="figure-block">
        <div class="figure-label">Shortfall after funding</div>
        <div class="figure figure-warn">${fcall['shortfall']:,.2f}</div>
      </div>
      <div class="figure-block">
        <div class="figure-label">Margin call triggered</div>
        <div class="figure">{fcall['call_triggered']}</div>
      </div>
    </div>
  </div>
</body>
</html>"""


def main():
    data = build_data()
    output = build_html(data)
    with open("dashboard.html", "w") as f:
        f.write(output)
    print("Wrote dashboard.html -- open it in your browser to view it.")


if __name__ == "__main__":
    main()
