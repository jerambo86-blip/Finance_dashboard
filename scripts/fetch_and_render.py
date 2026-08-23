"""
Fetches quotes for the US and Korea ETF Top 10 lists via yfinance (free, no API key
needed) and renders a static dark-themed HTML dashboard. Also keeps a rolling
history file so the dashboard can show a trend line over past runs.

Run manually:   python scripts/fetch_and_render.py
Run on a schedule: see .github/workflows/update-dashboard.yml
"""

import json
import os
from datetime import datetime, timezone

import yfinance as yf

# ---- Ticker lists ---------------------------------------------------------

US_ETFS = {
    "VOO": "S&P500 (미국 대형주)",
    "QQQ": "나스닥100 (기술주)",
    "VTI": "미국 전체시장",
    "VUG": "미국 성장주",
    "VTV": "미국 가치주",
    "IWM": "미국 소형주",
    "BND": "미국 채권",
    "GLD": "금",
    "VXUS": "해외 전체주식",
    "VNQ": "리츠(부동산)",
}

KR_ETFS = {
    "069500.KS": "KODEX 200",
    "102110.KS": "TIGER 200",
    "122630.KS": "KODEX 레버리지",
    "252670.KS": "KODEX 200선물인버스2X",
    "292150.KS": "TIGER TOP10",
    "229200.KS": "KODEX 코스닥150",
    "379800.KS": "KODEX 미국S&P500",
    "133690.KS": "TIGER 미국나스닥100",
    "132030.KS": "KODEX 골드선물(H)",
    "153130.KS": "KODEX 단기채권",
}

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "history.json")
OUTPUT_HTML = os.path.join(os.path.dirname(__file__), "..", "index.html")
MAX_HISTORY_POINTS = 26  # ~1 year of biweekly snapshots

# ---- Data fetching ----------------------------------------------------------


def fetch_quote(ticker: str):
    """Returns (price, change_percent) or (None, None) if unavailable."""
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        price = info.get("last_price") or info.get("lastPrice")
        prev_close = info.get("previous_close") or info.get("previousClose")
        if price is None:
            return None, None
        change_pct = None
        if prev_close:
            change_pct = (price - prev_close) / prev_close * 100
        return round(float(price), 2), (round(float(change_pct), 2) if change_pct is not None else None)
    except Exception as e:  # noqa: BLE001 - keep the run going even if one ticker fails
        print(f"[warn] failed to fetch {ticker}: {e}")
        return None, None


def load_history() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"us": {}, "kr": {}}


def save_history(history: dict) -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def append_point(history: dict, market: str, symbol: str, date: str, price):
    if price is None:
        return
    history.setdefault(market, {}).setdefault(symbol, [])
    history[market][symbol].append({"date": date, "price": price})
    history[market][symbol] = history[market][symbol][-MAX_HISTORY_POINTS:]


# ---- HTML rendering ---------------------------------------------------------

CSS = """
:root {
  --bg: #0B0F14;
  --card: #121821;
  --border: #232C38;
  --text: #E7ECF1;
  --muted: #8592A0;
  --up: #34D399;
  --down: #FB7185;
  --accent: #E8B54D;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, "Segoe UI", Inter, sans-serif;
  padding: 40px 24px 64px;
}
.wrap { max-width: 880px; margin: 0 auto; }
h1 { font-size: 28px; font-weight: 700; margin: 0 0 4px; letter-spacing: -0.5px; }
.updated {
  display: inline-block;
  font-family: "Courier New", monospace;
  font-size: 12px;
  color: #0B0F14;
  background: var(--accent);
  padding: 6px 12px;
  border-radius: 999px;
  font-weight: 700;
  margin: 12px 0 32px;
}
h2 { font-size: 17px; font-weight: 600; margin: 40px 0 14px; }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
}
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 18px;
}
.symbol { font-family: "Courier New", monospace; font-size: 14px; font-weight: 700; }
.name { font-size: 12px; color: var(--muted); margin-top: 2px; }
.price { font-family: "Courier New", monospace; font-size: 22px; font-weight: 700; margin-top: 10px; }
.change { font-family: "Courier New", monospace; font-size: 13px; margin-top: 4px; }
.up { color: var(--up); }
.down { color: var(--down); }
.na { color: var(--muted); font-size: 12px; }
footer { color: #4A5563; font-size: 11px; margin-top: 48px; }
"""


def render_cards(data: dict, labels: dict, currency_symbol: str) -> str:
    cards = []
    for symbol, label in labels.items():
        entry = data.get(symbol, {})
        price = entry.get("price")
        chg = entry.get("changePercent")
        if price is None:
            cards.append(
                f'<div class="card"><div class="symbol">{symbol}</div>'
                f'<div class="name">{label}</div><div class="na">데이터 없음</div></div>'
            )
            continue
        up = (chg or 0) >= 0
        arrow = "▲" if up else "▼"
        cls = "up" if up else "down"
        chg_text = f'{arrow} {abs(chg):.2f}%' if chg is not None else "-"
        price_text = f"{currency_symbol}{price:,.2f}"
        cards.append(
            f'<div class="card">'
            f'<div class="symbol">{symbol}</div>'
            f'<div class="name">{label}</div>'
            f'<div class="price">{price_text}</div>'
            f'<div class="change {cls}">{chg_text}</div>'
            f"</div>"
        )
    return "\n".join(cards)


def render_html(us_data: dict, kr_data: dict, updated_at: str) -> str:
    updated_display = updated_at.replace("T", " ").split(".")[0] + " UTC"
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>ETF 대시보드</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <h1>ETF 대시보드</h1>
  <div class="updated">UPDATED · {updated_display}</div>

  <h2>🇺🇸 미국 ETF TOP 10</h2>
  <div class="grid">
    {render_cards(us_data, US_ETFS, "$")}
  </div>

  <h2>🇰🇷 한국 ETF TOP 10</h2>
  <div class="grid">
    {render_cards(kr_data, KR_ETFS, "₩")}
  </div>

  <footer>2주(격주) 간격으로 GitHub Actions가 자동 갱신합니다. 데이터 출처: Yahoo Finance (yfinance).</footer>
</div>
</body>
</html>
"""


# ---- Main ---------------------------------------------------------------


def main():
    history = load_history()
    now = datetime.now(timezone.utc).isoformat()

    us_data = {}
    for symbol in US_ETFS:
        price, chg = fetch_quote(symbol)
        us_data[symbol] = {"price": price, "changePercent": chg}
        append_point(history, "us", symbol, now, price)

    kr_data = {}
    for symbol in KR_ETFS:
        price, chg = fetch_quote(symbol)
        kr_data[symbol] = {"price": price, "changePercent": chg}
        append_point(history, "kr", symbol, now, price)

    save_history(history)

    html = render_html(us_data, kr_data, now)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Wrote {OUTPUT_HTML} and updated {DATA_FILE}")


if __name__ == "__main__":
    main()
