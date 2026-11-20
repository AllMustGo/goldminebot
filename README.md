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
Coinbase (view-only): coinbase_sync.py + .github/workflows/coinbase.yml sync balances
every 30 min into the Holdings tab. GitHub secrets: COINBASE_KEY_NAME, COINBASE_PRIVATE_KEY
(ECDSA key, View permission only).
Compare tab: add tickers (app or Sheet column A + Found at in C); company numbers fill daily
at 6 AM ET from Finnhub. Run styleSheets() once to give the Sheet the app's look (it never runs
automatically, so your own formatting is safe).
Market data extras: today's movers, holiday/early-close notices, upcoming IPOs, dividends,
bid/ask spread warnings, and per-company analyst ratings, earnings beat/miss, insider trades,
peers, beta, dividend yield, ROE, debt/equity and 52-week position (Finnhub free plan).
Self-improvement: daily self-check at 6:30 AM ET (fixes missing schedules, flags bot/Sheet,
Alpaca, Coinbase, Compare and error problems; notifies only when needed) and a weekly AI
improvement report on Saturdays at 9 AM ET with setting suggestions you Approve or Dismiss
in the app (More > Health & improvements). Nothing changes without your approval.
IPO Watch (More > IPO Watch): track private companies; checked daily ~7:15 AM ET against the
Finnhub IPO calendar, SEC S-1/F-1 filings and listings worldwide; notifies on status changes.
Search accepts company names and explains foreign-only listings.
Coming next: daily scanner, backtesting, crypto recurring buys.

## Files
- bot.py, coinbase_sync.py, requirements.txt, .github/workflows/trade.yml and coinbase.yml -> GitHub repo
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

## Trading style: Normal or Aggressive (paper money only)
Settings > Bot style > Trading style. Picking **Aggressive** and saving fills in a preset so the bot trades much more and you collect data faster:
20 trades/day, 6 positions at once, a 35-stock watchlist, momentum 9:35–14:30, breakouts until 13:00, VWAP 9:50–15:15,
momentum also scans the watchlist, an extra "VWAP reclaim" setup, profit target 1.5x the risk, top 20 gainers, and the daily loss limit
raised to at least $300. Your $ per trade is not changed. Picking **Normal** puts the defaults back.
The app refuses Aggressive with live money, and the bot won't open trades if it ever sees Aggressive with PAPER=false.

## Trading tab (bottom bar, replaces "Bot")
**Bot trading:** on/off switch, today's bot P&L, wins/losses, trades used, loss limit used; every open bot position with a
stop → bought → target bar showing where the price is now and why it bought; today's buys and sells with reasons and results;
a 30-day scoreboard per setup (Breakout, VWAP, Momentum, Crypto) with plain-language lessons; finished trades; setup switches.
**My trading:** search to buy/sell, your stocks with Buy more / Sell buttons, your waiting orders (cancel), your recent orders.
The bot never sells your stocks.

## Crypto bot (paper money, 24/7) and gold
Runs from the Sheet every 10 minutes (trigger `runCryptoBot`, installed by `setup()`), so it costs no GitHub minutes.
Buys a breakout of the last 5 hours (Normal) or 3 hours (Aggressive, which also buys bounces back above the 20-bar average)
when the trend is up on 15-minute charts. Stop = 1.5x the average bar size (max 5% away), target = reward/risk setting.
Sells at the stop, target, after the time limit, or when the crypto bot or main switch is turned off. Settings › Crypto & gold.
Note: it checks every 10 minutes, so a fast move can go past the stop before it sells.
Gold: "Bot also day-trades gold" adds GLD, SLV, GDX, NEM to the stock bot's watchlist.

## Trade models (Trading › Models, also More › Trade models)
Ready-made rule sets you switch between in one tap: Careful, Aggressive, Quick hits (scalping, 1x targets), Big winners
(3x targets, fewer trades), Opening bell (first two hours only), Crypto only (stocks paused, up to 5 coins).
Each card shows trades/day, positions at once, target, widest stop, last new trade time, and the win rate needed to break even.
Every trade is labeled with the active model (Trades tab, column "Model"), and "Results by model" compares their profit.
If the weekly self-improvement or you change a setting, the active model shows "tuned" and lists what changed;
"Reset to …" puts the model's settings back. Your $ per trade and loss limit are never lowered by a model.
Settings › Trading style is a shortcut: Aggressive = Aggressive model, Normal = Careful model.
