"""
GOLDMINEBOT: stocks day trading bot
Alpaca (broker + market data) + GitHub Actions (runs every 5 min) + Google Sheet (log + kill switch)

Strategies (pick in the Sheet's Settings tab, cell "Strategy"):
  orb       = Opening Range Breakout (watchlist, 9:45-11:30 ET)
  vwap      = VWAP Pullback in an uptrend (watchlist, 10:00-15:00 ET)
  momentum  = Momentum on today's top gainers (9:45-11:30 ET)
  all       = run all three (or a comma list like "orb,vwap")

Every entry is a BRACKET order: the stop-loss and take-profit sit at Alpaca,
so they fire instantly even if a GitHub run is late.
"""
import os
import sys
import traceback
from datetime import datetime, timedelta, time as dtime
from zoneinfo import ZoneInfo

import requests

ET = ZoneInfo("America/New_York")


def env(name, default=None):
    value = os.environ.get(name)
    return value.strip() if value and value.strip() else default


# ---------------- Settings (GitHub Secrets / Variables) ----------------
PAPER = (env("PAPER", "true") or "true").lower() != "false"  # only the exact word "false" = LIVE
ALPACA_KEY = env("ALPACA_KEY")
ALPACA_SECRET = env("ALPACA_SECRET")
SHEET_URL = env("SHEET_WEBHOOK_URL")
SHEET_TOKEN = env("SHEET_TOKEN", "")

DEFAULT_STRATEGY = env("STRATEGY", "all").lower()
WATCHLIST = [s.strip().upper() for s in env(
    "WATCHLIST", "SPY,QQQ,AAPL,NVDA,TSLA,AMD,MSFT,META,AMZN,GOOGL").split(",") if s.strip()]

MAX_DOLLARS_PER_TRADE = float(env("MAX_DOLLARS_PER_TRADE", "500"))
MAX_DAILY_LOSS = float(env("MAX_DAILY_LOSS", "100"))
MAX_TRADES_PER_DAY = int(env("MAX_TRADES_PER_DAY", "5"))
MAX_OPEN_POSITIONS = int(env("MAX_OPEN_POSITIONS", "3"))
REWARD_RISK = float(env("REWARD_RISK", "2"))          # target = 2x the risk
MAX_STOP_PCT = float(env("MAX_STOP_PCT", "0.03"))     # skip trades whose stop is >3% away
MOMENTUM_MIN_GAIN_PCT = float(env("MOMENTUM_MIN_GAIN_PCT", "5"))

MIN_STOP_PCT = 0.002          # stops tighter than 0.2% get widened (avoid noise stop-outs)
MIN_PRICE, MAX_PRICE = 5.0, 500.0
STALE_ENTRY_MINUTES = 10      # unfilled entry orders get canceled after this
EOD_MINUTES_BEFORE_CLOSE = 15 # flatten everything this close to the bell (handles half-days)

TRADE_URL = "https://paper-api.alpaca.markets" if PAPER else "https://api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"
MODE = "PAPER" if PAPER else "LIVE"


# ---------------- Helpers ----------------
def alpaca(method, path, base=None, **kwargs):
    headers = {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}
    r = requests.request(method, (base or TRADE_URL) + path, headers=headers, timeout=20, **kwargs)
    if r.status_code >= 400:
        raise RuntimeError(f"Alpaca {method} {path} failed ({r.status_code}): {r.text[:300]}")
    try:
        return r.json()
    except ValueError:
        return {}


def parse_time(s):
    s = s.replace("Z", "+00:00")
    if "." in s:
        head, rest = s.split(".", 1)
        frac = ""
        for ch in rest:
            if ch.isdigit():
                frac += ch
            else:
                break
        tz = rest[len(frac):]
        s = f"{head}.{frac[:6].ljust(6, '0')}{tz}"
    return datetime.fromisoformat(s).astimezone(ET)


