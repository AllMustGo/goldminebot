# GOLDMINEBOT

Alpaca (stocks, gold ETFs) + GOLDMINEBOT engine on GitHub Actions (every 5 min) + Google Sheet + phone dashboard.
Phone app: portfolio chart with 1D-ALL ranges (drag to scrub), stocks and watchlist with
sparklines, stock pages with chart, stats and news, and Buy/Sell from the app.
The bot only manages its own trades (tagged orb-/vwap-/momentum-); stocks you buy
yourself (tagged manual-) are never sold by the bot.
Engines (installed by setup()): alerts every 5 min, recurring buys daily ~10 AM ET,
Intel recheck daily. Notifications by email and ntfy phone push (Settings > Notifications).
App extras: market strip, portfolio breakdown, report card vs. S&P 500, trade journal,
limit/stop orders, other accounts (e.g. Robinhood) tracking.
AI: morning brief on weekdays (Settings > Morning brief), Ask tab chat, earnings calendar.
Coming next: daily scanner, backtesting, Coinbase crypto.

## Files
- bot.py, requirements.txt, .github/workflows/trade.yml  -> GitHub repo
- apps_script/Code.gs, apps_script/Dashboard.html       -> the Google Sheet's Apps Script

## 1. Google Sheet + dashboard (use jbensonslist@gmail.com)
1. New Google Sheet named GOLDMINEBOT > Extensions > Apps Script.
2. Paste Code.gs into Code.gs. Click + > HTML, name it exactly Dashboard, paste Dashboard.html.
3. Run setup() once and approve permissions. Open Executions/Logs and copy BOT_TOKEN and DASH_KEY.
4. Project Settings (gear) > Script properties > add:
   ALPACA_KEY, ALPACA_SECRET, PAPER (true or false, same as GitHub),
   ANTHROPIC_API_KEY (from console.anthropic.com: Intel, morning brief, Ask tab),
   FINNHUB_API_KEY (optional, free at finnhub.io: earnings calendar)
5. Deploy > New deployment > Web app > Execute as: Me, Who has access: Anyone > Deploy.
6. Your dashboard link = the web app URL + ?key=YOUR_DASH_KEY  (save it in iPhone Notes)
7. After any code change: Deploy > Manage deployments > edit (pencil) > Version: New version.
   The URL stays the same.

Anyone without the key sees only "access key needed". Keep the full link private.

## 2. Alpaca
Paper keys and live keys are different. Use the set that matches PAPER.

## 3. GitHub
Repo name: goldminebot. Settings > Secrets and variables > Actions.

Secrets: ALPACA_KEY, ALPACA_SECRET, SHEET_WEBHOOK_URL (web app URL, no ?key), SHEET_TOKEN (= BOT_TOKEN)

Variables (optional except PAPER). Anything you set in the app's Settings screen
(gear icon) overrides these; they're only the fallback:
| Variable | Default | Meaning |
|---|---|---|
| PAPER | true | Exactly `false` = live money |
| STRATEGY | all | Fallback only; the dashboard setting wins |
| WATCHLIST | SPY,QQQ,AAPL,NVDA,TSLA,AMD,MSFT,META,AMZN,GOOGL | Used by ORB and VWAP |
| MAX_DOLLARS_PER_TRADE | 500 | Position size cap |
| MAX_DAILY_LOSS | 100 | Hit it: close all, stop for the day |
| MAX_TRADES_PER_DAY | 5 | New entries per day |
| MAX_OPEN_POSITIONS | 3 | At the same time |
| REWARD_RISK | 2 | Target = 2x stop distance |
| MAX_STOP_PCT | 0.03 | Skip setups with a stop over 3% away |
| MOMENTUM_MIN_GAIN_PCT | 5 | Min daily gain for momentum list |

## Sheet tabs
Settings, Trades, Daily, Log, Alerts, AutoInvest, Watchlist, Holdings (Coinbase balances, filled later),
Intel (event notes + AI research; notes on hold are rechecked daily at 7am ET).
Format them however you like; the code only adds rows and changes values.
