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

## Live screen (bottom bar; Ask moved to More)
Watch the bots work: a live strip (bot P&L today, open, trades used, won/lost, loss limit, market countdown),
a 5-stage pipeline (Scanning › Almost a signal › Order placed › In trade › Closed today) and a live feed of every
buy, sell, order, skipped signal (with the reason) and status change. Refreshes every 20 seconds while open.
How: bot.py sends a SCAN report at the end of every run (what it scanned, near misses within 0.6%, skips and why);
the crypto bot does the same. Only the latest scan + a 40-item rolling feed are kept (Script properties, not rows),
so the Sheet doesn't grow. If the stock bot hasn't run for 20+ minutes during market hours, Live shows a warning.
Trading › Bot trading is now the review screen (today, scoreboard, finished trades, setups); open trades and
today's moves live on the Live screen.

## Reliable timer (cron-job.org, free) + signal memory
GitHub's own timer is often 10-20 minutes late during market hours, so the bot kept arriving after breakouts.
1. bot.py now has signal memory: it checks the last 3 bars and still takes a breakout from 5-10 minutes ago if the
   price is within 0.3% of the signal price (no chasing). If the price ran away, Live shows it as skipped with the reason.
2. cron-job.org starts the workflow exactly every 5 minutes, using a GitHub token that can only run this repo's workflows:
   - GitHub › Settings › Developer settings › Personal access tokens › Fine-grained tokens › Generate new token.
     Name: goldminebot-timer. Expiration: 1 year. Repository access: Only select repositories › AllMustGo/goldminebot.
     Permissions › Repository › Actions: Read and write. Generate and copy the token (starts with github_pat_).
   - cron-job.org (free account) › Create cronjob:
     URL: https://api.github.com/repos/AllMustGo/goldminebot/actions/workflows/trade.yml/dispatches
     Schedule: Custom › every 5 minutes, hours 9-15, Monday-Friday, time zone America/New_York.
     Advanced › Request method: POST. Headers:
       Accept: application/vnd.github+json
       Authorization: Bearer github_pat_...  (your token)
       X-GitHub-Api-Version: 2022-11-28
     Request body: {"ref":"main","inputs":{"source":"timer"}}
     Save, then "Test run": the answer should be 204 and a new run appears in GitHub › Actions.
   GitHub's own schedule stays on as a backup; overlapping runs simply queue.

## Crypto system (weather-based)
Every 10 minutes from the Sheet. Bitcoin's daily + hourly trend sets the crypto weather:
Uptrend → breakout (24-hour high, 12 in Aggressive) or pullback to the 20-hour average; Sideways → buy near the bottom
of the 2-day range, sell near the top; Downtrend → wait in cash and sell open trades that aren't working.
Exits: stop 1.5x the average hourly move; break-even at +1R; trailing stop after +2R (trend trades); time limit
(Settings, default 48h). Protections: daily + weekly loss limits, 12-hour pause after 3 losses in a row, max 2 new
coins per check. Fear & Greed index (alternative.me) shown on Live. Bot trade alerts default to phone push for each
trade + one 8 PM summary email (Settings › Notifications); run setup() once to add the 8 PM trigger.

## Mirror tab (bottom bar; Alpaca moved under More)
Your real money next to GMB:
- Family goal: target, progress (Robinhood + Coinbase), and when you'd reach it at your weekly deposit and 7%/yr.
- Update Robinhood from screenshots: pick screenshots, Claude reads tickers/shares/cost, you confirm. Stored as
  "Robinhood" rows in the OtherAccounts tab. "Add cost" lets you type the average cost per share.
- Side by side per stock: Robinhood vs GMB (your own paper picks, not the bot), differences highlighted, and a coach:
  50-day trend, suggested stop-loss (20-day low or 2x the daily move), concentration (>40%), under-$1 and bankruptcy (Q) flags.
  "Try a buy/sell (GMB)" rehearses a move on paper first.
- The race: you (Robinhood total) vs the bot in Budget mode (its real trades re-sized to your budget, 30% per trade)
  vs the S&P 500 (SPY). Daily snapshot 4:30 PM into the Race tab; on payday the trading share of your deposit is added
  to the bot and the S&P. Run setup() once to add the 4:30 trigger.
- Coinbase holdings (auto-synced) and what the crypto bot holds.
- Paycheck plan: weekly deposit, core/trading split, emergency fund, 1/5/10-year ranges at 2%, 7%, 10% a year.
Settings › Money plan holds the same values.