def sheet_log(kind, **data):
    print(f"[{MODE}] {kind}: {data}")
    if not SHEET_URL:
        return
    try:
        payload = {"token": SHEET_TOKEN, "kind": kind, "mode": MODE,
                   "time": datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S"), **data}
        requests.post(SHEET_URL, json=payload, timeout=20)
    except Exception as e:
        print("Sheet log failed:", e)


def sheet_settings():
    """Returns {"enabled", "strategy"} or None if the Sheet can't be read (then no new trades)."""
    if not SHEET_URL:
        return {"enabled": True, "strategy": DEFAULT_STRATEGY}
    try:
        r = requests.get(SHEET_URL, params={"token": SHEET_TOKEN}, timeout=20)
        try:
            data = r.json()
        except ValueError:
            host = r.url.split("/")[2] if "://" in r.url else r.url
            print(f"Sheet settings: got a web page instead of settings (HTTP {r.status_code}, from {host}).")
            print("First part of the page:", " ".join(r.text[:200].split()))
            u = SHEET_URL
            print("URL check:", {
                "length": len(u),
                "starts_ok": u.startswith("https://script.google.com/macros/s/"),
                "ends_with_exec": u.endswith("/exec"),
                "has_account_part_/u/": "/u/" in u,
                "has_workspace_part_/a/": "/a/" in u,
                "has_dev": u.endswith("/dev"),
                "has_question_mark": "?" in u,
                "has_space": " " in os.environ.get("SHEET_WEBHOOK_URL", ""),
            })
            print("Redirects:", [f"{h.status_code} {h.url.split('/')[2]}" for h in r.history])
            print("Check: SHEET_WEBHOOK_URL ends in /exec, and the web app access is 'Anyone'.")
            return None
        if "error" in data:
            print("Sheet settings error:", data["error"])
            return None
        enabled = str(data.get("enabled", "")).strip().upper() in ("TRUE", "ON", "YES", "1")
        strategy = str(data.get("strategy") or DEFAULT_STRATEGY).strip().lower()
        return {"enabled": enabled, "strategy": strategy}
    except Exception as e:
        print("Could not read Sheet settings:", e)
        return None


def parse_strategies(value):
    value = (value or "all").lower()
    if "all" in value:
        return ["orb", "vwap", "momentum"]
    picked = [s.strip() for s in value.replace(";", ",").split(",")]
    return [s for s in ["orb", "vwap", "momentum"] if s in picked]


# ---------------- Market data ----------------
def get_today_bars(symbols, now):
    """Closed 5-minute bars since today's open, per symbol (free IEX feed)."""
    if not symbols:
        return {}
    start = now.replace(hour=9, minute=30, second=0, microsecond=0)
    params = {"symbols": ",".join(sorted(symbols)), "timeframe": "5Min",
              "start": start.isoformat(), "feed": "iex", "limit": 10000, "adjustment": "raw"}
    result = {}
    while True:
        data = alpaca("GET", "/v2/stocks/bars", base=DATA_URL, params=params)
        for sym, bars in (data.get("bars") or {}).items():
            for b in bars:
                b["et"] = parse_time(b["t"])
                if b["et"] + timedelta(minutes=5) <= now:  # only fully closed bars
                    result.setdefault(sym, []).append(b)
        token = data.get("next_page_token")
        if not token:
            break
        params["page_token"] = token
    return result


def get_top_gainers():
    try:
        data = alpaca("GET", "/v1beta1/screener/stocks/movers", base=DATA_URL, params={"top": 20})
    except Exception as e:
        print("Top gainers lookup failed:", e)
        return []
    out = []
    for g in data.get("gainers", []):
        sym = str(g.get("symbol", ""))
        price = float(g.get("price") or 0)
        pct = float(g.get("percent_change") or 0)
        if sym.isalpha() and MIN_PRICE <= price <= MAX_PRICE and pct >= MOMENTUM_MIN_GAIN_PCT:
            out.append(sym)
    return out[:10]


def vwap_series(bars):
    pv = vol = 0.0
    out = []
    for b in bars:
        typical = (b["h"] + b["l"] + b["c"]) / 3
        pv += typical * b["v"]
        vol += b["v"]
        out.append(pv / vol if vol else b["c"])
    return out


# ---------------- Strategies (return {"entry","stop","why"} or None) ----------------
def strat_orb(bars, now):
    if not (dtime(9, 45) <= now.time() <= dtime(11, 30)):
        return None
    opening = [b for b in bars if b["et"].time() < dtime(9, 45)]
    after = [b for b in bars if b["et"].time() >= dtime(9, 45)]
    if len(opening) < 3 or not after:
        return None
    hi = max(b["h"] for b in opening)
    lo = min(b["l"] for b in opening)
    last = after[-1]
    if any(b["c"] > hi for b in after[:-1]):
        return None  # only the FIRST breakout counts
    avg_vol = sum(b["v"] for b in bars[:-1]) / max(1, len(bars) - 1)
    if last["c"] > hi and last["v"] >= avg_vol:
        return {"entry": last["c"], "stop": (hi + lo) / 2,
                "why": f"Broke opening range high {hi:.2f} on above-avg volume"}
    return None


def strat_vwap(bars, now):
    if not (dtime(10, 0) <= now.time() <= dtime(15, 0)) or len(bars) < 6:
        return None
    vw = vwap_series(bars)
    last, v = bars[-1], vw[-1]
    share_above = sum(1 for b, x in zip(bars, vw) if b["c"] > x) / len(bars)
    if share_above < 0.7:
        return None  # not a clean uptrend
    if last["l"] <= v * 1.002 and last["c"] > v and last["c"] > last["o"]:
        return {"entry": last["c"], "stop": min(last["l"], v * 0.996),
                "why": f"Pulled back to VWAP {v:.2f} and bounced (uptrend {share_above:.0%} above VWAP)"}
    return None


def strat_momentum(bars, now):
    if not (dtime(9, 45) <= now.time() <= dtime(11, 30)) or len(bars) < 4:
        return None
    vw = vwap_series(bars)
    last = bars[-1]
    prior_high = max(b["h"] for b in bars[:-1])
    if last["c"] > prior_high and last["c"] > vw[-1] and last["c"] > last["o"]:
        return {"entry": last["c"], "stop": last["l"],
                "why": f"Top gainer making new high of day above {prior_high:.2f}"}
    return None


STRATEGIES = {"orb": strat_orb, "vwap": strat_vwap, "momentum": strat_momentum}


# ---------------- Orders & risk ----------------
def close_everything(reason):
    positions = alpaca("GET", "/v2/positions")
    orders = alpaca("GET", "/v2/orders", params={"status": "open", "limit": 500})
    if positions:
        alpaca("DELETE", "/v2/positions", params={"cancel_orders": "true"})
    elif orders:
        alpaca("DELETE", "/v2/orders")
    if positions or orders:
        sheet_log("CLOSE_ALL", message=f"{reason}: closed {len(positions)} position(s), canceled open orders")
    else:
        print(f"{reason}: nothing open.")


def cancel_stale_entries(orders, now):
    for o in orders:
        if o.get("side") == "buy" and o.get("order_class") == "bracket" and float(o.get("filled_qty") or 0) == 0:
            stamp = o.get("submitted_at") or o.get("created_at")
            if stamp and parse_time(stamp) < now - timedelta(minutes=STALE_ENTRY_MINUTES):
                alpaca("DELETE", f"/v2/orders/{o['id']}")
                sheet_log("CANCEL_STALE", message=f"{o['symbol']} entry not filled in {STALE_ENTRY_MINUTES} min, canceled")


def entries_today(now):
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    orders = alpaca("GET", "/v2/orders", params={"status": "all", "after": start.isoformat(),
                                                  "limit": 500, "nested": "false"})
    count = 0
    for o in orders:
        if o.get("side") != "buy":
            continue
        if float(o.get("filled_qty") or 0) > 0 or o.get("status") in ("new", "accepted", "pending_new", "partially_filled"):
            count += 1
    return count


def build_order(sym, strategy, sig, buying_power, now):
    entry, stop = float(sig["entry"]), float(sig["stop"])
    if not (MIN_PRICE <= entry <= MAX_PRICE):
        return None
    risk = entry - stop
    if risk <= 0 or risk / entry > MAX_STOP_PCT:
        return None
    if risk / entry < MIN_STOP_PCT:
        stop = entry * (1 - MIN_STOP_PCT)
        risk = entry - stop
    limit = round(entry * 1.001, 2)
    stop = round(stop, 2)
    target = round(limit + risk * REWARD_RISK, 2)
    qty = int(min(MAX_DOLLARS_PER_TRADE, buying_power * 0.95) // limit)
    if qty < 1:
        return None
    return {
        "symbol": sym, "qty": str(qty), "side": "buy", "type": "limit",
        "limit_price": f"{limit:.2f}", "time_in_force": "day", "order_class": "bracket",
        "take_profit": {"limit_price": f"{target:.2f}"},
        "stop_loss": {"stop_price": f"{stop:.2f}"},
        "client_order_id": f"{strategy}-{sym}-{now:%Y%m%d%H%M%S}",
    }


# ---------------- Main ----------------
def main():
    if not ALPACA_KEY or not ALPACA_SECRET:
        sys.exit("Missing ALPACA_KEY or ALPACA_SECRET secret.")

    clock = alpaca("GET", "/v2/clock")
    if not clock.get("is_open"):
        print(f"[{MODE}] Market closed. Nothing to do.")
        return

    now = datetime.now(ET)
    account = alpaca("GET", "/v2/account")
    if account.get("trading_blocked") or account.get("account_blocked"):
        sheet_log("ERROR", message="Alpaca account is blocked from trading")
        return
    equity = float(account["equity"])
    last_equity = float(account.get("last_equity") or 0)
    if last_equity <= 0:
        last_equity = equity  # brand-new account has no previous close yet
    day_pnl = equity - last_equity
    print(f"[{MODE}] {now:%H:%M} ET | equity {equity:.2f} | day P&L {day_pnl:+.2f}")

    # 1) End of day: flatten everything (works on half-days too)
    minutes_to_close = (parse_time(clock["next_close"]) - now).total_seconds() / 60
    if minutes_to_close <= EOD_MINUTES_BEFORE_CLOSE:
        close_everything("End of day")
        sheet_log("DAY_SUMMARY", start_equity=round(last_equity, 2),
                  end_equity=round(equity, 2), day_pnl=round(day_pnl, 2))
        return

    # 2) Daily loss limit
    if day_pnl <= -MAX_DAILY_LOSS:
        close_everything(f"Daily loss limit hit ({day_pnl:+.2f})")
        return

    # 3) Kill switch / strategy from the Sheet
    settings = sheet_settings()
    if settings is None:
        print("Settings tab unreachable: not opening new trades this run.")
        return
    if not settings["enabled"]:
        close_everything("Kill switch OFF")
        return

    # 4) Housekeeping and capacity
    orders = alpaca("GET", "/v2/orders", params={"status": "open", "nested": "true", "limit": 500})
    cancel_stale_entries(orders, now)
    positions = alpaca("GET", "/v2/positions")
    busy = {p["symbol"] for p in positions} | {o["symbol"] for o in orders}
    slots = min(MAX_OPEN_POSITIONS - len(busy), MAX_TRADES_PER_DAY - entries_today(now))
    if slots <= 0:
        print("No free slots (max positions or max trades per day reached).")
        return

    # 5) Scan
    active = parse_strategies(settings["strategy"])
    if not active:
        sheet_log("ERROR", message=f"Unknown strategy setting '{settings['strategy']}'. Use orb, vwap, momentum or all.")
        return
    watch = set(WATCHLIST) if ("orb" in active or "vwap" in active) else set()
    gainers = get_top_gainers() if "momentum" in active else []
    bars = get_today_bars(watch | set(gainers), now)

    candidates, seen = [], set()
    for name in active:
        symbols = gainers if name == "momentum" else sorted(watch)
        for sym in symbols:
            if sym in busy or sym in seen or not bars.get(sym):
                continue
            sig = STRATEGIES[name](bars[sym], now)
            if sig:
                candidates.append((name, sym, sig))
                seen.add(sym)

    if not candidates:
        print(f"No signals ({', '.join(active)}).")
        return

    # 6) Place bracket orders
    buying_power = float(account["buying_power"])
    placed = 0
    for name, sym, sig in candidates:
        if placed >= slots:
            break
        order = build_order(sym, name, sig, buying_power, now)
        if not order:
            continue
        try:
            res = alpaca("POST", "/v2/orders", json=order)
        except Exception as e:
            sheet_log("ERROR", message=f"Order failed for {sym}: {e}")
            continue
        placed += 1
        buying_power -= float(order["qty"]) * float(order["limit_price"])
        sheet_log("ENTRY", strategy=name, symbol=sym, qty=int(order["qty"]),
                  entry=float(order["limit_price"]), stop=float(order["stop_loss"]["stop_price"]),
                  target=float(order["take_profit"]["limit_price"]), reason=sig["why"],
                  order_id=res.get("id", ""))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        sheet_log("ERROR", message=str(e)[:500])
        sys.exit(1)
