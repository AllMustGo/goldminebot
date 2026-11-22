<!DOCTYPE html>
<html>
<head>
<base target="_top">
<meta charset="utf-8">
<title>GOLDMINEBOT</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #F6F7F9; --surface: #FFFFFF; --sunk: #EEF0F3; --ink: #11151C; --muted: #646E7E; --line: #E2E5EA;
    --gold: #A8790A; --gold-ink: #FFFFFF; --gain: #0B9E68; --loss: #E2483D; --trend: var(--gain);
    color-scheme: light;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0D1015; --surface: #161A21; --sunk: #1D222B; --ink: #EEF1F5; --muted: #8F98A8; --line: #262C36;
      --gold: #E2B33C; --gold-ink: #15120A; --gain: #2FD58F; --loss: #FF6A5D;
      color-scheme: dark;
    }
  }
  :root[data-trend="down"] { --trend: var(--loss); }
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  html, body { margin: 0; background: var(--bg); color: var(--ink); }
  body {
    font-family: "Manrope", system-ui, -apple-system, "Segoe UI", sans-serif;
    font-size: 16px; line-height: 1.45; font-variant-numeric: tabular-nums;
    padding: env(safe-area-inset-top, 0) 0 calc(78px + env(safe-area-inset-bottom, 0));
  }
  main { max-width: 560px; margin: 0 auto; padding: 14px 18px 28px; }
  .homegrid { display: flex; flex-direction: column; }
  .homegrid .col { display: contents; }
  h2 { font-size: 1.15rem; font-weight: 800; margin: 32px 0 8px; letter-spacing: -0.01em; }
  p { margin: 0; }
  button { font: inherit; color: inherit; }
  .muted { color: var(--muted); } .small { font-size: .85rem; }
  .gain { color: var(--gain); } .loss { color: var(--loss); } .trend { color: var(--trend); }

  /* Top bar */
  .top { display: flex; align-items: center; gap: 10px; }
  .brand { font-weight: 800; letter-spacing: -0.02em; color: var(--gold); font-size: 1.05rem; }
  .chip { white-space: nowrap; font-weight: 700; font-size: .78rem; padding: 3px 9px; border-radius: 999px; background: var(--sunk); color: var(--muted); }
  .chip.live { background: var(--loss); color: #fff; }
  .spacer { flex: 1; }
  .ghost { border: 0; background: none; color: var(--muted); font-weight: 600; font-size: .9rem; padding: 6px 4px; }

  .search { margin-top: 14px; display: flex; align-items: center; gap: 8px; background: var(--sunk); border-radius: 12px; padding: 0 12px; }
  .search svg { flex: none; width: 18px; height: 18px; stroke: var(--muted); }
  .search input { border: 0; background: none; padding: 11px 0; width: 100%; font: inherit; font-size: 16px; color: var(--ink); outline: none; }

  /* Hero value + chart: the signature element */
  .hero { margin-top: 22px; }
  .value { font-size: clamp(2.5rem, 11vw, 3.3rem); font-weight: 800; letter-spacing: -0.035em; line-height: 1.05; }
  .delta { margin-top: 6px; font-weight: 700; color: var(--trend); }
  .delta .muted { font-weight: 600; }
  .chart { position: relative; margin: 18px -18px 0; height: 190px; touch-action: pan-y; cursor: crosshair; }
  .chart svg { width: 100%; height: 100%; display: block; overflow: visible; }
  .chart .line { fill: none; stroke: var(--trend); stroke-width: 2.25; stroke-linejoin: round; stroke-linecap: round; }
  .chart .baseline { stroke: var(--muted); stroke-width: 1; stroke-dasharray: 2 5; opacity: .6; vector-effect: non-scaling-stroke; }
  .cursor { position: absolute; top: 0; bottom: 0; width: 1px; background: var(--muted); opacity: 0; pointer-events: none; }
  .dot { position: absolute; width: 11px; height: 11px; margin: -5.5px 0 0 -5.5px; border-radius: 50%; background: var(--trend); border: 2px solid var(--bg); opacity: 0; pointer-events: none; }
  .chart.scrubbing .cursor, .chart.scrubbing .dot { opacity: 1; }
  .ylab { position: absolute; right: 18px; font-size: .72rem; font-weight: 700; color: var(--muted); background: color-mix(in srgb, var(--bg) 80%, transparent); padding: 1px 6px; border-radius: 6px; pointer-events: none; }
  .xlabs { display: flex; justify-content: space-between; font-size: .72rem; color: var(--muted); margin-top: 4px; }
  .chartnote { font-size: .8rem; color: var(--muted); margin-top: 4px; }
  .chart .flat { position: absolute; inset: 0; display: grid; place-items: center; color: var(--muted); font-size: .9rem; }
  .ranges { display: flex; justify-content: space-between; margin-top: 10px; border-bottom: 1px solid var(--line); padding-bottom: 10px; }
  .ranges button { border: 0; background: none; font-weight: 700; font-size: .85rem; color: var(--muted); padding: 6px 10px; border-radius: 8px; }
  .ranges button.on { background: var(--trend); color: var(--bg); }

  .rowlink { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid var(--line); }

  /* Lists */
  .item { display: grid; grid-template-columns: 1fr 76px 92px; align-items: center; gap: 10px; padding: 12px 0; border-bottom: 1px solid var(--line); width: 100%; background: none; border-left: 0; border-right: 0; border-top: 0; text-align: left; cursor: pointer; }
  .item .sym { font-weight: 800; }
  .item .sub { font-size: .82rem; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .spark { width: 76px; height: 30px; display: block; }
  .spark path { fill: none; stroke-width: 1.6; stroke-linejoin: round; }
  .spark.up path { stroke: var(--gain); } .spark.down path { stroke: var(--loss); }
  .pill { justify-self: end; min-width: 84px; text-align: center; font-weight: 700; font-size: .88rem; padding: 6px 8px; border-radius: 8px; border: 0; color: #fff; background: var(--gain); }
  .pill.down { background: var(--loss); }
  .pill.flat { background: var(--sunk); color: var(--muted); }
  .empty { padding: 16px 0; color: var(--muted); }
  .notice { padding: 12px 14px; border-radius: 12px; background: var(--sunk); font-size: .9rem; }
  .notice.bad { background: color-mix(in srgb, var(--loss) 14%, var(--surface)); }

  /* Buttons */
  .primary { border: 0; border-radius: 999px; padding: 14px 18px; font-weight: 800; background: var(--gold); color: var(--gold-ink); width: 100%; }
  .outline { border: 1.5px solid var(--line); border-radius: 999px; padding: 12px 18px; font-weight: 700; background: none; width: 100%; }
  .danger { margin-top: 26px; width: 100%; padding: 14px; border-radius: 999px; border: 1.5px solid var(--loss); background: transparent; color: var(--loss); font-weight: 800; }
  button:disabled { opacity: .5; }
  button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible { outline: 3px solid var(--gold); outline-offset: 2px; }

  /* Bot switch */
  .switch { margin-top: 18px; width: 100%; display: flex; align-items: center; gap: 14px; padding: 14px 16px; border-radius: 18px; border: 2px solid var(--line); background: var(--surface); text-align: left; cursor: pointer; }
  .switch .track { flex: none; width: 58px; height: 34px; border-radius: 999px; background: var(--line); position: relative; transition: background .2s; }
  .switch .knob { position: absolute; top: 4px; left: 4px; width: 26px; height: 26px; border-radius: 50%; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.3); transition: left .2s; }
  .switch.on { border-color: var(--gain); } .switch.on .track { background: var(--gain); } .switch.on .knob { left: 28px; }
  .switch strong { display: block; font-size: 1.05rem; }
  .row { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--line); }
  .row .grow { flex: 1; min-width: 0; }
  .row .right { text-align: right; }
  .toggle { flex: none; width: 46px; height: 28px; border-radius: 999px; border: 0; background: var(--line); position: relative; }
  .toggle::after { content: ""; position: absolute; top: 3px; left: 3px; width: 22px; height: 22px; border-radius: 50%; background: #fff; transition: left .15s; }
  .toggle.on { background: var(--gain); } .toggle.on::after { left: 21px; }
  .del { flex: none; border: 0; background: none; color: var(--muted); font-size: .85rem; text-decoration: underline; padding: 4px; }

  /* Forms */
  form.card { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 14px; display: grid; gap: 10px; }
  .pair { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  label { display: grid; gap: 4px; font-size: .85rem; color: var(--muted); }
  input, select, textarea { font: inherit; font-size: 16px; color: var(--ink); background: var(--sunk); border: 1px solid var(--line); border-radius: 10px; padding: 10px; width: 100%; }
  textarea { min-height: 150px; resize: vertical; }

  /* Intel */
  .tag { display: inline-block; font-size: .78rem; font-weight: 700; padding: 2px 8px; border-radius: 999px; background: var(--sunk); }
  .tag.public { color: var(--gain); } .tag.theme { color: var(--gold); } .tag.hold { color: #fff; background: var(--loss); }
  details.intel { padding: 12px 0; border-bottom: 1px solid var(--line); }
  details.intel summary { list-style: none; cursor: pointer; }
  details.intel summary::-webkit-details-marker { display: none; }
  details.intel .body { margin-top: 10px; display: grid; gap: 10px; font-size: .92rem; white-space: pre-wrap; overflow-wrap: anywhere; }
  a { color: var(--gold); }

  /* Stock detail page */
  #detail { position: fixed; inset: 0; background: var(--bg); overflow-y: auto; z-index: 20; display: none;
    padding: env(safe-area-inset-top, 0) 0 calc(96px + env(safe-area-inset-bottom, 0)); }
  #detail.open { display: block; }
  .dtop { display: flex; justify-content: space-between; align-items: center; }
  .iconbtn { border: 0; background: none; font-size: 1.6rem; line-height: 1; padding: 6px 8px; color: var(--ink); }
  .star.on { color: var(--gold); }
  .dsym { font-size: 1.05rem; font-weight: 800; margin-top: 8px; }
  .stats { display: grid; grid-template-columns: 1fr 1fr; column-gap: 24px; }
  .stats div { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--line); font-size: .92rem; }
  .stats span:first-child { color: var(--muted); }
  .news a { display: block; padding: 12px 0; border-bottom: 1px solid var(--line); color: var(--ink); text-decoration: none; }
  .news .src { font-size: .8rem; color: var(--muted); font-weight: 700; }
  .tradebar { position: fixed; left: 0; right: 0; bottom: 0; z-index: 21; background: var(--bg); border-top: 1px solid var(--line);
    padding: 12px 18px calc(12px + env(safe-area-inset-bottom, 0)); display: flex; gap: 10px; }
  .tradebar .inner { max-width: 524px; margin: 0 auto; width: 100%; display: flex; gap: 10px; }

  /* Order sheet */
  .scrim { position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 30; }
  .sheet { position: fixed; left: 0; right: 0; bottom: 0; z-index: 31; background: var(--surface); border-radius: 22px 22px 0 0;
    padding: 18px 18px calc(18px + env(safe-area-inset-bottom, 0)); max-width: 560px; margin: 0 auto; display: grid; gap: 14px; }
  .sheet h3 { margin: 0; font-size: 1.2rem; font-weight: 800; }
  .seg { display: flex; background: var(--sunk); border-radius: 999px; padding: 4px; }
  .seg button { flex: 1; border: 0; background: none; padding: 8px; border-radius: 999px; font-weight: 700; color: var(--muted); }
  .seg button.on { background: var(--surface); color: var(--ink); box-shadow: 0 1px 3px rgba(0,0,0,.12); }
  .amount { font-size: 2.6rem; font-weight: 800; text-align: center; border: 0; background: none; padding: 4px; letter-spacing: -0.03em; }
  .est { text-align: center; color: var(--muted); font-size: .92rem; }
  .review div { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--line); }

  .strip { display: flex; gap: 8px; overflow-x: auto; margin: 14px -18px 0; padding: 0 18px 4px; scrollbar-width: none; }
  .strip::-webkit-scrollbar { display: none; }
  .mkt { flex: none; border: 1px solid var(--line); background: var(--surface); border-radius: 12px; padding: 8px 12px; text-align: left; min-width: 104px; }
  .mkt b { display: block; font-size: .78rem; color: var(--muted); font-weight: 700; }
  .mkt span { font-weight: 800; font-size: .95rem; }
  .bar { height: 8px; border-radius: 99px; background: var(--sunk); overflow: hidden; margin-top: 6px; }
  .bar i { display: block; height: 100%; background: var(--gold); border-radius: 99px; }
  .cards { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .card2 { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 12px; }
  .card2 .big { font-size: 1.3rem; font-weight: 800; }
  .legend { display: flex; gap: 16px; font-size: .85rem; margin-top: 8px; }
  .legend i { display: inline-block; width: 12px; height: 3px; border-radius: 2px; vertical-align: middle; margin-right: 6px; }
  .chart .line2 { fill: none; stroke: var(--muted); stroke-width: 2; stroke-dasharray: 4 4; }
  .chart .line1 { fill: none; stroke: var(--gold); stroke-width: 2.25; }
  .tick { display: inline-flex; gap: 6px; flex-wrap: wrap; }
  .tickbtn { border: 1px solid var(--line); background: var(--surface); border-radius: 999px; padding: 4px 10px; font-weight: 700; font-size: .82rem; }
  .brief { margin-top: 16px; background: var(--surface); border: 1px solid var(--line); border-left: 4px solid var(--gold); border-radius: 14px; padding: 12px 14px; }
  .brief summary { list-style: none; cursor: pointer; font-weight: 800; }
  .brief summary::-webkit-details-marker { display: none; }
  .brief .txt { white-space: pre-wrap; font-size: .93rem; margin-top: 8px; }
  .chat { display: grid; gap: 10px; margin-top: 16px; }
  .msg { max-width: 88%; padding: 10px 13px; border-radius: 16px; white-space: pre-wrap; overflow-wrap: anywhere; font-size: .95rem; }
  .msg.user { justify-self: end; background: var(--gold); color: var(--gold-ink); border-bottom-right-radius: 4px; }
  .msg.bot { justify-self: start; background: var(--surface); border: 1px solid var(--line); border-bottom-left-radius: 4px; }
  .suggest { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
  .askbar { position: sticky; bottom: calc(70px + env(safe-area-inset-bottom, 0)); margin-top: 16px; padding: 10px 0; background: var(--bg); display: flex; gap: 8px; align-items: flex-end; }
  .askbar textarea { min-height: 46px; max-height: 140px; border-radius: 22px; padding: 11px 14px; }
  .askbar button { flex: none; border-radius: 999px; width: auto; padding: 12px 18px; }
  .ccard { padding: 14px 0; border-bottom: 1px solid var(--line); }
  .ccard .head { display: flex; align-items: center; gap: 10px; }
  .ccard .head .grow { flex: 1; min-width: 0; }
  .ccard .name { font-size: .82rem; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .metric { display: grid; grid-template-columns: 92px 1fr 78px; align-items: center; gap: 8px; margin-top: 7px; font-size: .82rem; }
  .metric .lbl { color: var(--muted); }
  .metric .val { text-align: right; font-weight: 700; }
  .track { height: 10px; border-radius: 99px; background: var(--sunk); overflow: hidden; }
  .track i { display: block; height: 100%; border-radius: 99px; background: var(--gold); }
  .track i.g { background: var(--gain); } .track i.r { background: var(--loss); } .track i.y { background: #E0A800; }
  .chips { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 9px; }
  .chip2 { font-size: .78rem; font-weight: 700; padding: 3px 9px; border-radius: 999px; }
  .chip2.g { background: color-mix(in srgb, var(--gain) 16%, transparent); color: var(--gain); }
  .chip2.y { background: color-mix(in srgb, #E0A800 18%, transparent); color: #B98900; }
  .chip2.r { background: color-mix(in srgb, var(--loss) 15%, transparent); color: var(--loss); }
  .chip2.n { background: var(--sunk); color: var(--muted); }
  .controls { display: flex; gap: 8px; margin-top: 12px; }
  .controls select { flex: 1; }
  .sum { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 14px; }
  .sum .card2 .big { font-size: 1.15rem; }
  .stat { font-size: .74rem; font-weight: 800; padding: 2px 8px; border-radius: 999px; }
  .stat.filled { background: color-mix(in srgb, var(--gain) 16%, transparent); color: var(--gain); }
  .stat.pending { background: color-mix(in srgb, #E0A800 18%, transparent); color: #B98900; }
  .stat.canceled { background: var(--sunk); color: var(--muted); }
  .stat.rejected { background: color-mix(in srgb, var(--loss) 15%, transparent); color: var(--loss); }
  .src { font-size: .74rem; color: var(--muted); }
  .stack { display: flex; height: 12px; border-radius: 99px; overflow: hidden; margin-top: 8px; background: var(--sunk); }
  .stack i { display: block; height: 100%; }
  .logo { width: 34px; height: 34px; border-radius: 9px; object-fit: contain; background: #fff; border: 1px solid var(--line); flex: none; }
  .note { margin-top: 12px; padding: 9px 12px; border-radius: 10px; font-size: .86rem; background: color-mix(in srgb, #E0A800 14%, var(--surface)); }
  .gear { border: 0; background: none; padding: 6px; color: var(--muted); display: grid; place-items: center; }
  .gear svg { width: 22px; height: 22px; }
  .sgroup { margin-top: 30px; }
  .sgroup h2 { margin: 0 0 4px; }
  .field { display: grid; gap: 4px; padding: 12px 0; border-bottom: 1px solid var(--line); }
  .field > span { font-weight: 700; color: var(--ink); font-size: .95rem; }
  .field small { color: var(--muted); font-size: .82rem; }
  .savebar { position: sticky; bottom: calc(70px + env(safe-area-inset-bottom, 0)); margin-top: 20px; padding: 10px 0; background: var(--bg); }
  .kv { display: flex; justify-content: space-between; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--line); }
  nav { position: fixed; left: 0; right: 0; bottom: 0; z-index: 10; display: flex; background: var(--surface); border-top: 1px solid var(--line);
    padding: 6px 6px calc(6px + env(safe-area-inset-bottom, 0)); }
  nav button { flex: 1; border: 0; background: none; color: var(--muted); font-size: .76rem; font-weight: 700; padding: 10px 2px; border-radius: 10px; }
  nav button.active { color: var(--ink); background: var(--sunk); }

  .toast { position: fixed; left: 50%; bottom: calc(92px + env(safe-area-inset-bottom, 0)); transform: translateX(-50%); z-index: 40; background: var(--ink); color: var(--bg);
    padding: 10px 16px; border-radius: 12px; font-size: .9rem; max-width: 90vw; opacity: 0; transition: opacity .2s; pointer-events: none; }
  .toast.show { opacity: 1; }
  .pcard { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 12px 14px; margin-top: 10px; }
  .rbar { margin-top: 12px; }
  .rtrack { position: relative; height: 12px; border-radius: 99px; background: var(--sunk); margin: 0 8px; }
  .rtrack i { position: absolute; top: 0; bottom: 0; }
  .rtrack .rloss { background: color-mix(in srgb, var(--loss) 40%, transparent); border-radius: 99px 0 0 99px; }
  .rtrack .rgain { background: color-mix(in srgb, var(--gain) 40%, transparent); border-radius: 0 99px 99px 0; }
  .rtrack b { position: absolute; top: 50%; transform: translate(-50%, -50%); }
  .rtrack .rentry { width: 2px; height: 20px; background: var(--ink); }
  .rtrack .rnow { width: 18px; height: 18px; border-radius: 50%; border: 3px solid var(--surface); background: var(--gain); box-shadow: 0 1px 3px rgba(0,0,0,.35); }
  .rtrack .rnow.down { background: var(--loss); }
  .rlabs { display: flex; justify-content: space-between; gap: 6px; font-size: .74rem; font-weight: 700; margin-top: 8px; }
  .tl { display: flex; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid var(--line); }
  .tl .t { width: 58px; flex: none; font-size: .78rem; color: var(--muted); font-weight: 700; }
  .tl .grow { flex: 1; min-width: 0; }
  .tl .right { text-align: right; }
  .ic { width: 26px; height: 26px; flex: none; border-radius: 50%; display: grid; place-items: center; font-weight: 800; font-size: .78rem; }
  .ic.buy { background: color-mix(in srgb, var(--gold) 22%, transparent); color: var(--gold); }
  .ic.win { background: color-mix(in srgb, var(--gain) 18%, transparent); color: var(--gain); }
  .ic.lose { background: color-mix(in srgb, var(--loss) 16%, transparent); color: var(--loss); }
  .wr { display: grid; grid-template-columns: 84px 1fr 78px; gap: 10px; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--line); font-size: .9rem; }
  .wr .right { text-align: right; }
  .hb { margin-top: 14px; font-size: .8rem; color: var(--muted); font-weight: 600; }
  .pulse { display: inline-block; width: 9px; height: 9px; border-radius: 50%; background: var(--gain); margin-right: 6px; vertical-align: middle; }
  .pulse.off { background: var(--muted); }
  @media (prefers-reduced-motion: no-preference) { .pulse:not(.off) { animation: pulse 1.6s infinite; } @keyframes pulse { 50% { opacity: .25; } } }
  .lstrip { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 10px; }
  .lstrip .card2 { padding: 9px 10px; } .lstrip .big { font-size: 1.1rem; }
  .stage { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 12px 14px; }
  .stg-h { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
  .stg-i { display: inline-grid; place-items: center; width: 22px; height: 22px; border-radius: 50%; background: var(--gold); color: var(--gold-ink); font-size: .75rem; font-weight: 800; margin-right: 8px; }
  .stg-n { font-weight: 800; font-size: .85rem; background: var(--sunk); border-radius: 99px; padding: 2px 10px; }
  .flow { text-align: center; color: var(--muted); font-weight: 800; line-height: 1; padding: 4px 0; }
  .nrow { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-top: 1px solid var(--line); cursor: pointer; }
  .nrow .grow { flex: 1; min-width: 0; } .nrow .close { width: 82px; flex: none; text-align: right; }
  .ltrade { padding: 10px 0; border-top: 1px solid var(--line); }
  .ic.skip, .ic.status { background: var(--sunk); color: var(--muted); }
  .ic.order { background: color-mix(in srgb, #E0A800 18%, transparent); color: #B98900; }
  @media (min-width: 1100px) { .lstrip { grid-template-columns: repeat(6, 1fr); } }
  .risk { display: inline-flex; gap: 3px; margin-right: 6px; vertical-align: middle; }
  .risk i { width: 14px; height: 6px; border-radius: 3px; background: var(--sunk); }
  .risk i.on.r1 { background: var(--gain); } .risk i.on.r2 { background: #E0A800; } .risk i.on.r3 { background: var(--loss); }
  .mgrid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 10px; }
  .mgrid div { background: var(--sunk); border-radius: 10px; padding: 8px; text-align: center; }
  .mgrid b { display: block; font-size: 1.05rem; font-weight: 800; }
  .mgrid span { font-size: .72rem; color: var(--muted); }
  .pnlbar { position: relative; height: 10px; border-radius: 99px; background: var(--sunk); }
  .pnlbar i { position: absolute; top: 0; bottom: 0; border-radius: 99px; }
  .pnlbar i.g { background: var(--gain); } .pnlbar i.r { background: var(--loss); }
  .pnlbar b { position: absolute; left: 50%; top: -3px; bottom: -3px; width: 1px; background: var(--muted); }
  @media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
  @media (min-width: 1100px) {
    main { max-width: 960px; padding: 18px 32px 32px; }
    main.wide { max-width: 80vw; }
    .homegrid { display: grid; grid-template-columns: minmax(260px, 1fr) minmax(420px, 1.7fr) minmax(260px, 1fr); gap: 40px; align-items: start; }
    .homegrid .col { display: block; min-width: 0; }
    .homegrid .col-left h2:first-child, .homegrid .col-right h2:first-child { margin-top: 22px; }
    .chart { height: 300px; }
    .cards, .sum { grid-template-columns: repeat(4, 1fr); }
    #cmpList { display: grid; grid-template-columns: repeat(2, 1fr); column-gap: 36px; }
    #detail main { max-width: 960px; }
    .tradebar .inner { max-width: 896px; }
    nav { justify-content: center; }
    nav button { flex: 0 1 150px; }
    .toast { bottom: 96px; }
  }
</style>
</head>
<body>
<main id="view"><p class="muted" style="padding:40px 0">Loading GOLDMINEBOT…</p></main>
<section id="detail" aria-live="polite"></section>
<div id="sheetHost"></div>

<nav id="nav">
  <button data-tab="home" class="active">Home</button>
  <button data-tab="alpaca">Alpaca</button>
  <button data-tab="live">Live</button>
  <button data-tab="intel">Intel</button>
  <button data-tab="trading">Trading</button>
  <button data-tab="more">More</button>
</nav>
<div class="toast" id="toast" role="status" aria-live="polite"></div>

<script>
const KEY = <?!= JSON.stringify(key) ?>;
const STRATS = [
  { id: 'orb', name: 'Opening range breakout', text: 'Buys the first break above the opening range high on strong volume. Hours follow Settings.' },
  { id: 'vwap', name: 'VWAP pullback', text: 'Buys uptrending stocks when they dip to VWAP and bounce (Aggressive also buys VWAP reclaims).' },
  { id: 'momentum', name: 'Top gainers momentum', text: 'Buys stocks making a new high of the day above VWAP. Hours follow Settings.' }
];
const RANGES = ['1D', '1W', '1M', '3M', '1Y', 'ALL'];
const RANGE_LABEL = { '1D': 'Today', '1W': 'Past week', '1M': 'Past month', '3M': 'Past 3 months', '1Y': 'Past year', 'ALL': 'All time' };

let D = null, hist = null, tab = 'home', busy = false, pillMode = 'price';
let stock = null, stockRange = '1D', order = null, lastEvent = '';

// ---------- helpers ----------
const $ = (id) => document.getElementById(id);
function call(fn, ...args) {
  return new Promise((resolve, reject) => google.script.run.withSuccessHandler(resolve).withFailureHandler(reject)[fn](...args));
}
function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
function money(n) { return Number(n || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD' }); }
function price(n) { n = Number(n || 0); return n > 0 && n < 1 ? '$' + n.toFixed(4) : money(n); }
function signed(n) { return (n >= 0 ? '+' : '−') + money(Math.abs(n)); }
function pct(n) { return (n >= 0 ? '+' : '−') + Math.abs(n || 0).toFixed(2) + '%'; }
function compact(n) { return n == null ? '—' : Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(n); }
function isOn(v) { return String(v).toUpperCase() === 'TRUE'; }
function toast(msg) { const t = $('toast'); t.textContent = msg; t.classList.add('show'); clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove('show'), Math.max(3400, String(msg).length * 60)); }
function when(t, range) {
  const d = new Date(t);
  if (range === '1D') return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  if (range === '1W') return d.toLocaleString('en-US', { weekday: 'short', hour: 'numeric', minute: '2-digit' });
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: (range === '1Y' || range === 'ALL') ? 'numeric' : undefined });
}
function ago(t) {
  const m = Math.round((Date.now() - new Date(t)) / 60000);
  if (m < 60) return m + 'm'; if (m < 1440) return Math.round(m / 60) + 'h'; return Math.round(m / 1440) + 'd';
}
function setTrend(up) { document.documentElement.dataset.trend = up ? 'up' : 'down'; }

// ---------- charts ----------
function scale(points, base, baseline, H, pad) {
  const vals = points.map((p) => p.v); if (baseline && base) vals.push(base);
  let min = Math.min(...vals), max = Math.max(...vals);
  if (max === min) { max += 1; min -= 1; }
  return (v) => pad + (H - 2 * pad) * (1 - (v - min) / (max - min));
}
function pathFor(points, W, y) {
  return points.map((p, i) => (i ? 'L' : 'M') + (points.length === 1 ? W / 2 : i * W / (points.length - 1)).toFixed(1) + ' ' + y(p.v).toFixed(1)).join(' ');
}
function bigChart(c, id, fmt) {
  const W = 360, H = 190, pad = 12;
  fmt = fmt || price;
  if (!c || c.points.length < 2) return `<div class="chart" id="${id}"><div class="flat">Not enough history yet</div></div>`;
  const baseline = c.range === '1D';
  const y = scale(c.points, c.base, baseline, H, pad);
  const bl = baseline ? `<line class="baseline" x1="0" x2="${W}" y1="${y(c.base).toFixed(1)}" y2="${y(c.base).toFixed(1)}"/>` : '';
  const vals = c.points.map((p) => p.v), hi = Math.max(...vals), lo = Math.min(...vals);
  const first = c.points[0].t, last = c.points[c.points.length - 1].t;
  const d = (t) => c.range === '1D' ? new Date(t).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }) : new Date(t).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: c.range === 'ALL' || c.range === '1Y' ? 'numeric' : undefined });
  return `<div class="chart" id="${id}"><svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">${bl}<path class="line" vector-effect="non-scaling-stroke" d="${pathFor(c.points, W, y)}"/></svg>
    <span class="ylab" style="top:2px">High ${fmt(hi)}</span><span class="ylab" style="bottom:2px">Low ${fmt(lo)}</span><div class="cursor"></div><div class="dot"></div></div>
    <div class="xlabs"><span>${esc(d(first))}</span><span>${Date.now() - last < 36 * 3600000 ? 'Now' : esc(d(last))}</span></div>`;
}
function sparkline(vals, up) {
  if (!vals || vals.length < 2) return '<svg class="spark"></svg>';
  const pts = vals.map((v) => ({ v })), y = scale(pts, 0, false, 30, 2);
  return `<svg class="spark ${up ? 'up' : 'down'}" viewBox="0 0 76 30" preserveAspectRatio="none"><path vector-effect="non-scaling-stroke" d="${pathFor(pts, 76, y)}"/></svg>`;
}
function bindScrub(id, c, onMove, onEnd) {
  const wrap = $(id); if (!wrap || !c || c.points.length < 2) return;
  const y = scale(c.points, c.base, c.range === '1D', 190, 12), n = c.points.length;
  const cur = wrap.querySelector('.cursor'), dot = wrap.querySelector('.dot');
  let active = false;
  const at = (x) => {
    const r = wrap.getBoundingClientRect();
    const i = Math.round(Math.max(0, Math.min(1, (x - r.left) / r.width)) * (n - 1));
    const left = (i / (n - 1) * 100) + '%';
    cur.style.left = left; dot.style.left = left; dot.style.top = (y(c.points[i].v) / 190 * 100) + '%';
    wrap.classList.add('scrubbing'); onMove(c.points[i]);
  };
  const end = () => { if (!active) return; active = false; wrap.classList.remove('scrubbing'); onEnd(); };
  wrap.addEventListener('pointerdown', (e) => { active = true; try { wrap.setPointerCapture(e.pointerId); } catch (_) {} at(e.clientX); });
  wrap.addEventListener('pointermove', (e) => { if (active || e.pointerType === 'mouse') { active = true; at(e.clientX); } });
  ['pointerup', 'pointercancel', 'pointerleave'].forEach((ev) => wrap.addEventListener(ev, end));
}
function pill(q) {
  if (!q || !q.price) return '<span class="pill flat">—</span>';
  const up = q.change >= 0;
  const text = pillMode === 'price' ? price(q.price) : pillMode === 'pct' ? pct(q.pct) : signed(q.change);
  return `<span class="pill ${up ? '' : 'down'}" data-do="pill">${text}</span>`;
}

// ---------- loading ----------
function load(quiet) {
  if (!quiet) busy = true;
  call('getDashboard', KEY).then((d) => {
    D = d; if (!hist || hist.range === '1D') hist = d.history || null; busy = false; render();
  }).catch((e) => { busy = false; $('view').innerHTML = '<div class="notice bad" style="margin-top:20px">' + esc(e.message || e) + '</div>'; });
}
function act(promise, message) {
  busy = true; render();
  return promise.then((d) => { if (d && d.settings) D = d; busy = false; render(); if (message) toast(message); })
    .catch((e) => { busy = false; render(); toast(e.message || String(e)); });
}

// ---------- header ----------
function header() {
  const live = D.mode === 'LIVE';
  return `<div class="top"><span class="brand">GOLDMINEBOT</span><span class="chip ${live ? 'live' : ''}">${live ? 'Live money' : 'Paper money'}</span>
    <span class="spacer"></span><button class="ghost" data-do="refresh" ${busy ? 'disabled' : ''}>${busy ? 'Updating…' : 'Refresh'}</button>
    <button class="gear" data-do="settings" aria-label="Settings"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg></button></div>`;
}

// ---------- Home ----------
const RANGE_DAYS = { '1W': 7, '1M': 31, '3M': 92, '1Y': 366, 'ALL': 99999 };
// The account history, with today's current value as the last point so the line ends where the big number is
function homeChart() {
  if (!hist || !hist.points.length || !D.account) return hist;
  const pts = hist.points.slice(), now = Date.now(), eq = D.account.equity;
  const lastP = pts[pts.length - 1];
  const sameDay = new Date(lastP.t).toDateString() === new Date(now).toDateString();
  if (hist.range === '1D') { if (now - lastP.t > 10 * 60000 && D.marketOpen) pts.push({ t: now, v: eq }); }
  else if (sameDay) pts[pts.length - 1] = { t: lastP.t, v: eq };
  else pts.push({ t: now, v: eq });
  return { range: hist.range, base: hist.base, points: pts };
}
function heroNumbers() {
  const a = D.account; if (!a) return null;
  const c = homeChart();
  if (!c || !c.points.length || c.range === '1D') return { value: a.equity, change: a.dayPnl, pctv: a.dayPct, label: RANGE_LABEL['1D'] };
  const first = c.points[0].v, last = a.equity;
  const startT = c.points[0].t, ageDays = (Date.now() - startT) / 86400000;
  const short = c.range === 'ALL' || ageDays < RANGE_DAYS[c.range] * 0.85;
  const label = short ? 'Since ' + new Date(startT).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + (c.range === 'ALL' || ageDays < 60 ? ' (account start)' : '') : RANGE_LABEL[c.range];
  return { value: last, change: last - first, pctv: first ? (last - first) / first * 100 : 0, label: label };
}
function homeView() {
  let top = header();
  top += `<form class="search" id="searchForm"><svg viewBox="0 0 24 24" fill="none" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
    <input name="q" placeholder="Search a ticker or company name" autocapitalize="characters" autocomplete="off" enterkeyhint="search"></form>`;
  if (D.alpacaError) return top + `<div class="notice bad" style="margin-top:18px">Couldn’t reach Alpaca. ${esc(D.alpacaError)}</div>`;
  if (D.market && D.market.length) top += '<div class="strip">' + D.market.filter((m) => m.price).map((m) =>
    `<button class="mkt" ${m.crypto ? '' : `data-open="${esc(m.symbol)}"`}><b>${esc(m.label)}</b><span class="${m.pct >= 0 ? 'gain' : 'loss'}">${pct(m.pct)}</span></button>`).join('') + '</div>';

  // Center: value, chart, account links
  let main = '';
  if (D.calendar && D.calendar.length) {
    const c = D.calendar[0];
    main += `<div class="note">📅 ${c.type === 'closed' ? 'Market closed' : 'Early close at ' + esc(fmtTime(c.close))} ${esc(fmtDay(c.date))}${D.calendar.length > 1 ? ' · then ' + D.calendar.slice(1, 3).map((x) => (x.type === 'closed' ? 'closed ' : 'early close ') + fmtDay(x.date)).join(', ') : ''}</div>`;
  }
  const n = heroNumbers(); setTrend(n.change >= 0);
  main += `<div class="hero"><div class="value" id="heroValue">${money(n.value)}</div>
    <div class="delta" id="heroDelta">${signed(n.change)} (${pct(n.pctv)}) <span class="muted">${n.label}</span></div></div>`;
  main += `<p class="chartnote">${D.mode === 'LIVE' ? 'Your Alpaca account' : 'Your Alpaca practice account (paper money)'}: cash + stocks. Robinhood and crypto are not included.</p>`;
  main += bigChart(homeChart(), 'pchart', money);
  main += `<div class="ranges">${RANGES.map((r) => `<button data-do="range" data-range="${r}" class="${hist && hist.range === r ? 'on' : ''}">${r}</button>`).join('')}</div>`;
  const rl = 'style="width:100%;background:none;border-left:0;border-right:0;border-top:0;cursor:pointer"';
  main += `<div class="rowlink"><span>Buying power</span><strong>${money(D.account.buyingPower)}</strong></div>
    <button class="rowlink" data-do="portfolio" ${rl}><span>Portfolio breakdown</span><span class="muted">›</span></button>
    <button class="rowlink" data-do="gotab" data-tab="alpaca" ${rl}><span>Alpaca account${D.openOrders ? ' · <strong style="color:#B98900">' + D.openOrders + ' pending order' + (D.openOrders > 1 ? 's' : '') + '</strong>' : ''}</span><span class="muted">›</span></button>
    <button class="rowlink" data-do="compare" ${rl}><span>Compare companies${D.compare && D.compare.length ? ' (' + D.compare.length + ')' : ''}</span><span class="muted">›</span></button>`;

  let stocks = '<h2>Stocks</h2>';
  if (!D.positions.length) stocks += '<p class="empty">You don’t own any stocks yet. Search a ticker to buy, or turn on the bot.</p>';
  D.positions.forEach((p) => {
    const q = D.quotes[p.symbol] || { price: p.price, change: p.change, pct: p.change };
    stocks += `<button class="item" data-open="${esc(p.symbol)}"><span><span class="sym">${esc(p.symbol)}</span><br><span class="sub">${+p.qty.toFixed(4)} shares</span></span>
      ${sparkline(q.spark, q.change >= 0)}${pill(q)}</button>`;
  });
  let watch = '<h2>Watchlist</h2>';
  if (!D.watchlist.length) watch += `<p class="empty">Star a stock to follow it here.</p><button class="outline" data-do="seed" ${busy ? 'disabled' : ''}>Add SPY, QQQ and GLD</button>`;
  D.watchlist.forEach((s) => {
    const q = D.quotes[s];
    watch += `<button class="item" data-open="${esc(s)}"><span><span class="sym">${esc(s)}</span><br><span class="sub">${q ? pct(q.pct) + ' today' : ''}</span></span>
      ${sparkline(q && q.spark, q ? q.change >= 0 : true)}${pill(q)}</button>`;
  });
  const sec = (o, html) => `<section style="order:${o}">${html}</section>`;
  // Desktop: three columns (left / center / right). Phone: one column in the `order` shown.
  return top + `<div class="homegrid">
    <div class="col col-left">${sec(2, stocks)}${sec(3, watch)}${sec(8, cryptoSection())}</div>
    <div class="col col-center">${sec(1, main)}${sec(5, earningsSection())}${sec(6, iposSection())}</div>
    <div class="col col-right">${sec(4, moversSection())}${sec(7, otherAccountsSection())}</div></div>
    <p class="muted small" style="margin-top:22px">${D.marketOpen ? 'Market open' : 'Market closed'}. Updated ${esc(D.updated)} ET.</p>`;
}
function afterHome() {
  if (!D || D.alpacaError || !hist) return;
  const n = heroNumbers(), hc = homeChart();
  bindScrub('pchart', hc, (p) => {
    const base = hc.range === '1D' ? hc.base : hc.points[0].v, ch = p.v - base;
    setTrend(ch >= 0);
    $('heroValue').textContent = money(p.v);
    $('heroDelta').innerHTML = `${signed(ch)} (${pct(base ? ch / base * 100 : 0)}) <span class="muted">${esc(when(p.t, hist.range))}</span>`;
  }, () => {
    setTrend(n.change >= 0);
    $('heroValue').textContent = money(n.value);
    $('heroDelta').innerHTML = `${signed(n.change)} (${pct(n.pctv)}) <span class="muted">${n.label}</span>`;
  });
}

// ---------- Stock detail ----------
function openStock(sym, side) {
  stock = { symbol: sym, loading: true }; stockRange = '1D'; order = null;
  $('detail').classList.add('open'); $('detail').scrollTop = 0; renderDetail();
  call('getStock', KEY, sym, '1D').then((s) => { stock = s; renderDetail(); if (side && !s.error) openOrder(side); })
    .catch((e) => { stock = { symbol: sym, error: e.message || String(e) }; renderDetail(); });
}
function closeStock() { $('detail').classList.remove('open'); $('detail').innerHTML = ''; $('sheetHost').innerHTML = ''; stock = null; order = null; load(true); if (tab === 'trading') loadTrading(true); if (tab === 'live') loadLive(true); render(); }
function stockNumbers() {
  const s = stock, c = s.chart;
  if (stockRange === '1D' || !c.points.length) return { change: s.change, pctv: s.pct, label: 'Today' };
  const first = c.points[0].v;
  return { change: s.price - first, pctv: first ? (s.price - first) / first * 100 : 0, label: RANGE_LABEL[stockRange] };
}
function renderDetail() {
  const el = $('detail'); if (!stock) return;
  let h = `<main><div class="dtop"><button class="iconbtn" data-do="back" aria-label="Back">‹</button>`;
  if (stock.loading || stock.error) {
    h += `</div><div class="dsym">${esc(stock.symbol)}</div>` + (stock.error ? `<div class="notice bad" style="margin-top:16px">${esc(stock.error)}</div>` : '<p class="muted" style="margin-top:20px">Loading…</p>') + '</main>';
    el.innerHTML = h; return;
  }
  const s = stock, n = stockNumbers(); setTrend(n.change >= 0);
  h += `<span><button class="tickbtn" data-do="addcompare" data-sym="${esc(s.symbol)}" style="margin-right:6px">+ Compare</button><button class="iconbtn star ${s.watch ? 'on' : ''}" data-do="star" aria-label="${s.watch ? 'Remove from watchlist' : 'Add to watchlist'}">${s.watch ? '★' : '☆'}</button></span></div>
    <div style="display:flex;gap:10px;align-items:center;margin-top:8px">${s.extras && s.extras.logo ? `<img class="logo" src="${esc(s.extras.logo)}" alt="">` : ''}
      <div><div class="dsym" style="margin-top:0">${esc(s.symbol)}</div><p class="muted" style="margin:0">${esc(s.name)}</p></div></div>
    ${s.extras && (s.extras.web || s.extras.ipo || s.extras.industry) ? `<p class="muted small" style="margin-top:6px">${[s.extras.industry ? esc(s.extras.industry) : '', s.extras.ipo ? 'Public since ' + esc(String(s.extras.ipo).slice(0, 4)) : '', s.extras.web ? `<a href="${esc(/^https?:/.test(s.extras.web) ? s.extras.web : '#')}" target="_blank" rel="noopener">Website</a>` : ''].filter(Boolean).join(' · ')}</p>` : ''}
    <div class="hero" style="margin-top:12px"><div class="value" id="sValue">${price(s.price)}</div>
    <div class="delta" id="sDelta">${signed(n.change)} (${pct(n.pctv)}) <span class="muted">${n.label}</span></div></div>
    ${bigChart(s.chart, 'schart')}
    <div class="ranges">${RANGES.map((r) => `<button data-do="srange" data-range="${r}" class="${stockRange === r ? 'on' : ''}">${r}</button>`).join('')}</div>`;
  if (s.position) {
    const p = s.position;
    h += `<h2>Your position</h2><div class="stats">
      <div><span>Shares</span><span>${+p.qty.toFixed(4)}</span></div><div><span>Market value</span><span>${money(p.value)}</span></div>
      <div><span>Average cost</span><span>${price(p.avg)}</span></div><div><span>Today’s return</span><span class="${p.todayPl >= 0 ? 'gain' : 'loss'}">${signed(p.todayPl)}</span></div>
      <div style="grid-column:1/-1"><span>Total return</span><span class="${p.pl >= 0 ? 'gain' : 'loss'}">${signed(p.pl)} (${pct(p.plpc)})</span></div></div>`;
  }
  if (s.orders && s.orders.length) {
    h += '<h2>Open orders</h2>' + s.orders.map((o) => `<div class="row"><div class="grow"><strong>${o.side === 'buy' ? 'Buy' : 'Sell'} ${o.qty ? +Number(o.qty).toFixed(4) + ' sh' : money(o.notional)}</strong>
      <div class="muted small">${esc(o.type)}${o.limit ? ' at ' + price(o.limit) : ''}${o.stop ? ' stop ' + price(o.stop) : ''} · ${o.tif === 'gtc' ? 'good until canceled' : 'today only'}${o.mine ? '' : ' · bot'}</div></div>
      ${o.mine ? `<button class="del" data-do="cancelorder" data-id="${esc(o.id)}">Cancel</button>` : ''}</div>`).join('');
  }
  const elsewhere = (D.other || []).filter((x) => x.symbol === s.symbol);
  if (elsewhere.length) {
    h += '<h2>In your other accounts</h2><div class="stats">' + elsewhere.map((x) =>
      `<div style="grid-column:1/-1"><span>${esc(x.account)}</span><span>${+x.shares.toFixed(6)} shares · ${money(x.shares * s.price)}${x.cost ? ' · <span class="' + (s.price >= x.cost ? 'gain' : 'loss') + '">' + signed((s.price - x.cost) * x.shares) + '</span>' : ''}</span></div>`).join('') + '</div>';
  }
  const f = (v) => v == null ? '—' : price(v);
  h += `<h2>Stats</h2><div class="stats">
    <div><span>Open</span><span>${f(s.open)}</span></div><div><span>Volume</span><span>${compact(s.volume)}</span></div>
    <div><span>High</span><span>${f(s.high)}</span></div><div><span>52 wk high</span><span>${f(s.w52h)}</span></div>
    <div><span>Low</span><span>${f(s.low)}</span></div><div><span>52 wk low</span><span>${f(s.w52l)}</span></div>
    <div><span>Prev close</span><span>${f(s.prev)}</span></div><div><span>Exchange</span><span>${esc(s.exchange || '—')}</span></div></div>
    <p class="muted small" style="margin-top:8px">Volume is from the free IEX feed, a slice of total market volume.</p>`;
  h += stockExtras(s);
  if (s.earnings) h += `<div class="notice" style="margin-top:14px">Next earnings: <strong>${esc(fmtDay(s.earnings.date))}</strong> ${esc(hourLabel(s.earnings.hour))}${s.earnings.epsEstimate != null ? ' · expected EPS ' + Number(s.earnings.epsEstimate).toFixed(2) : ''}</div>`;
  h += '<h2>News</h2><div class="news">';
  if (!s.news.length) h += '<p class="empty">No recent news.</p>';
  s.news.forEach((a) => { h += `<a href="${esc(/^https?:/.test(a.url) ? a.url : '#')}" target="_blank" rel="noopener"><span class="src">${esc(a.source)} · ${ago(a.time)}</span><br>${esc(a.headline)}</a>`; });
  h += '</div></main>';
  if (s.tradable) h += `<div class="tradebar"><div class="inner">${s.position ? '<button class="outline" data-do="trade" data-side="sell">Sell</button>' : ''}<button class="primary" data-do="trade" data-side="buy">Buy</button></div></div>`;
  el.innerHTML = h;
  bindScrub('schart', s.chart, (p) => {
    const base = stockRange === '1D' ? (s.chart.base || s.prev) : s.chart.points[0].v, ch = p.v - base;
    setTrend(ch >= 0);
    $('sValue').textContent = price(p.v);
    $('sDelta').innerHTML = `${signed(ch)} (${pct(base ? ch / base * 100 : 0)}) <span class="muted">${esc(when(p.t, stockRange))}</span>`;
  }, () => {
    setTrend(n.change >= 0);
    $('sValue').textContent = price(s.price);
    $('sDelta').innerHTML = `${signed(n.change)} (${pct(n.pctv)}) <span class="muted">${n.label}</span>`;
  });
}


// ---------- Stock page: Finnhub details ----------
function stockExtras(s) {
  const x = s.extras || {};
  let h = '';
  const f2 = (v, suf) => v == null ? '—' : Number(v).toFixed(2) + (suf || '');
  const rows = [
    ['Beta (jumpiness)', x.beta == null ? '—' : x.beta.toFixed(2) + (x.beta > 1.3 ? ' · jumpier than market' : x.beta < 0.8 ? ' · calmer than market' : '')],
    ['Dividend yield', x.divYield == null || x.divYield === 0 ? 'None' : f2(x.divYield, '%')],
    ['Return on equity', f2(x.roe, '%')],
    ['Debt / equity', f2(x.de)],
    ['52-wk position', x.pos52 == null ? '—' : x.pos52.toFixed(0) + '% of range'],
    ['Bid / ask spread', s.spreadPct == null ? '—' : s.spreadPct.toFixed(2) + '%' + (s.spreadPct > 0.5 ? ' · wide' : '')]
  ];
  h += '<div class="stats" style="margin-top:6px">' + rows.map((r) => `<div><span>${r[0]}</span><span>${r[1]}</span></div>`).join('') + '</div>';
  if (s.spreadPct != null && s.spreadPct > 0.5) h += `<div class="note">The gap between buy and sell prices is ${s.spreadPct.toFixed(2)}%. Buying at market and selling right away would lose about that much. A limit order protects your price.</div>`;

  if (x.analysts) {
    const a = x.analysts, w = (n) => (n / a.total * 100).toFixed(1) + '%';
    const trend = a.buyPct3mAgo != null ? (a.buyPct > a.buyPct3mAgo + 2 ? ' · more bullish than 3 months ago' : a.buyPct < a.buyPct3mAgo - 2 ? ' · less bullish than 3 months ago' : ' · steady') : '';
    h += `<h2>Analysts</h2><p><strong>${a.buyPct.toFixed(0)}%</strong> rate it Buy <span class="muted small">(${a.total} analysts, ${esc(String(a.period).slice(0, 7))}${trend})</span></p>
      <div class="stack"><i style="width:${w(a.strongBuy)};background:#08784F"></i><i style="width:${w(a.buy)};background:var(--gain)"></i><i style="width:${w(a.hold)};background:#E0A800"></i><i style="width:${w(a.sell)};background:var(--loss)"></i><i style="width:${w(a.strongSell)};background:#9E2A22"></i></div>
      <p class="muted small" style="margin-top:6px">Strong buy ${a.strongBuy} · Buy ${a.buy} · Hold ${a.hold} · Sell ${a.sell} · Strong sell ${a.strongSell}</p>`;
  }
  if (x.earningsHist && x.earningsHist.length) {
    h += '<h2>Earnings: beat or miss</h2><div class="chips">' + x.earningsHist.map((e) => {
      const beat = e.actual != null && e.estimate != null ? e.actual >= e.estimate : null;
      return `<span class="chip2 ${beat == null ? 'n' : beat ? 'g' : 'r'}">Q${e.quarter} ${e.year} ${beat == null ? '—' : beat ? 'Beat' : 'Miss'}${e.surprisePct != null ? ' ' + pct(e.surprisePct) : ''}</span>`;
    }).join('') + '</div><p class="muted small" style="margin-top:6px">Earnings per share vs. what analysts expected.</p>';
  }
  if (x.insiders) {
    const i = x.insiders;
    h += `<h2>Insiders (last 90 days)</h2><p><span class="gain"><strong>${i.buys}</strong> buys${i.buyValue ? ' · ' + money(i.buyValue).replace('.00', '') : ''}</span> &nbsp; <span class="loss"><strong>${i.sells}</strong> sells${i.sellValue ? ' · ' + money(i.sellValue).replace('.00', '') : ''}</span></p>`;
    if (!i.buys && !i.sells) h += '<p class="muted small">No open-market buys or sells by executives.</p>';
    i.recent.forEach((t) => {
      h += `<div class="row"><div class="grow"><strong class="small">${esc(t.name)}</strong><div class="muted small">${esc(t.date)}</div></div>
        <div class="right small ${t.buy ? 'gain' : 'loss'}">${t.buy ? 'Bought' : 'Sold'} ${compact(t.shares)}${t.price ? ' @ ' + price(t.price) : ''}</div></div>`;
    });
    h += '<p class="muted small" style="margin-top:6px">Executives buying with their own money is a closely watched signal. Selling is common for many reasons (taxes, diversifying).</p>';
  }
  if (x.peers && x.peers.length) {
    h += `<h2>Similar companies</h2><div class="tick">${x.peers.map((p) => `<button class="tickbtn" data-open="${esc(p)}">${esc(p)}</button>`).join('')}</div>
      <button class="outline" style="margin-top:10px" data-do="peerscompare">Add ${esc(s.symbol)} and its peers to Compare</button>`;
  }
  return h;
}

// ---------- Order sheet ----------
function openOrder(side) {
  const canDollars = stock.fractionable;
  const def = Number(D.settingsValues && D.settingsValues.default_buy_amount) || '';
  const useDollars = side === 'buy' && canDollars && def;
  order = { side, type: 'market', price: '', mode: useDollars ? 'dollars' : 'shares', amount: useDollars ? String(def) : '', step: 'edit' };
  renderOrder();
}
function estimate() {
  const a = Number(order.amount), p = stock.price;
  if (order.mode === 'all') return stock.position ? `${+stock.position.qty.toFixed(4)} shares ≈ ${money(stock.position.qty * p)}` : '';
  const px = order.type !== 'market' && Number(order.price) > 0 ? Number(order.price) : p;
  if (order.type !== 'market' && a > 0 && px) return `≈ ${money(a * px)} if it fills at ${price(px)}`;
  if (!(a > 0) || !p) return `Market price ${price(p)}`;
  return order.mode === 'dollars' ? `≈ ${(a / p).toFixed(4)} shares at ${price(p)}` : `≈ ${money(a * p)} at ${price(p)}`;
}
function renderOrder() {
  const host = $('sheetHost');
  if (!order) { host.innerHTML = ''; return; }
  const s = stock, verb = order.side === 'buy' ? 'Buy' : 'Sell', live = D.mode === 'LIVE';
  let h = '<div class="scrim" data-do="closeorder"></div><div class="sheet" role="dialog" aria-label="' + verb + ' ' + esc(s.symbol) + '">';
  if (order.step === 'edit') {
    const modes = [];
    if (s.fractionable && order.type === 'market') modes.push(['dollars', 'Dollars']);
    modes.unshift(['shares', 'Shares']);
    if (order.side === 'sell' && s.position && order.type === 'market') modes.push(['all', 'Sell all']);
    const types = [['market', 'Market'], ['limit', 'Limit'], ['stop', 'Stop']];
    h += `<h3>${verb} ${esc(s.symbol)}</h3>
      <div class="seg">${types.map((t) => `<button data-do="otype" data-type="${t[0]}" class="${order.type === t[0] ? 'on' : ''}">${t[1]}</button>`).join('')}</div>
      <div class="seg">${modes.map((m) => `<button data-do="omode" data-mode="${m[0]}" class="${order.mode === m[0] ? 'on' : ''}">${m[1]}</button>`).join('')}</div>`;
    if (order.type !== 'market') h += `<label>${order.type === 'limit' ? (order.side === 'buy' ? 'Buy at or below' : 'Sell at or above') : (order.side === 'buy' ? 'Buy once it rises to' : 'Sell if it falls to')} ($)
      <input id="oPrice" type="number" inputmode="decimal" step="any" min="0" value="${esc(order.price)}" placeholder="${price(s.price)}"></label>`;
    if (order.mode !== 'all') h += `<input class="amount" id="oAmount" type="number" inputmode="decimal" step="any" min="0" placeholder="${order.mode === 'dollars' ? '$0' : '0'}" value="${esc(order.amount)}">`;
    h += `<p class="est" id="oEst">${estimate()}</p>
      ${s.position && order.side === 'sell' ? `<p class="est">You own ${+s.position.qty.toFixed(4)} shares</p>` : ''}
      ${!D.marketOpen && order.type === 'market' ? '<p class="est">Market is closed. Your order fills when it opens.</p>' : ''}
      ${order.type !== 'market' ? '<p class="est">Whole-share orders stay open until filled or canceled. Fractional ones last for today only.</p>' : ''}
      ${order.type === 'market' && s.spreadPct != null && s.spreadPct > 0.5 ? `<p class="note">Wide spread (${s.spreadPct.toFixed(2)}%): bid ${price(s.bid)}, ask ${price(s.ask)}. Consider a Limit order.</p>` : ''}
      <button class="primary" data-do="oreview">Review order</button>`;
  } else {
    const amt = order.mode === 'all' ? 'All shares' : order.mode === 'dollars' ? money(order.amount) : order.amount + ' shares';
    h += `<h3>Review ${verb.toLowerCase()}</h3><div class="review">
      <div><span class="muted">Stock</span><strong>${esc(s.symbol)}</strong></div>
      <div><span class="muted">Amount</span><strong>${amt}</strong></div>
      <div><span class="muted">Estimate</span><span>${estimate()}</span></div>
      <div><span class="muted">Order type</span><span>${order.type === 'market' ? 'Market' : (order.type === 'limit' ? 'Limit' : 'Stop') + ' at ' + price(order.price)}</span></div>
      <div><span class="muted">Account</span><span class="${live ? 'loss' : ''}">${live ? 'Live money' : 'Paper money'}</span></div></div>
      ${live ? '<p class="notice bad">This uses real money.</p>' : ''}
      <button class="primary" data-do="osubmit" ${busy ? 'disabled' : ''}>${busy ? 'Sending…' : 'Submit ' + verb.toLowerCase()}</button>
      <button class="outline" data-do="oedit">Edit</button>`;
  }
  host.innerHTML = h + '</div>';
  const inp = $('oAmount');
  if (inp) { inp.addEventListener('input', () => { order.amount = inp.value; $('oEst').textContent = estimate(); }); setTimeout(() => inp.focus(), 50); }
  const pin = $('oPrice');
  if (pin) pin.addEventListener('input', () => { order.price = pin.value; $('oEst').textContent = estimate(); });
}

// ---------- Bot ----------
function activeStrats() {
  const v = String(D.settings.strategy || 'all').toLowerCase();
  return v.indexOf('all') >= 0 ? STRATS.map((s) => s.id) : v.split(',').map((s) => s.trim());
}
// ---------- Trading tab (Bot trading + My trading) ----------
let trd = null, tradeSeg = 'bot';
const STRAT_NAME = { orb: 'Breakout', vwap: 'VWAP', momentum: 'Momentum', crypto: 'Crypto' };
function loadTrading(quiet) {
  if (!quiet) { trd = trd && !trd.error ? Object.assign(trd, { refreshing: true }) : { loading: true }; render(); }
  call('getTrading', KEY).then((t) => { trd = t; if (tab === 'trading' && !stock) render(); })
    .catch((e) => { if (!quiet || !trd || trd.loading) { trd = { error: e.message || String(e) }; render(); } });
}
function heldFor(from, to) {
  const m = Math.max(0, Math.round(((to ? new Date(to) : new Date()) - new Date(from)) / 60000));
  if (m < 60) return m + 'm';
  if (m < 1440) return Math.floor(m / 60) + 'h ' + (m % 60) + 'm';
  return Math.floor(m / 1440) + 'd ' + Math.floor((m % 1440) / 60) + 'h';
}
function clockTime(t) { return new Date(t).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }); }
function stratChip(s) { return `<span class="chip2 ${s === 'crypto' ? 'y' : 'n'}">${esc(STRAT_NAME[s] || s)}</span>`; }

// Stop ——— bought ——— target, with a dot where the price is now
function rangeBar(p) {
  if (!(p.stop > 0 && p.target > p.stop && p.price > 0)) return '<p class="src" style="margin-top:8px">Stop and target show once the orders are in place.</p>';
  const lo = Math.min(p.stop, p.price), hi = Math.max(p.target, p.price), span = hi - lo || 1;
  const x = (v) => (v - lo) / span * 100;
  const xs = x(p.stop), xe = x(p.entry), xt = x(p.target), xn = x(p.price);
  let where;
  if (p.price >= p.entry) where = `${Math.min(100, Math.round((p.price - p.entry) / (p.target - p.entry) * 100))}% of the way to the target`;
  else where = `${Math.min(100, Math.round((p.entry - p.price) / (p.entry - p.stop) * 100))}% of the way to the stop`;
  return `<div class="rbar"><div class="rtrack">
      <i class="rloss" style="left:${xs.toFixed(1)}%;width:${(xe - xs).toFixed(1)}%"></i><i class="rgain" style="left:${xe.toFixed(1)}%;width:${(xt - xe).toFixed(1)}%"></i>
      <b class="rentry" style="left:${xe.toFixed(1)}%"></b><b class="rnow ${p.price >= p.entry ? '' : 'down'}" style="left:${xn.toFixed(1)}%"></b></div>
    <div class="rlabs"><span class="loss">Stop ${price(p.stop)}</span><span>Bought ${price(p.entry)}</span><span class="gain">Target ${price(p.target)}</span></div>
    <div class="src" style="margin-top:4px">Now ${price(p.price)} · ${where}</div></div>`;
}

function lessons(st) {
  const a = st.all;
  if (!a || a.trades < 5) return [`${a ? a.trades : 0} finished trade${a && a.trades === 1 ? '' : 's'} so far. Patterns show up after about 5; after about 15 the weekly report starts tuning the bot.`];
  const out = [];
  const list = ['orb', 'vwap', 'momentum', 'crypto'].map((k) => ({ k, s: st[k] })).filter((x) => x.s && x.s.trades >= 2);
  if (list.length) {
    list.sort((x, y) => y.s.total - x.s.total);
    const b = list[0], w = list[list.length - 1];
    out.push(`Best setup so far: <strong>${STRAT_NAME[b.k]}</strong> (${signed(b.s.total)}, ${Math.round(b.s.winRate)}% wins over ${b.s.trades} trades).`);
    if (w.k !== b.k && w.s.total < 0) out.push(`Weakest: <strong>${STRAT_NAME[w.k]}</strong> (${signed(w.s.total)}, ${Math.round(w.s.winRate)}% wins).`);
  }
  if (a.avgWin > 0 && a.avgLoss < 0) {
    const loss = Math.abs(a.avgLoss), need = loss / (a.avgWin + loss) * 100;
    out.push(`Average win ${money(a.avgWin)} vs. average loss ${money(loss)}. With those sizes the bot needs <strong>${Math.round(need)}% wins</strong> to break even. It’s at <strong class="${a.winRate >= need ? 'gain' : 'loss'}">${Math.round(a.winRate)}%</strong>.`);
  }
  return out;
}

function botTradingSection() {
  const t = trd, on = isOn(D.settings.enabled), acts = activeStrats(), L = t.limits;
  let h = `<button class="switch ${on ? 'on' : ''}" data-do="switch" aria-pressed="${on}" ${busy ? 'disabled' : ''}>
    <span class="track"><span class="knob"></span></span><span><strong>Bot trading is ${on ? 'on' : 'off'}</strong>
    <span class="muted small">${on ? 'Tap to stop. The bot closes its own trades (stocks and crypto). Stocks you bought yourself stay.' : 'Tap to let the bot trade again.'}</span></span></button>`;
  const mkt = t.marketOpen ? 'Stock market open · closes ' + clockTime(t.nextClose) : 'Stock market closed · opens ' + whenShort(t.nextOpen);
  h += `<div class="chips"><span class="chip2 ${t.style === 'aggressive' ? 'y' : 'n'}">${t.style === 'aggressive' ? 'Aggressive' : 'Normal'} style</span>
    <span class="chip2 ${t.marketOpen ? 'g' : 'n'}">${esc(mkt)}</span>
    <span class="chip2 ${t.cryptoOn && on ? 'g' : 'n'}">Crypto bot ${t.cryptoOn && on ? 'on 24/7' : 'off'}</span>
    ${t.goldOn ? '<span class="chip2 n">Gold included</span>' : ''}</div>`;

  // Today at a glance
  const used = t.today.pnl < 0 && L.maxLoss ? Math.min(100, -t.today.pnl / L.maxLoss * 100) : 0;
  const stockOpen = t.open.filter((p) => p.strategy !== 'crypto').length, coinOpen = t.open.length - stockOpen;
  h += `<h2>Today</h2><div class="sum" style="margin-top:6px">
    <div class="card2"><span class="muted small">Bot profit/loss</span><div class="big ${t.today.pnl >= 0 ? 'gain' : 'loss'}">${signed(t.today.pnl)}</div>
      <div class="src">${signed(t.today.realized)} closed · ${signed(t.today.unrealized)} still open</div></div>
    <div class="card2"><span class="muted small">Wins / losses</span><div class="big"><span class="gain">${t.today.wins}</span> / <span class="loss">${t.today.losses}</span></div>
      <div class="src">finished trades today</div></div>
    <div class="card2"><span class="muted small">Stock trades used</span><div class="big">${t.today.entries} / ${L.maxTrades}</div>
      <div class="track"><i style="width:${Math.min(100, L.maxTrades ? t.today.entries / L.maxTrades * 100 : 0)}%"></i></div></div>
    <div class="card2"><span class="muted small">Loss limit used</span><div class="big">${Math.round(used)}%</div>
      <div class="track"><i class="r" style="width:${used}%"></i></div><div class="src">limit ${money(L.maxLoss)} · open ${stockOpen}/${L.maxOpen} stocks, ${coinOpen}/${L.cryptoMaxOpen} coins</div></div></div>`;
  h += `<button class="outline" style="margin-top:12px" data-do="trdrefresh">${t.refreshing ? 'Refreshing…' : 'Refresh'}</button>`;

  h += `<button class="primary" style="margin-top:12px" data-do="gotab" data-tab="live">Watch it live ›</button>`;

  // Scoreboard
  h += '<h2>Scoreboard · last 30 days</h2>';
  h += lessons(t.stats).map((x) => `<div class="note">${x}</div>`).join('');
  h += '<div style="margin-top:6px">';
  ['orb', 'vwap', 'momentum', 'crypto'].forEach((k) => {
    const s = t.stats[k] || { trades: 0 };
    h += `<div class="wr"><strong>${STRAT_NAME[k]}</strong>
      <div><div class="track"><i class="${s.winRate >= 50 ? 'g' : 'r'}" style="width:${s.trades ? s.winRate : 0}%"></i></div>
        <div class="src">${s.trades ? `${Math.round(s.winRate)}% wins · ${s.trades} trade${s.trades === 1 ? '' : 's'} · avg win ${money(s.avgWin)} / loss ${money(Math.abs(s.avgLoss))}` : 'No finished trades yet'}</div></div>
      <div class="right ${s.total >= 0 ? 'gain' : 'loss'}"><strong>${s.trades ? signed(s.total) : '—'}</strong></div></div>`;
  });
  const A = t.stats.all;
  h += `<div class="wr" style="border-bottom:0"><strong>All</strong><div class="src">${A.trades} trades · ${Math.round(A.winRate)}% wins · best ${signed(A.best)} · worst ${signed(A.worst)}</div>
    <div class="right ${A.total >= 0 ? 'gain' : 'loss'}"><strong>${signed(A.total)}</strong></div></div></div>`;

  // Finished trades
  h += '<h2>Finished trades</h2>';
  if (!t.closed.length) h += '<p class="empty">Finished trades show up here with their entry, exit and result.</p>';
  t.closed.forEach((c) => {
    h += `<div class="row"><div class="grow"><strong>${esc(c.symbol)}</strong> ${stratChip(c.strategy)}
        <div class="src">${price(c.entry)} → ${price(c.exit)} · held ${heldFor(c.opened, c.closed)} · ${esc(c.date.slice(5))}</div><div class="src">${esc(c.why)}</div></div>
      <div class="right"><strong class="${c.pnl >= 0 ? 'gain' : 'loss'}">${signed(c.pnl)}</strong><div class="src">${pct(c.ret)}</div></div></div>`;
  });

  // Controls
  h += '<h2>Setups the bot uses</h2>';
  STRATS.forEach((s) => {
    const o = acts.indexOf(s.id) >= 0;
    h += `<div class="row"><div class="grow"><strong>${s.name}</strong><div class="muted small">${s.text}</div></div>
      <button class="toggle ${o ? 'on' : ''}" data-do="strat" data-id="${s.id}" aria-label="${s.name}" aria-pressed="${o}" ${busy ? 'disabled' : ''}></button></div>`;
  });
  h += `<div class="row"><div class="grow"><strong>Crypto (24/7)</strong><div class="muted small">Breakouts in an uptrend on 15-minute charts, checked every 10 minutes. Coins and $ per trade are in Settings › Crypto &amp; gold.</div></div>
    <button class="toggle ${t.cryptoOn ? 'on' : ''}" data-do="cryptotoggle" aria-label="Crypto bot" aria-pressed="${t.cryptoOn}" ${busy || t.mode === 'LIVE' ? 'disabled' : ''}></button></div>`;
  h += '<button class="outline" style="margin-top:14px" data-do="report">Report card and you vs. the S&amp;P 500</button>';

  h += '<details class="brief"><summary>Last 7 days, journal and bot log</summary><h2>Last 7 days</h2>';
  if (!D.daily.length) h += '<p class="empty">Daily results appear after the first full trading day.</p>';
  D.daily.forEach((d) => {
    const pl = Number(String(d['Day P&L']).replace(/[^0-9.-]/g, '')) || 0;
    h += `<div class="row"><div class="grow">${esc(d['Date'])} <span class="muted small">${esc(d['Mode'])}</span></div><div class="${pl >= 0 ? 'gain' : 'loss'}">${signed(pl)}</div></div>`;
  });
  h += '<h2>Journal</h2>';
  if (!D.trades.length) h += '<p class="empty">No trades yet.</p>';
  D.trades.forEach((r) => {
    h += `<div class="row"><div class="grow"><strong>${esc(r['Symbol'])}</strong> <span class="muted small">${esc(r['Strategy'])}</span>
      <div class="muted small">${esc(r['Qty'])}${r['Entry'] ? ' @ ' + esc(r['Entry']) : ''}${r['Stop'] ? ' · stop ' + esc(r['Stop']) + ' · target ' + esc(r['Target']) : ''}</div>
      <div class="muted small">${esc(r['Reason'])}</div>
      ${r['Note'] ? `<div class="small" style="margin-top:4px">📝 ${esc(r['Note'])}</div>` : ''}
      <button class="del" style="padding-left:0" data-do="note" data-row="${r._row}" data-sym="${esc(r['Symbol'])}" data-note="${esc(r['Note'] || '')}">${r['Note'] ? 'Edit note' : 'Add note'}</button></div>
      <div class="right muted small">${esc(String(r['Time']).slice(5, 16))}</div></div>`;
  });
  h += '<h2>Bot log</h2>';
  if (!D.log.length) h += '<p class="empty">Nothing logged yet.</p>';
  D.log.forEach((l) => {
    h += `<div class="row"><div class="grow"><strong class="small">${esc(l['Event'])}</strong><div class="muted small">${esc(l['Message'])}</div></div><div class="right muted small">${esc(String(l['Time']).slice(5, 16))}</div></div>`;
  });
  h += '</details>';
  h += `<button class="danger" data-do="closeall" ${busy ? 'disabled' : ''}>Close every position now</button>
    <p class="muted small" style="margin-top:8px">Sells everything in the account, including stocks you bought yourself, cancels open orders and turns bot trading off.</p>`;
  return h;
}

function myTradingSection() {
  const t = trd, M = t.me;
  let h = `<form class="search" id="tradeSearch"><svg viewBox="0 0 24 24" fill="none" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
    <input name="q" placeholder="Buy or sell: ticker or company" autocomplete="off" autocapitalize="characters" enterkeyhint="go"></form>`;
  const invested = M.positions.reduce((a, p) => a + p.value, 0), pl = M.positions.reduce((a, p) => a + p.pl, 0);
  h += `<div class="sum">
    <div class="card2"><span class="muted small">Your stocks</span><div class="big">${money(invested)}</div><div class="small ${pl >= 0 ? 'gain' : 'loss'}">${signed(pl)} total</div></div>
    <div class="card2"><span class="muted small">Buying power</span><div class="big">${money(t.buyingPower)}</div><div class="src">${t.marketOpen ? 'Market open' : 'Market closed · orders wait for the open'}</div></div></div>`;
  const wl = (D.watchlist || []).slice(0, 12);
  if (wl.length) h += '<div class="strip">' + wl.map((w) => `<button class="tickbtn" data-open="${esc(w.symbol || w.Symbol || w)}">${esc(w.symbol || w.Symbol || w)}</button>`).join('') + '</div>';

  h += `<h2>Your stocks (${M.positions.length})</h2>`;
  if (!M.positions.length) h += '<p class="empty">Nothing yet. Search above to buy your first stock.</p>';
  M.positions.sort((x, y) => y.value - x.value).forEach((p) => {
    h += `<div class="pcard"><div class="row" style="padding:0;border:0" data-open="${esc(p.symbol)}"><div class="grow" style="cursor:pointer"><strong>${esc(p.symbol)}</strong> <span class="src">${esc(p.source)}</span>
        <div class="src">${+p.qty.toFixed(6)} sh · avg ${price(p.entry)} · now ${price(p.price)} · <span class="${p.todayPct >= 0 ? 'gain' : 'loss'}">${pct(p.todayPct)} today</span></div></div>
      <div class="right"><strong>${money(p.value)}</strong><div class="src ${p.pl >= 0 ? 'gain' : 'loss'}">${signed(p.pl)} (${pct(p.plpc)})</div></div></div>
      <div class="pair" style="margin-top:10px"><button class="outline" data-do="quick" data-side="buy" data-sym="${esc(p.symbol)}">Buy more</button><button class="outline" data-do="quick" data-side="sell" data-sym="${esc(p.symbol)}">Sell</button></div></div>`;
  });

  h += `<h2>Your waiting orders (${M.open.length})</h2>`;
  if (!M.open.length) h += '<p class="empty">No orders waiting.</p>';
  M.open.forEach((o) => {
    h += `<div class="row"><div class="grow"><strong>${esc(o.symbol)}</strong> <span class="stat pending">Waiting</span>
      <div class="small">${esc(orderWhat(o))}</div><div class="src">${esc(o.source)} · ${esc(whenShort(o.time))} · ${o.tif === 'gtc' ? 'good until canceled' : 'today only'}</div></div>
      <button class="del" data-do="cancelorder3" data-id="${esc(o.id)}">Cancel</button></div>`;
  });

  h += '<h2>Your recent orders</h2>';
  if (!M.activity.length) h += '<p class="empty">Orders you place from this app show up here.</p>';
  M.activity.forEach((o) => {
    const st = statusLabel(o.status);
    h += `<div class="row"><div class="grow"><strong>${esc(o.symbol)}</strong> <span class="stat ${st[0]}">${st[1]}</span>
      <div class="small">${esc(orderWhat(o))}${o.price ? ' · filled at ' + price(o.price) : ''}</div><div class="src">${esc(o.source)}</div></div>
      <div class="right src">${esc(whenShort(o.time))}</div></div>`;
  });
  h += '<p class="muted small" style="margin-top:14px">The bot never sells these. Its own trades are under Bot trading.</p>';
  return h;
}


// ---------- Models (inside Trading) ----------
let mdl = null;
function loadModels(quiet) {
  if (!quiet) { mdl = mdl && !mdl.error ? Object.assign(mdl, { refreshing: true }) : { loading: true }; render(); }
  call('getModels', KEY).then((m) => { mdl = m; if (tab === 'trading' && tradeSeg === 'models' && !stock) render(); })
    .catch((e) => { mdl = { error: e.message || String(e) }; render(); });
}
function riskDots(n) {
  return `<span class="risk" aria-label="Risk ${n} of 3">${[1, 2, 3].map((i) => `<i class="${i <= n ? 'on r' + n : ''}"></i>`).join('')}</span><span class="src">${['', 'Low', 'Medium', 'High'][n]} activity</span>`;
}
function modelsSection() {
  if (!mdl || mdl.loading) return '<p class="muted" style="margin-top:16px">Loading models…</p>';
  if (mdl.error) return `<div class="notice bad" style="margin-top:12px">${esc(mdl.error)}</div>`;
  const M = mdl, live = M.mode === 'LIVE', act = M.models.find((m) => m.id === M.active) || M.models[0];
  let h = `<div class="pcard" style="border:2px solid var(--gold)"><span class="muted small">Active model</span>
    <div class="big" style="font-size:1.4rem;font-weight:800">${esc(act.name)}</div>
    <div class="src">${M.since ? 'Since ' + esc(M.since.slice(0, 16)) : 'Current settings'}${act.diff.length ? ` · tuned: ${act.diff.length} setting${act.diff.length === 1 ? '' : 's'} changed` : ''}</div>
    ${act.diff.length ? `<div class="src" style="margin-top:6px">${act.diff.slice(0, 4).map((d) => `${esc(d.label)}: ${esc(d.model)} → <strong>${esc(d.now)}</strong>`).join('<br>')}${act.diff.length > 4 ? '<br>…' : ''}</div>` : ''}</div>`;

  // Results by model
  const withData = M.models.filter((m) => M.results[m.id] && M.results[m.id].trades);
  h += '<h2>Results by model · last 90 days</h2>';
  if (!withData.length) h += '<p class="empty">No finished trades labeled yet. From now on every trade is labeled with the model that made it, so you can compare them here.</p>';
  else {
    const maxAbs = Math.max(...withData.map((m) => Math.abs(M.results[m.id].total)), 1);
    withData.sort((a, b) => M.results[b.id].total - M.results[a.id].total).forEach((m) => {
      const r = M.results[m.id], w = Math.abs(r.total) / maxAbs * 50;
      h += `<div class="wr"><strong>${esc(m.name)}</strong>
        <div><div class="pnlbar"><i class="${r.total >= 0 ? 'g' : 'r'}" style="${r.total >= 0 ? 'left:50%' : 'right:50%'};width:${w.toFixed(1)}%"></i><b></b></div>
          <div class="src">${r.trades} trades · ${Math.round(r.winRate)}% wins</div></div>
        <div class="right ${r.total >= 0 ? 'gain' : 'loss'}"><strong>${signed(r.total)}</strong></div></div>`;
    });
  }
  if (M.results.before && M.results.before.trades) h += `<p class="src" style="margin-top:6px">Before models: ${M.results.before.trades} trades, ${signed(M.results.before.total)}.</p>`;

  // Model cards
  h += '<h2>Pick a model</h2>';
  M.models.forEach((m) => {
    const on = m.id === M.active, r = M.results[m.id], be = Math.round(100 / (1 + m.rr));
    const blocked = live && m.paperOnly;
    h += `<div class="pcard" ${on ? 'style="border:2px solid var(--gold)"' : ''}>
      <div class="row" style="padding:0;border:0"><div class="grow"><strong style="font-size:1.05rem">${esc(m.name)}</strong> ${on ? '<span class="chip2 y">Active</span>' : ''}${m.paperOnly ? ' <span class="chip2 n">Paper only</span>' : ''}</div>${riskDots(m.risk)}</div>
      <div class="small" style="margin-top:6px">${esc(m.idea)}</div>
      <div class="src" style="margin-top:4px">Good for: ${esc(m.good)}</div>
      <div class="mgrid">
        <div><b>${m.trades}</b><span>trades/day</span></div><div><b>${m.id === 'crypto' ? m.coins : m.open}</b><span>${m.id === 'crypto' ? 'coins at once' : 'at once'}</span></div>
        <div><b>${m.rr}x</b><span>target</span></div><div><b>${m.stop}%</b><span>widest stop</span></div>
        <div><b>${esc(m.hours)}</b><span>${m.id === 'crypto' ? 'hours' : 'last new trade'}</span></div><div><b>${be}%</b><span>wins to break even</span></div></div>
      <div class="src" style="margin-top:8px">${r && r.trades ? `Your results: ${r.trades} trades · ${Math.round(r.winRate)}% wins · <strong class="${r.total >= 0 ? 'gain' : 'loss'}">${signed(r.total)}</strong>` : 'Not tried yet'}</div>
      ${on && !m.diff.length ? '' : `<button class="${on ? 'outline' : 'primary'}" style="margin-top:10px" data-do="usemodel" data-id="${m.id}" data-name="${esc(m.name)}" ${busy || blocked ? 'disabled' : ''}>${blocked ? 'Paper money only' : on ? 'Reset to ' + esc(m.name) + ' settings' : 'Switch to ' + esc(m.name)}</button>`}
    </div>`;
  });
  h += `<p class="muted small" style="margin-top:14px">Switching changes the bot’s rules starting with its next check. Trades already open keep their stop and target. Your $ per trade (${money(M.perTrade)}) and daily loss limit (${money(M.lossLimit)}) stay yours; a model only raises a limit that’s too small for it. The weekly self-improvement still fine-tunes whichever model is active.</p>`;
  return h;
}

// ---------- Live (watch the bots work) ----------
let live = null;
function loadLive(quiet) {
  if (!quiet) { live = live && !live.error ? Object.assign(live, { refreshing: true }) : { loading: true }; render(); }
  call('getLive', KEY).then((d) => { d.fetched = Date.now(); live = d; if (tab === 'live' && !stock) render(); })
    .catch((e) => { if (!quiet || !live || live.loading) { live = { error: e.message || String(e) }; render(); } });
}
function secsAgo(ms) {
  const s = Math.max(0, Math.round((Date.now() - ms) / 1000));
  if (s < 60) return s + 's'; const m = Math.round(s / 60); if (m < 60) return m + ' min'; return Math.floor(m / 60) + 'h ' + (m % 60) + 'm';
}
function untilText(iso) {
  const m = Math.max(0, Math.round((new Date(iso) - Date.now()) / 60000));
  return m < 60 ? m + 'm' : Math.floor(m / 60) + 'h ' + (m % 60) + 'm';
}
function stage(n, title, count, body) {
  return `<div class="stage"><div class="stg-h"><span><span class="stg-i">${n}</span><strong>${title}</strong></span><span class="stg-n">${count}</span></div>${body}</div>`;
}
const FLOW = '<div class="flow" aria-hidden="true">↓</div>';
function liveView() {
  let h = header();
  if (!live || live.loading) return h + '<p class="muted" style="margin-top:16px">Connecting to the bots…</p>';
  if (live.error) return h + `<div class="notice bad" style="margin-top:12px">${esc(live.error)}</div><button class="outline" style="margin-top:12px" data-do="liverefresh">Try again</button>`;
  const L = live, T = L.today, lim = L.limits, S = L.stock || {}, C = L.crypto || {};
  const stockLate = L.marketOpen && L.enabled && (!L.lastStockRun || Date.now() - L.lastStockRun > 20 * 60000);
  const stockRun = L.lastStockRun ? 'stocks ' + secsAgo(L.lastStockRun) + ' ago' : 'stocks not yet';
  const cryptoRun = L.lastCryptoRun ? 'crypto ' + secsAgo(L.lastCryptoRun) + ' ago' : 'crypto not yet';
  h += `<div class="hb"><span class="pulse ${L.enabled ? '' : 'off'}"></span><span id="liveAgo">Updated just now</span> · bots ran: ${esc(stockRun)}, ${esc(cryptoRun)}</div>`;
  if (!L.enabled) h += '<div class="notice bad" style="margin-top:8px">Bot trading is off. Turn it on in Trading › Bot trading.</div>';
  if (stockLate) h += '<div class="notice" style="margin-top:8px">The stock bot hasn’t run in over 20 minutes. GitHub’s timer is sometimes late during busy hours; if this lasts an hour, check GitHub › Actions.</div>';

  // Live strip
  const used = T.pnl < 0 && lim.maxLoss ? Math.min(100, -T.pnl / lim.maxLoss * 100) : 0;
  const stockOpen = L.open.filter((p) => p.strategy !== 'crypto').length, coins = L.open.length - stockOpen;
  const mkt = L.marketOpen ? 'Closes in ' + untilText(L.nextClose) : 'Opens ' + whenShort(L.nextOpen);
  h += `<div class="lstrip">
    <div class="card2"><span class="muted small">Bot today</span><div class="big ${T.pnl >= 0 ? 'gain' : 'loss'}">${signed(T.pnl)}</div></div>
    <div class="card2"><span class="muted small">Open</span><div class="big">${stockOpen}/${lim.maxOpen}${coins ? ` <span class="src">+${coins} coin${coins > 1 ? 's' : ''}</span>` : ''}</div></div>
    <div class="card2"><span class="muted small">Trades used</span><div class="big">${T.entries}/${lim.maxTrades}</div></div>
    <div class="card2"><span class="muted small">Won / lost</span><div class="big"><span class="gain">${T.wins}</span>/<span class="loss">${T.losses}</span></div></div>
    <div class="card2"><span class="muted small">Loss limit</span><div class="big">${Math.round(used)}%</div><div class="track"><i class="r" style="width:${used}%"></i></div></div>
    <div class="card2"><span class="muted small">Market</span><div class="big" style="font-size:1rem">${esc(mkt)}</div></div></div>
    <div class="src" style="margin-top:6px">${esc(L.model)} model · ${L.style === 'aggressive' ? 'Aggressive' : 'Normal'} style${L.goldOn ? ' · gold on' : ''}${L.cryptoOn ? ' · crypto 24/7' : ''}</div>`;

  // Pipeline
  h += '<h2>Pipeline</h2>';
  const statusLine = (name, x, last) => x && x.status ? `<div class="src">${name}: ${esc(x.status)}${last ? ' · ' + secsAgo(last) + ' ago' : ''}</div>` : '';
  h += stage(1, 'Scanning', (S.scanned || 0) + (C.scanned || 0),
    `<div class="src">${S.scanned || 0} stocks${S.gainers ? ' (incl. ' + S.gainers + ' top gainers)' : ''} · ${C.scanned || 0} coins</div>` +
    statusLine('Stocks', S, L.lastStockRun) + statusLine('Crypto', C, L.lastCryptoRun) +
    (C.weather ? `<div class="chips"><span class="chip2 ${C.weather.state === 'up' ? 'g' : C.weather.state === 'down' ? 'r' : 'y'}">Crypto weather: ${esc(C.weather.label)}</span>${C.weather.fng ? `<span class="chip2 n">Fear &amp; Greed ${C.weather.fng.value} · ${esc(C.weather.fng.label)}</span>` : ''}</div><div class="src" style="margin-top:4px">${esc(C.weather.text)}</div>` : ''));
  h += FLOW;
  const near = (S.near || []).concat(C.near || []).sort((a, b) => a.pct - b.pct).slice(0, 8);
  h += stage(2, 'Almost a signal', near.length, near.length ? near.map((x) => `<div class="nrow" ${x.strategy === 'crypto' ? '' : `data-open="${esc(x.symbol)}"`}>
      <div class="grow"><strong>${esc(x.symbol)}</strong> ${stratChip(x.strategy)}<div class="src">${esc(x.text)}</div></div>
      <div class="close"><div class="track"><i class="y" style="width:${Math.max(8, Math.round((1 - x.pct / 0.01) * 100))}%"></i></div><span class="src">${(x.pct * 100).toFixed(1)}% away</span></div></div>`).join('')
    : '<div class="src">Nothing close to a setup on the last check.</div>');
  h += FLOW;
  h += stage(3, 'Order placed', L.waiting.length, L.waiting.length ? L.waiting.map((o) => `<div class="src" style="margin-top:4px"><strong style="color:var(--ink)">${esc(o.symbol)}</strong> ${stratChip(o.strategy)} · ${o.qty ? esc(o.qty) + ' sh' : money(o.notional)}${o.limit ? ' up to ' + price(o.limit) : ''} · waiting ${secsAgo(new Date(o.time).getTime())}</div>`).join('')
    : '<div class="src">No orders waiting to fill.</div>');
  h += FLOW;
  h += stage(4, 'In trade', L.open.length, L.open.length ? L.open.map((p) => `<div class="ltrade"><div class="row" style="padding:0;border:0"><div class="grow"><strong ${p.strategy === 'crypto' ? '' : `data-open="${esc(p.symbol)}" style="cursor:pointer"`}>${esc(p.symbol)}</strong> ${stratChip(p.strategy)}
        <div class="src">${money(p.value)} · held ${heldFor(p.opened)}</div></div><div class="right"><strong class="${p.pl >= 0 ? 'gain' : 'loss'}">${signed(p.pl)}</strong><div class="src">${pct(p.plpc)}</div></div></div>${rangeBar(p)}</div>`).join('')
    : '<div class="src">Not holding anything right now.</div>');
  h += FLOW;
  h += stage(5, 'Closed today', T.wins + T.losses, `<div class="src"><span class="gain">${T.wins} win${T.wins === 1 ? '' : 's'} ${signed(T.winSum || 0)}</span> · <span class="loss">${T.losses} loss${T.losses === 1 ? '' : 'es'} ${signed(T.lossSum || 0)}</span></div>
    <button class="del" style="padding-left:0" data-do="gotab" data-tab="trading">Scoreboard and finished trades ›</button>`);

  // Feed
  h += '<h2>Live feed</h2>';
  if (!L.feed.length) h += '<p class="empty">Nothing yet today. Every buy, sell, skipped signal and status change shows up here.</p>';
  const ICON = { buy: ['buy', 'B'], win: ['win', 'S'], loss: ['lose', 'S'], skip: ['skip', '–'], order: ['order', 'O'], status: ['status', '•'] };
  L.feed.forEach((f) => {
    const ic = ICON[f.kind] || ICON.status;
    h += `<div class="tl"><span class="t">${esc(clockTime(f.t))}</span><span class="ic ${ic[0]}">${ic[1]}</span>
      <div class="grow small ${f.kind === 'skip' || f.kind === 'status' ? 'muted' : ''}">${esc(f.text)}</div>
      ${f.pnl != null ? `<strong class="${f.pnl >= 0 ? 'gain' : 'loss'}">${signed(f.pnl)}</strong>` : ''}</div>`;
  });
  h += `<p class="src" style="margin-top:12px">Prices refresh every 20 seconds while this screen is open. The stock bot decides every 5 minutes, the crypto bot every 10.</p>`;
  return h;
}
setInterval(() => { if (tab === 'live' && !stock && !busy && !document.hidden && live && !live.loading) loadLive(true); }, 20000);
setInterval(() => { const el = $('liveAgo'); if (el && live && live.fetched) el.textContent = 'Updated ' + secsAgo(live.fetched) + ' ago'; }, 1000);

function tradingView() {
  let h = header() + `<div class="seg" style="margin-top:18px"><button data-do="tseg" data-s="bot" class="${tradeSeg === 'bot' ? 'on' : ''}">Bot trading</button>
    <button data-do="tseg" data-s="me" class="${tradeSeg === 'me' ? 'on' : ''}">My trading</button>
    <button data-do="tseg" data-s="models" class="${tradeSeg === 'models' ? 'on' : ''}">Models</button></div>`;
  if (tradeSeg === 'models') return h + modelsSection();
  if (!trd || trd.loading) return h + '<p class="muted" style="margin-top:16px">Loading trades…</p>';
  if (trd.error) return h + `<div class="notice bad" style="margin-top:12px">${esc(trd.error)}</div><button class="outline" style="margin-top:12px" data-do="trdrefresh">Try again</button>`;
  return h + (tradeSeg === 'bot' ? botTradingSection() : myTradingSection());
}

// ---------- Intel ----------
function intelTag(r) {
  if (r['Status'] === 'Analyzing') return '<span class="tag">Analyzing</span>';
  if (r['Status'] === 'Error') return '<span class="tag hold">Error</span>';
  if (r['Category'] === 'Not yet public') return '<span class="tag hold">On hold</span>';
  if (r['Category'] === 'Public') return '<span class="tag public">Public</span>';
  return '<span class="tag theme">Theme</span>';
}
function intelView() {
  if (!lastEvent && D.intel.length) lastEvent = D.intel[0]['Event'] || '';
  let h = header() + '<h2>What did you see or hear?</h2>';
  if (!D.intelReady) h += '<div class="notice bad" style="margin-bottom:12px">Add ANTHROPIC_API_KEY in Script properties to turn on research.</div>';
  h += `<form class="card" id="intelForm">
      <label>Event<input name="event" value="${esc(lastEvent)}" placeholder="e.g. Japanese Chamber of Commerce dinner"></label>
      <label>Notes<textarea name="note" placeholder="Companies at the tables, speech topics, trends people kept mentioning…" required></textarea></label>
      <button class="primary" ${busy ? 'disabled' : ''}>${busy ? 'Researching… (up to a minute)' : 'Save and research'}</button></form>
    <p class="muted small" style="margin-top:8px">Themes and public facts get researched with ideas. Specific company info that isn’t public yet goes on hold with no trade ideas, and is rechecked every morning.</p>
    <h2>Your notes</h2>`;
  if (!D.intel.length) h += '<p class="empty">No notes yet. Your first one shows up here with its research.</p>';
  D.intel.forEach((r) => {
    const sources = String(r['Sources'] || '').split('\n').filter(Boolean).map((u) => `<a href="${esc(/^https?:\/\//.test(u) ? u : '#')}" target="_blank" rel="noopener">${esc(u.replace(/^https?:\/\/(www\.)?/, '').slice(0, 60))}</a>`).join('<br>');
    h += `<details class="intel"><summary><div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">${intelTag(r)}<strong>${esc(r['Tickers'] || r['Event'] || 'Note')}</strong><span class="muted small">${esc(String(r['Time']).slice(5, 16))}</span></div>
      <div class="muted small" style="margin-top:6px">${esc(r['Summary'] || String(r['Note']).slice(0, 140))}</div></summary>
      <div class="body"><div><strong>Your note</strong><br>${esc(r['Note'])}${r['Event'] ? '<br><span class="muted small">' + esc(r['Event']) + '</span>' : ''}</div>
      ${r['Tickers'] && r['Category'] !== 'Not yet public' ? '<div class="tick">' + String(r['Tickers']).split(/[,\s]+/).filter(Boolean).map((t) => `<button class="tickbtn" data-do="watchadd" data-sym="${esc(t)}">☆ ${esc(t)}</button><button class="tickbtn" data-do="alertfor" data-sym="${esc(t)}">🔔 ${esc(t)}</button><button class="tickbtn" data-do="addcompare" data-sym="${esc(t)}" data-found="${esc(r['Event'] || '')}">📊 ${esc(t)}</button>`).join('') + '</div>' : ''}
      <div><button class="tickbtn" data-do="ipoaddprompt" data-found="${esc(r['Event'] || '')}">🚀 Watch a private company from this note</button></div>
      ${r['Research'] ? '<div><strong>Research</strong><br>' + esc(r['Research']) + '</div>' : ''}
      ${r['Ideas'] ? '<div><strong>Ideas to watch</strong><br>' + esc(r['Ideas']) + '</div>' : ''}
      ${sources ? '<div><strong>Sources</strong><br>' + sources + '</div>' : ''}
      <div class="muted small">Checked ${esc(r['Last Checked'] || 'not yet')}</div>
      <button class="outline" data-do="recheck" data-row="${r._row}" data-time="${esc(r['Time'])}" ${busy ? 'disabled' : ''}>Recheck now</button></div></details>`;
  });
  return h;
}

// ---------- Alerts & Auto ----------
function rowList(items, tabName, describe) {
  if (!items.length) return '<p class="empty">Nothing here yet. Add one above.</p>';
  return items.map((r) => {
    const on = isOn(r['Active']);
    return `<div class="row"><button class="toggle ${on ? 'on' : ''}" data-do="toggle" data-tab="${tabName}" data-row="${r._row}" data-sym="${esc(r['Symbol'])}" aria-label="Turn ${esc(r['Symbol'])} ${on ? 'off' : 'on'}" aria-pressed="${on}" ${busy ? 'disabled' : ''}></button>
      <div class="grow"><strong>${esc(r['Symbol'])}</strong><div class="muted small">${describe(r)}</div></div>
      <button class="del" data-do="delete" data-tab="${tabName}" data-row="${r._row}" data-sym="${esc(r['Symbol'])}" ${busy ? 'disabled' : ''}>Remove</button></div>`;
  }).join('');
}
let alertPrefill = '';
function alertsView() {
  const pre = alertPrefill; alertPrefill = '';
  return header() + `<h2>New alert</h2><form class="card" id="alertForm">
      <div class="pair"><label>Symbol<input name="symbol" value="${esc(pre)}" placeholder="AAPL, GLD, BTC-USD" autocapitalize="characters" required></label>
      <label>Type<select name="asset"><option>Stock/ETF</option><option>Crypto</option></select></label></div>
      <div class="pair"><label>When<select name="condition"><option>Price above</option><option>Price below</option><option>Up % today</option><option>Down % today</option></select></label>
      <label>Value<input name="value" type="number" step="any" inputmode="decimal" placeholder="e.g. 250 or 5" required></label></div>
      <label>Note (optional)<input name="note" placeholder="Why this matters"></label>
      <button class="primary" ${busy ? 'disabled' : ''}>Add alert</button></form>
    <p class="notice" style="margin-top:12px">Alerts are checked every 5 minutes and each one sends at most once a day, by email and phone push. Set where they go in Settings.</p>
    <h2>Your alerts</h2>` + rowList(D.alerts, 'Alerts', (r) => esc(r['Condition']) + ' ' + esc(r['Value']) + (r['Note'] ? ' · ' + esc(r['Note']) : '') + (r['Last Triggered'] ? '<br>Last sent ' + esc(r['Last Triggered']) : ''));
}
function autoView() {
  return header() + `<h2>New recurring buy</h2><form class="card" id="autoForm">
      <div class="pair"><label>Symbol<input name="symbol" placeholder="GLD, VOO, BTC-USD" autocapitalize="characters" required></label>
      <label>Type<select name="asset"><option>Stock/ETF</option><option>Crypto</option></select></label></div>
      <div class="pair"><label>Amount ($)<input name="amount" type="number" min="1" step="any" inputmode="decimal" placeholder="25" required></label>
      <label>How often<select name="frequency" id="freq"><option>Weekly</option><option>Monthly</option><option>Daily</option></select></label></div>
      <label id="dayWrap">Day<select name="day" id="daySel"></select></label>
      <button class="primary" ${busy ? 'disabled' : ''}>Add recurring buy</button></form>
    <p class="notice" style="margin-top:12px">Recurring buys run around 10 AM ET on their day (or the next market day). They count against your per-order limit in Settings. Crypto plans start once Coinbase is connected.</p>
    <h2>Your plans</h2>` + rowList(D.auto, 'AutoInvest', (r) => {
      const w = r['Frequency'] === 'Weekly' ? 'every ' + r['Day'] : r['Frequency'] === 'Monthly' ? 'monthly on day ' + r['Day'] : 'daily';
      return '$' + esc(r['Amount $']) + ' ' + esc(w) + (r['Last Run'] ? '<br>Last bought ' + esc(r['Last Run']) : '');
    });
}
function fillDays() {
  const f = $('freq'), sel = $('daySel'), wrap = $('dayWrap'); if (!f) return;
  const opts = f.value === 'Weekly' ? ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] : f.value === 'Monthly' ? Array.from({ length: 28 }, (_, i) => String(i + 1)) : [];
  wrap.style.display = opts.length ? '' : 'none';
  sel.innerHTML = opts.map((o) => '<option>' + o + '</option>').join('');
}



// ---------- Crypto (Coinbase) ----------
function num(v) { return Number(String(v == null ? '' : v).replace(/[^0-9.-]/g, '')) || 0; }
function cryptoTotals() {
  let total = 0, today = 0;
  (D.crypto || []).forEach((c) => { const v = num(c['Value $']), ch = num(c['Change 24h %']); total += v; today += ch ? v - v / (1 + ch / 100) : 0; });
  return { total, today };
}
function cryptoSection() {
  let h = '<h2>Crypto</h2>';
  if (!D.crypto || !D.crypto.length) return h + '<p class="empty">Coinbase isn’t connected yet. Your crypto shows here once it is.</p>';
  const t = cryptoTotals();
  h += `<div class="rowlink"><strong>Coinbase</strong><span><strong>${money(t.total)}</strong> <span class="small ${t.today >= 0 ? 'gain' : 'loss'}">${signed(t.today)} 24h</span></span></div>`;
  D.crypto.slice().sort((a, b) => num(b['Value $']) - num(a['Value $'])).forEach((c) => {
    const ch = num(c['Change 24h %']);
    const text = pillMode === 'price' ? (num(c['Price $']) ? price(num(c['Price $'])) : money(num(c['Value $']))) : pillMode === 'pct' ? pct(ch) : money(num(c['Value $']));
    h += `<div class="item" style="cursor:default;grid-template-columns:1fr 92px"><span><span class="sym">${esc(c['Symbol'])}</span><br><span class="sub">${esc(c['Qty'])} · ${money(num(c['Value $']))}</span></span>
      <span class="pill ${ch >= 0 ? '' : 'down'}" data-do="pill">${text}</span></div>`;
  });
  const upd = D.crypto[0] && D.crypto[0]['Updated'];
  if (upd) h += `<p class="muted small" style="margin-top:6px">Coinbase updated ${esc(String(upd).slice(5, 16))} · syncs every 30 minutes</p>`;
  return h;
}

// ---------- Other accounts ----------
function holdingValue(x) {
  const q = D.quotes[x.symbol];
  const px = q && q.price ? q.price : 0;
  return { q, px, value: x.shares * px, today: q && px ? x.shares * q.change : 0, gain: x.cost && px ? (px - x.cost) * x.shares : null };
}
function otherAccountsSection() {
  const list = D.other || [];
  let h = '<h2 style="display:flex;justify-content:space-between;align-items:baseline">Other accounts <button class="ghost" data-do="holdings">Manage</button></h2>';
  if (!list.length) return h + '<p class="empty">Track stocks you hold elsewhere, like Robinhood. They’re for watching only; the bot never trades them.</p><button class="outline" data-do="holdings">Add holdings</button>';
  const accounts = [...new Set(list.map((x) => x.account))];
  accounts.forEach((acc) => {
    const items = list.filter((x) => x.account === acc);
    let total = 0, today = 0;
    items.forEach((x) => { const v = holdingValue(x); total += v.value; today += v.today; });
    h += `<div class="rowlink"><strong>${esc(acc)}</strong><span><strong>${money(total)}</strong> <span class="small ${today >= 0 ? 'gain' : 'loss'}">${signed(today)} today</span></span></div>`;
    items.forEach((x) => {
      const v = holdingValue(x);
      h += `<button class="item" data-open="${esc(x.symbol)}"><span><span class="sym">${esc(x.symbol)}</span><br><span class="sub">${+x.shares.toFixed(6)} sh${v.px ? ' · ' + money(v.value) : ' · no price'}</span></span>
        ${sparkline(v.q && v.q.spark, v.q ? v.q.change >= 0 : true)}${pill(v.q)}</button>`;
    });
  });
  return h;
}
function holdingsView() {
  const list = D.other || [];
  let h = header() + `<h2 style="margin-top:22px">Other accounts</h2>
    <p class="muted small">Stocks you own outside GOLDMINEBOT. Prices update live; nothing here is ever bought or sold.</p>
    <form class="card" id="holdingForm" style="margin-top:14px">
      <div class="pair"><label>Account<input name="account" value="${esc((list[0] && list[0].account) || 'Robinhood')}" required></label>
      <label>Ticker<input name="symbol" placeholder="AAPL" autocapitalize="characters" required></label></div>
      <div class="pair"><label>Shares<input name="shares" type="number" step="any" inputmode="decimal" min="0" required></label>
      <label>Cost per share (optional)<input name="cost" type="number" step="any" inputmode="decimal" min="0" placeholder="$"></label></div>
      <button class="primary" ${busy ? 'disabled' : ''}>Add holding</button></form>
    <h2>Your holdings</h2>`;
  if (!list.length) h += '<p class="empty">Nothing added yet.</p>';
  list.forEach((x) => {
    const v = holdingValue(x);
    h += `<div class="row"><div class="grow"><strong>${esc(x.symbol)}</strong> <span class="muted small">${esc(x.account)}</span>
      <div class="muted small">${+x.shares.toFixed(6)} shares${v.px ? ' · ' + money(v.value) : ' · no price available'}${v.gain != null ? ' · <span class="' + (v.gain >= 0 ? 'gain' : 'loss') + '">' + signed(v.gain) + ' total</span>' : ''}</div></div>
      <button class="del" data-do="delholding" data-row="${x.row}" data-sym="${esc(x.symbol)}" ${busy ? 'disabled' : ''}>Remove</button></div>`;
  });
  return h;
}


// ---------- Report card ----------
let report = null, reportRange = '1M';
function loadReport(r) {
  reportRange = r; report = { loading: true }; render();
  call('getReport', KEY, r).then((x) => { report = x; render(); }).catch((e) => { report = { error: e.message || String(e) }; render(); });
}
function compareChart(c) {
  if (!c) return '<p class="empty">Not enough account history yet. This fills in as days pass.</p>';
  const W = 360, H = 170, pad = 12;
  const vals = c.points.flatMap((p) => [p.you, p.spy]);
  let min = Math.min(...vals, 0), max = Math.max(...vals, 0); if (max === min) { max += 1; min -= 1; }
  const y = (v) => pad + (H - 2 * pad) * (1 - (v - min) / (max - min));
  const x = (i) => i * W / (c.points.length - 1);
  const path = (k) => c.points.map((p, i) => (i ? 'L' : 'M') + x(i).toFixed(1) + ' ' + y(p[k]).toFixed(1)).join(' ');
  return `<div class="chart" style="height:170px;cursor:default"><svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
    <line class="baseline" x1="0" x2="${W}" y1="${y(0).toFixed(1)}" y2="${y(0).toFixed(1)}"/>
    <path class="line2" vector-effect="non-scaling-stroke" d="${path('spy')}"/><path class="line1" vector-effect="non-scaling-stroke" d="${path('you')}"/></svg></div>
    <div class="legend"><span><i style="background:var(--gold)"></i>You ${pct(c.you)}</span><span><i style="background:var(--muted)"></i>S&amp;P 500 ${pct(c.spy)}</span></div>
    <p class="small" style="margin-top:6px">${c.you >= c.spy ? 'You’re ahead of the market by ' : 'The market is ahead of you by '}${Math.abs(c.you - c.spy).toFixed(2)} points.</p>`;
}
function reportView() {
  let h = header() + '<h2 style="margin-top:22px">Report card</h2>';
  h += `<div class="seg" style="margin-top:6px">${['1M', '3M', '1Y'].map((r) => `<button data-do="rrange" data-range="${r}" class="${reportRange === r ? 'on' : ''}">${r}</button>`).join('')}</div>`;
  if (!report || report.loading) return h + '<p class="muted" style="margin-top:20px">Crunching your trades…</p>';
  if (report.error) return h + `<div class="notice bad" style="margin-top:16px">${esc(report.error)}</div>`;
  h += '<h2>You vs. the S&amp;P 500</h2>' + compareChart(report.compare);
  const card = (name, s) => `<div class="card2"><strong>${name}</strong>
    <div class="big ${s.total >= 0 ? 'gain' : 'loss'}">${signed(s.total)}</div>
    <div class="muted small">${s.trades} trades · ${s.winRate.toFixed(0)}% wins</div>
    <div class="muted small">Avg win ${money(s.avgWin)} · avg loss ${money(Math.abs(s.avgLoss))}</div>
    <div class="muted small">Profit factor ${s.profitFactor == null ? '∞' : s.profitFactor.toFixed(2)}</div></div>`;
  h += '<h2>Bot strategies</h2>';
  if (!report.stats.all.trades) h += '<p class="empty">No finished bot trades in this period yet. Results show up after the bot’s first round trips.</p>';
  else h += `<div class="cards">${card('All strategies', report.stats.all)}${card('Breakout', report.stats.orb)}${card('VWAP pullback', report.stats.vwap)}${card('Momentum', report.stats.momentum)}</div>
    <p class="muted small" style="margin-top:8px">Profit factor = money won ÷ money lost. Above 1 means the strategy makes money; aim for 1.5+ before trusting it with real money.</p>`;
  if (report.trades.length) {
    h += '<h2>Finished bot trades</h2>';
    report.trades.forEach((t) => {
      h += `<div class="row"><div class="grow"><strong>${esc(t.symbol)}</strong> <span class="muted small">${esc(t.strategy)} · ${esc(t.date)}</span>
        <div class="muted small">${+t.qty.toFixed(4)} sh · ${price(t.entry)} → ${price(t.exit)}</div></div>
        <div class="right ${t.pnl >= 0 ? 'gain' : 'loss'}"><strong>${signed(t.pnl)}</strong><div class="small">${pct(t.ret)}</div></div></div>`;
    });
  }
  return h;
}

// ---------- Portfolio breakdown ----------
function portfolioView() {
  let h = header() + '<h2 style="margin-top:22px">Portfolio breakdown</h2>';
  const items = [];
  (D.positions || []).forEach((p) => items.push({ symbol: p.symbol, account: 'GOLDMINEBOT', value: p.value }));
  (D.other || []).forEach((x) => { const v = holdingValue(x); if (v.value > 0) items.push({ symbol: x.symbol, account: x.account, value: v.value }); });
  (D.crypto || []).forEach((c) => { const v = num(c['Value $']); if (v > 0) items.push({ symbol: c['Symbol'], account: 'Coinbase', value: v }); });
  const cash = Math.max(0, (D.account && D.account.cash) || 0);
  const total = items.reduce((t, i) => t + i.value, 0) + cash;
  if (!total) return h + '<p class="empty">Nothing to break down yet.</p>';
  h += `<div class="rowlink"><span>Total across accounts</span><strong>${money(total)}</strong></div>`;
  const bySym = {};
  items.forEach((i) => { bySym[i.symbol] = (bySym[i.symbol] || 0) + i.value; });
  const rows = Object.entries(bySym).sort((a, b) => b[1] - a[1]);
  const invested = total - cash;
  const big = rows.filter((r) => invested && r[1] / invested > 0.25);
  if (big.length) h += `<div class="notice" style="margin-top:14px">${big.map((r) => `<strong>${esc(r[0])}</strong> is ${(r[1] / invested * 100).toFixed(0)}%`).join(', ')} of your invested money. A single stock above about 25% means one bad day there moves your whole portfolio.</div>`;
  const barRow = (label, v) => `<div style="padding:10px 0;border-bottom:1px solid var(--line)"><div style="display:flex;justify-content:space-between"><strong>${esc(label)}</strong><span>${money(v)} <span class="muted small">${(v / total * 100).toFixed(1)}%</span></span></div><div class="bar"><i style="width:${Math.max(1, v / total * 100).toFixed(1)}%"></i></div></div>`;
  h += '<h2>By holding</h2>' + rows.map((r) => barRow(r[0], r[1])).join('') + (cash ? barRow('Cash', cash) : '');
  const byAcc = {};
  items.forEach((i) => { byAcc[i.account] = (byAcc[i.account] || 0) + i.value; });
  if (cash) byAcc['GOLDMINEBOT'] = (byAcc['GOLDMINEBOT'] || 0) + cash;
  h += '<h2>By account</h2>' + Object.entries(byAcc).sort((a, b) => b[1] - a[1]).map((r) => barRow(r[0], r[1])).join('');
  h += '<p class="muted small" style="margin-top:10px">Sector breakdown arrives with the daily scanner’s company data.</p>';
  return h;
}



// ---------- Movers / IPOs / helpers ----------
let moversTab = 'gainers';
function fmtTime(hm) { const p = String(hm).split(':'); const hh = Number(p[0]); return (hh % 12 || 12) + ':' + p[1] + (hh >= 12 ? ' PM' : ' AM'); }
function moversSection() {
  const m = D.movers;
  if (!m) return '';
  const tabs = [['gainers', 'Gainers'], ['losers', 'Losers'], ['actives', 'Most active']];
  let h = `<h2>Today’s movers</h2><div class="seg">${tabs.map((t) => `<button data-do="moverstab" data-t="${t[0]}" class="${moversTab === t[0] ? 'on' : ''}">${t[1]}</button>`).join('')}</div>`;
  const list = m[moversTab] || [];
  if (!list.length) return h + '<p class="empty">No data right now.</p>';
  list.forEach((x) => {
    h += `<button class="item" data-open="${esc(x.symbol)}" style="grid-template-columns:1fr auto"><span class="sym">${esc(x.symbol)}</span>${
      moversTab === 'actives' ? `<span class="muted small">${compact(x.volume)} shares</span>` : `<span class="pill ${x.pct >= 0 ? '' : 'down'}">${price(x.price)} ${pct(x.pct)}</span>`}</button>`;
  });
  return h + '<p class="muted small" style="margin-top:6px">Stocks $2 and up. Big movers are often volatile; research before buying.</p>';
}
function iposSection() {
  let h = `<h2 style="display:flex;justify-content:space-between;align-items:baseline">Upcoming IPOs <button class="ghost" data-do="gotab" data-tab="ipowatch">IPO Watch${D.ipoWatch && D.ipoWatch.length ? ' (' + D.ipoWatch.length + ')' : ''} ›</button></h2>`;
  if (!D.ipos || !D.ipos.length) return h + '<p class="empty">No US IPOs scheduled in the next 3 weeks.</p>';
  D.ipos.slice(0, 8).forEach((i) => {
    h += `<div class="row"><div class="grow"><strong>${esc(i.name)}</strong>${i.symbol ? ' <span class="muted small">' + esc(i.symbol) + '</span>' : ''}
      <div class="muted small">${esc(i.exchange)}${i.price ? ' · $' + esc(i.price) : ''}${i.value ? ' · raising ' + money(i.value).replace('.00', '') : ''}${i.status && i.status !== 'expected' ? ' · ' + esc(i.status) : ''}</div></div>
      <strong class="small">${esc(fmtDay(i.date))}</strong></div>`;
  });
  return h;
}

// ---------- Earnings ----------
function fmtDay(d) { const x = new Date(d + 'T12:00:00'); return x.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }); }
function hourLabel(hh) { return hh === 'bmo' ? 'before the open' : hh === 'amc' ? 'after the close' : ''; }
function earningsSection() {
  let h = '<h2>Upcoming earnings</h2>';
  if (!D.earningsReady) return h + '<p class="empty">Add a free FINNHUB_API_KEY in Script properties to see earnings dates for your stocks.</p>';
  if (!D.earnings || !D.earnings.length) return h + '<p class="empty">None in the next 3 weeks for your stocks and watchlist.</p>';
  D.earnings.forEach((e) => {
    h += `<button class="item" data-open="${esc(e.symbol)}" style="grid-template-columns:1fr auto"><span><span class="sym">${esc(e.symbol)}</span><br><span class="sub">${esc(hourLabel(e.hour)) || 'time not announced'}</span></span>
      <strong>${esc(fmtDay(e.date))}</strong></button>`;
  });
  return h;
}

// ---------- Ask GOLDMINEBOT ----------
let chat = [], asking = false;
function askView() {
  let h = header() + '<h2 style="margin-top:22px">Ask GOLDMINEBOT</h2><p class="muted small">Answers use your live accounts plus the news. It can explain and compare, but it can’t place trades.</p>';
  if (!D.status || !D.status.anthropic) h += '<div class="notice bad" style="margin-top:12px">Add ANTHROPIC_API_KEY in Script properties to turn this on.</div>';
  if (!chat.length) {
    h += '<div class="suggest">' + ['How is my portfolio doing today?', 'Why did TSLA move today?', 'How did the bot do this week?', 'What earnings are coming up for my stocks?', 'Which of my stocks is riskiest?']
      .map((q) => `<button class="tickbtn" data-do="askq" data-q="${esc(q)}">${esc(q)}</button>`).join('') + '</div>';
  }
  h += '<div class="chat">' + chat.map((m) => `<div class="msg ${m.role === 'user' ? 'user' : 'bot'}">${esc(m.text)}</div>`).join('') +
    (asking ? '<div class="msg bot muted">Thinking… (up to a minute)</div>' : '') + '</div>';
  h += `<form class="askbar" id="askForm"><textarea name="q" rows="1" placeholder="Ask about your money or the market…" ${asking ? 'disabled' : ''}></textarea>
    <button class="primary" ${asking ? 'disabled' : ''}>Ask</button></form>`;
  if (chat.length) h += '<button class="del" data-do="clearchat">Start a new conversation</button>';
  return h;
}
function sendAsk(q) {
  q = String(q || '').trim(); if (!q || asking) return;
  const history = chat.slice();
  chat.push({ role: 'user', text: q }); asking = true; render(); window.scrollTo(0, document.body.scrollHeight);
  call('askBot', KEY, q, history).then((a) => { chat.push({ role: 'assistant', text: a }); })
    .catch((e) => { chat.push({ role: 'assistant', text: 'Something went wrong: ' + (e.message || e) }); })
    .finally(() => { asking = false; render(); window.scrollTo(0, document.body.scrollHeight); });
}


// ---------- Compare ----------
let cmpSort = 'mcap', cmpFilter = '';
const CMP_SORTS = [['mcap', 'Market value (biggest first)'], ['rev', 'Revenue'], ['profit', 'Profit'], ['growth', 'Growth (fastest first)'],
  ['score', 'Value score (best first)'], ['pe', 'P/E (lowest first)'], ['today', 'Today % (best first)'], ['buyPct', 'Analysts (most bullish)'],
  ['insNet', 'Insider buying (most)'], ['roe', 'Return on equity'], ['pos52', 'Near 52-wk high'], ['found', 'Where you found it']];
function cmpNum(r, k) { const v = r[k]; if (v === '' || v == null) return null; const n = Number(String(v).replace(/[^0-9.\-]/g, '')); return isNaN(n) ? null : n; }
function cmpRows() {
  let list = (D.compare || []).map((r) => ({
    row: r._row, sym: String(r['Ticker']).trim().toUpperCase(), name: r['Company'], found: r['Found at'], industry: r['Industry'],
    price: cmpNum(r, 'Price $'), today: cmpNum(r, 'Today %'), mcap: cmpNum(r, 'Market value $B'), rev: cmpNum(r, 'Revenue $B'),
    profit: cmpNum(r, 'Profit $B'), margin: cmpNum(r, 'Profit margin %'), growth: cmpNum(r, 'Revenue growth %'),
    pe: cmpNum(r, 'P/E'), score: cmpNum(r, 'Value score'), updated: r['Updated'],
    de: cmpNum(r, 'Debt/Equity'), roe: cmpNum(r, 'ROE %'), divy: cmpNum(r, 'Dividend yield %'), beta: cmpNum(r, 'Beta'),
    pos52: cmpNum(r, '52-wk position %'), buyPct: cmpNum(r, 'Analysts buy %'), insNet: cmpNum(r, 'Insider net 90d'), logo: r['Logo']
  }));
  if (cmpFilter) list = list.filter((x) => x.found === cmpFilter);
  const lowFirst = { pe: true, score: true };
  list.sort((a, b) => {
    if (cmpSort === 'found') return String(a.found).localeCompare(String(b.found));
    let x = a[cmpSort], y = b[cmpSort];
    if (cmpSort === 'pe' || cmpSort === 'score') { x = x != null && x > 0 ? x : null; y = y != null && y > 0 ? y : null; }
    if (x == null) return 1; if (y == null) return -1;
    return lowFirst[cmpSort] ? x - y : y - x;
  });
  return list;
}
function bn(n) { if (n == null) return '—'; const a = Math.abs(n); return (n < 0 ? '−' : '') + '$' + (a >= 1000 ? (a / 1000).toFixed(2) + 'T' : a >= 1 ? a.toFixed(1) + 'B' : (a * 1000).toFixed(0) + 'M'); }
function compareView() {
  let h = header() + '<h2 style="margin-top:22px">Compare companies</h2><p class="muted small">Each bar is sized against the other companies in the list. Numbers update every morning from company filings.</p>';
  if (!D.earningsReady) h += '<div class="notice bad" style="margin-top:12px">Add FINNHUB_API_KEY in Script properties to fill in company numbers.</div>';
  h += `<form class="card" id="compareForm" style="margin-top:14px"><div class="pair">
      <label>Ticker<input name="symbol" placeholder="RPC" autocapitalize="characters" required></label>
      <label>Where you found it<input name="found" placeholder="NAVember 2026" value="${esc(cmpFilter)}"></label></div>
      <button class="primary" ${busy ? 'disabled' : ''}>Add to Compare</button></form>`;
  const all = D.compare || [];
  if (!all.length) return h + '<p class="empty">Nothing to compare yet. Add a ticker above, or tap “+ Compare” on any stock page.</p>';
  const founds = [...new Set(all.map((r) => r['Found at']).filter(Boolean))];
  h += `<div class="controls"><select id="cmpSort">${CMP_SORTS.map((o) => `<option value="${o[0]}" ${cmpSort === o[0] ? 'selected' : ''}>Sort: ${o[1]}</option>`).join('')}</select>
    <select id="cmpFilter"><option value="">All sources</option>${founds.map((f) => `<option ${cmpFilter === f ? 'selected' : ''}>${esc(f)}</option>`).join('')}</select></div>
    <button class="outline" style="margin-top:10px" data-do="cmprefresh" ${busy ? 'disabled' : ''}>${busy ? 'Updating numbers…' : 'Refresh numbers now'}</button>`;
  const list = cmpRows();
  const max = (k) => Math.max(...list.map((x) => Math.abs(x[k] || 0)), 0) || 1;
  const mM = max('mcap'), mR = max('rev'), mP = max('profit'), mG = Math.max(...list.map((x) => x.growth || 0), 1);
  const bar = (label, v, m, text, cls) => `<div class="metric"><span class="lbl">${label}</span><span class="track"><i class="${cls || ''}" style="width:${v == null ? 0 : Math.max(2, Math.min(100, Math.abs(v) / m * 100)).toFixed(1)}%"></i></span><span class="val">${text}</span></div>`;
  const tone = (v, good, ok) => v == null ? 'n' : v <= good[0] ? good[1] : v <= ok[0] ? ok[1] : 'r';
  h += '<div id="cmpList">';
  list.forEach((x) => {
    const gCls = x.growth == null ? '' : x.growth >= 15 ? 'g' : x.growth >= 0 ? 'y' : 'r';
    const peCls = x.pe == null ? 'n' : x.pe <= 0 ? 'r' : x.pe <= 20 ? 'g' : x.pe <= 40 ? 'y' : 'r';
    const scCls = x.score == null ? 'n' : x.score < 1 ? 'g' : x.score <= 2 ? 'y' : 'r';
    h += `<div class="ccard"><div class="head">${x.logo ? `<img class="logo" src="${esc(x.logo)}" alt="">` : ''}<div class="grow" data-open="${esc(x.sym)}" style="cursor:pointer"><span class="sym">${esc(x.sym)}</span>
        <div class="name">${esc(x.name || 'Loading company data…')}${x.industry ? ' · ' + esc(x.industry) : ''}</div></div>
        <span class="pill ${x.today == null ? 'flat' : x.today >= 0 ? '' : 'down'}" style="min-width:auto">${x.price != null ? price(x.price) : '—'}${x.today != null ? ' ' + pct(x.today) : ''}</span></div>
      ${bar('Market value', x.mcap, mM, bn(x.mcap))}
      ${bar('Revenue', x.rev, mR, bn(x.rev))}
      ${bar('Profit', x.profit, mP, bn(x.profit), x.profit == null ? '' : x.profit >= 0 ? 'g' : 'r')}
      ${bar('Growth', x.growth != null ? Math.max(x.growth, 0) : null, mG, x.growth == null ? '—' : pct(x.growth), gCls)}
      ${bar('52-wk range', x.pos52, 100, x.pos52 == null ? '—' : x.pos52.toFixed(0) + '%', x.pos52 == null ? '' : x.pos52 >= 70 ? 'g' : x.pos52 >= 30 ? 'y' : 'r')}
      <div class="chips"><span class="chip2 ${peCls}">P/E ${x.pe == null ? '—' : x.pe.toFixed(1)}</span>
        <span class="chip2 ${scCls}">Value score ${x.score == null ? '—' : x.score.toFixed(2)}</span>
        ${x.margin != null ? `<span class="chip2 ${x.margin >= 0 ? 'g' : 'r'}">Margin ${x.margin.toFixed(1)}%</span>` : ''}
        ${x.buyPct != null ? `<span class="chip2 ${x.buyPct >= 60 ? 'g' : x.buyPct >= 40 ? 'y' : 'r'}">Analysts ${x.buyPct.toFixed(0)}% buy</span>` : ''}
        ${x.insNet != null ? `<span class="chip2 ${x.insNet > 0 ? 'g' : x.insNet < 0 ? 'r' : 'n'}">Insiders ${x.insNet > 0 ? '+' : ''}${x.insNet}</span>` : ''}
        ${x.roe != null ? `<span class="chip2 ${x.roe >= 15 ? 'g' : x.roe >= 0 ? 'y' : 'r'}">ROE ${x.roe.toFixed(0)}%</span>` : ''}
        ${x.de != null ? `<span class="chip2 ${x.de <= 1 ? 'g' : x.de <= 2 ? 'y' : 'r'}">Debt/eq ${x.de.toFixed(2)}</span>` : ''}
        ${x.beta != null ? `<span class="chip2 n">Beta ${x.beta.toFixed(2)}</span>` : ''}
        ${x.divy ? `<span class="chip2 n">Div ${x.divy.toFixed(1)}%</span>` : ''}
        ${x.found ? `<span class="chip2 n">${esc(x.found)}</span>` : ''}
        <button class="del" data-do="cmpremove" data-row="${x.row}" data-sym="${esc(x.sym)}">Remove</button></div></div>`;
  });
  h += '</div>';
  h += `<p class="muted small" style="margin-top:12px">Value score = P/E ÷ revenue growth. Under 1 (green) means cheap for how fast it grows; over 2 (red) means expensive for its growth. Past numbers, not predictions.</p>`;
  return h;
}


// ---------- Alpaca tab ----------
let alp = null;
function loadAlpaca() {
  alp = alp && !alp.error ? Object.assign(alp, { refreshing: true }) : { loading: true }; render();
  call('getAlpaca', KEY).then((a) => { alp = a; render(); }).catch((e) => { alp = { error: e.message || String(e) }; render(); });
}
function statusLabel(s) {
  if (s === 'filled') return ['filled', 'Filled'];
  if (s === 'partially_filled') return ['pending', 'Partly filled'];
  if (['new', 'accepted', 'pending_new', 'held'].indexOf(s) >= 0) return ['pending', 'Waiting'];
  if (s === 'rejected') return ['rejected', 'Rejected'];
  if (s === 'expired') return ['canceled', 'Expired'];
  if (s === 'canceled' || s === 'pending_cancel') return ['canceled', 'Canceled'];
  return ['canceled', s];
}
function whenShort(t) {
  if (!t) return '';
  const d = new Date(t);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' ' + d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
}
function orderWhat(o) {
  const amt = o.notional ? money(o.notional) : (+Number(o.qty).toFixed(6)) + ' sh';
  return `${o.side === 'buy' ? 'Buy' : 'Sell'} ${amt}${o.type && o.type !== 'market' ? ' · ' + o.type + (o.limit ? ' ' + price(o.limit) : '') + (o.stop ? ' stop ' + price(o.stop) : '') : ''}`;
}
function alpacaView() {
  let h = header() + '<h2 style="margin-top:22px">Alpaca account</h2>';
  if (!alp || alp.loading) return h + '<p class="muted" style="margin-top:16px">Loading your Alpaca account…</p>';
  if (alp.error) return h + `<div class="notice bad" style="margin-top:12px">${esc(alp.error)}</div>`;
  const a = alp.account, live = alp.mode === 'LIVE';
  const next = alp.marketOpen ? 'Market open · closes ' + whenShort(alp.nextClose) : 'Market closed · opens ' + whenShort(alp.nextOpen);
  h += `<p class="muted small">${live ? 'Live money' : 'Paper money (practice)'} · ${esc(next)}</p>`;
  const invested = alp.positions.reduce((t, p) => t + p.value, 0), unreal = alp.positions.reduce((t, p) => t + p.pl, 0);
  h += `<div class="sum">
    <div class="card2"><span class="muted small">Total value</span><div class="big">${money(a.equity)}</div><div class="small ${a.dayPnl >= 0 ? 'gain' : 'loss'}">${signed(a.dayPnl)} today</div></div>
    <div class="card2"><span class="muted small">Invested in stocks</span><div class="big">${money(invested)}</div><div class="small ${unreal >= 0 ? 'gain' : 'loss'}">${signed(unreal)} total</div></div>
    <div class="card2"><span class="muted small">Cash</span><div class="big">${money(a.cash)}</div></div>
    <div class="card2"><span class="muted small">Buying power</span><div class="big">${money(a.buyingPower)}</div></div></div>
    ${alp.dividends ? `<div class="card2" style="margin-top:10px"><span class="muted small">Dividends received (12 months)</span><div class="big">${money(alp.dividends.total)}</div>${alp.dividends.items.length ? '<div class="muted small">' + alp.dividends.items.slice(0, 4).map((d) => esc(d.symbol) + ' ' + money(d.amount)).join(' · ') + '</div>' : '<div class="muted small">None yet. They land here when a stock you own pays one.</div>'}</div>` : ''}
    <button class="outline" style="margin-top:12px" data-do="alprefresh">${alp.refreshing ? 'Refreshing…' : 'Refresh'}</button>`;

  h += `<h2>Pending orders (${alp.open.length})</h2>`;
  if (!alp.open.length) h += '<p class="empty">No orders waiting. Orders placed while the market is closed wait here until it opens.</p>';
  alp.open.forEach((o) => {
    h += `<div class="row"><div class="grow"><strong data-open="${esc(o.symbol)}" style="cursor:pointer">${esc(o.symbol)}</strong> <span class="stat pending">Waiting</span>
      <div class="small">${esc(orderWhat(o))}</div><div class="src">${esc(o.source)} · placed ${esc(whenShort(o.time))} · ${o.tif === 'gtc' ? 'good until canceled' : 'today only'}</div></div>
      ${o.mine ? `<button class="del" data-do="cancelorder2" data-id="${esc(o.id)}">Cancel</button>` : ''}</div>`;
  });

  h += `<h2>Stocks you own (${alp.positions.length})</h2>`;
  if (!alp.positions.length) h += '<p class="empty">No stocks yet. When an order fills, the stock shows up here.</p>';
  alp.positions.sort((x, y) => y.value - x.value).forEach((p) => {
    h += `<div class="row" data-open="${esc(p.symbol)}" style="cursor:pointer"><div class="grow"><strong>${esc(p.symbol)}</strong> <span class="src">${esc(p.source)}</span>
      <div class="small">${+p.qty.toFixed(6)} sh · avg ${price(p.avg)} · now ${price(p.price)}</div>
      <div class="small"><span class="${p.todayPct >= 0 ? 'gain' : 'loss'}">${pct(p.todayPct)} today</span> · <span class="${p.pl >= 0 ? 'gain' : 'loss'}">${signed(p.pl)} (${pct(p.plpc)}) total</span></div></div>
      <div class="right"><strong>${money(p.value)}</strong><div class="src">cost ${money(p.cost)}</div></div></div>`;
  });

  h += '<h2>Activity</h2>';
  if (!alp.history.length) h += '<p class="empty">No finished orders yet.</p>';
  alp.history.forEach((o) => {
    const st = statusLabel(o.status);
    h += `<div class="row"><div class="grow"><strong>${esc(o.symbol)}</strong> <span class="stat ${st[0]}">${st[1]}</span>
      <div class="small">${esc(orderWhat(o))}${o.price ? ' · filled at ' + price(o.price) : ''}</div><div class="src">${esc(o.source)}</div></div>
      <div class="right src">${esc(whenShort(o.time))}</div></div>`;
  });
  return h;
}


// ---------- Morning brief ----------
function briefIsNew() { return D && D.brief && String(D.brief.time).slice(0, 10) === String(D.updated).slice(0, 10); }
function briefView() {
  let h = header() + '<h2 style="margin-top:22px">Morning brief</h2><p class="muted small">Sent on weekdays before the market opens. Change the time in Settings.</p>';
  if (!D.briefs || !D.briefs.length) return h + '<p class="empty">No briefs yet. The first one arrives the next weekday morning, or send one now from Settings.</p>';
  D.briefs.forEach((b, i) => {
    h += `<details class="brief" ${i === 0 ? 'open' : ''}><summary>${esc(fmtDay(String(b.time).slice(0, 10)))} <span class="muted small" style="font-weight:600">${esc(String(b.time).slice(11, 16))}</span>${i === 0 && briefIsNew() ? ' <span class="stat pending">New</span>' : ''}</summary><div class="txt">${esc(b.text)}</div></details>`;
  });
  return h;
}


// ---------- Health & improvements ----------
function improvementsPending() { return (D.improvements || []).filter((r) => r['Type'] === 'Setting' && r['Status'] === 'Pending').length; }
function healthBad() { return D.health && D.health['Status'] !== 'All good'; }
function healthView() {
  let h = header() + '<h2 style="margin-top:22px">Health &amp; improvements</h2><p class="muted small">GOLDMINEBOT checks itself every morning and writes an improvement report every Saturday. Nothing changes until you approve it.</p>';
  h += '<h2>Daily self-check</h2>';
  if (!D.health) h += '<p class="empty">No self-check yet. The first one runs tomorrow at 6:30 AM, or run one now.</p>';
  else {
    const ok = D.health['Status'] === 'All good';
    h += `<div class="card2"><strong class="${ok ? 'gain' : 'loss'}">${ok ? '✓ All good' : '⚠ Needs attention'}</strong> <span class="muted small">${esc(String(D.health['Time']).slice(5, 16))}</span>
      ${D.health['Issues'] ? '<div class="small" style="margin-top:8px;white-space:pre-wrap">' + String(D.health['Issues']).split('\n').map((i) => '• ' + esc(i)).join('\n') + '</div>' : ''}
      ${D.health['Fixed'] ? '<div class="small gain" style="margin-top:8px">Fixed automatically: ' + esc(D.health['Fixed']) + '</div>' : ''}</div>`;
  }
  h += `<button class="outline" style="margin-top:10px" data-do="selfcheck" ${busy ? 'disabled' : ''}>Run self-check now</button>`;

  h += '<h2>Weekly improvement report</h2>';
  const list = D.improvements || [];
  if (!list.length) h += '<p class="empty">No report yet. The first one arrives Saturday morning, or write one now.</p>';
  const latestT = list.length ? list[0]['Time'] : '';
  const summary = list.find((r) => r['Type'] === 'Summary');
  if (summary) h += `<div class="brief" style="margin-top:6px"><strong>${esc(fmtDay(String(summary['Time']).slice(0, 10)))}</strong><div class="txt">${esc(summary['Reason'])}</div></div>`;
  const label = (k) => { const f = (D.settingsSchema || []).find((x) => x.k === k); return f ? f.l : k; };
  const sets = list.filter((r) => r['Type'] === 'Setting');
  if (sets.length) h += '<h2>Suggested setting changes</h2>';
  sets.forEach((r) => {
    const pending = r['Status'] === 'Pending';
    h += `<div class="ccard"><strong>${esc(label(r['Setting']))}</strong>
      <div style="margin-top:4px"><span class="muted">${esc(r['Current'])}</span> → <strong style="color:var(--gold)">${esc(r['Suggested'])}</strong></div>
      <div class="small" style="margin-top:6px">${esc(r['Reason'])}</div>
      ${pending ? `<div class="controls"><button class="primary" data-do="improve" data-ok="1" data-row="${r._row}" data-time="${esc(r['Time'])}" ${busy ? 'disabled' : ''}>Approve</button>
        <button class="outline" data-do="improve" data-ok="0" data-row="${r._row}" data-time="${esc(r['Time'])}" ${busy ? 'disabled' : ''}>Dismiss</button></div>`
        : `<div class="small" style="margin-top:6px">${/^Auto-approved/.test(r['Status']) ? '<span class="stat filled">Applied by the bot</span> <span class="muted">' + esc(String(r['Status']).slice(14, 30)) + '</span>' : '<span class="muted">' + esc(r['Status']) + '</span>'}</div>`}</div>`;
  });
  const notes = list.filter((r) => (r['Type'] === 'Problem' || r['Type'] === 'Idea') && r['Status'] === 'New');
  if (notes.length) {
    h += '<h2>Problems and ideas</h2>';
    notes.forEach((r) => {
      h += `<div class="row"><div class="grow"><span class="stat ${r['Type'] === 'Problem' ? 'rejected' : 'pending'}">${r['Type'] === 'Problem' ? 'Problem' : 'Idea'}</span>
        <div class="small" style="margin-top:4px">${esc(r['Reason'])}</div></div>
        <button class="del" data-do="improve" data-ok="0" data-row="${r._row}" data-time="${esc(r['Time'])}">Dismiss</button></div>`;
    });
  }
  h += `<button class="outline" style="margin-top:14px" data-do="improvenow" ${busy ? 'disabled' : ''}>${busy ? 'Working…' : 'Write a new report now'}</button>
    <p class="muted small" style="margin-top:8px">The AI only suggests small, evidence-based changes to bot limits, timing and filters. On paper money (if allowed in Settings › Self-improvement) the bot applies small safe ones itself and tells you; it never changes your loss limit, $ per trade, live-money settings or keys. Tip: until there are about 15 finished trades, expect few or no setting suggestions.</p>`;
  return h;
}


// ---------- IPO Watch ----------
const IPO_TONE = { 'Private': 'n', 'Filed to go public': 'y', 'IPO scheduled': 'y', 'IPO priced': 'g', 'Listed (US)': 'g', 'Listed abroad': 'n', 'IPO withdrawn': 'r' };
const IPO_ORDER = ['IPO scheduled', 'IPO priced', 'Filed to go public', 'Listed (US)', 'Listed abroad', 'Private', 'IPO withdrawn'];
function ipoWatchView() {
  let h = header() + `<h2 style="margin-top:22px">IPO Watch</h2>
    <p class="muted small">Add private companies you hear about. Every morning GOLDMINEBOT checks the IPO calendar, SEC filings and stock exchanges, and notifies you when one files to go public, gets an IPO date, or starts trading. On IPO day you also get an 8 AM reminder with tips for buying a new stock.</p>
    <form class="card" id="ipoForm" style="margin-top:14px"><div class="pair">
      <label>Company name<input name="name" placeholder="e.g. GoldenTree, Stripe" required></label>
      <label>Where you heard of it<input name="found" placeholder="GoldenTree conference"></label></div>
      <button class="primary" ${busy ? 'disabled' : ''}>${busy ? 'Checking…' : 'Add to IPO Watch'}</button></form>`;
  if (!D.earningsReady) h += '<div class="notice bad" style="margin-top:12px">IPO Watch needs FINNHUB_API_KEY in Script properties.</div>';
  const list = (D.ipoWatch || []).slice().sort((a, b) => IPO_ORDER.indexOf(a['Status']) - IPO_ORDER.indexOf(b['Status']));
  h += `<h2>Watching (${list.length})</h2>`;
  if (!list.length) h += '<p class="empty">Nothing yet. Add a company above, or tap 🚀 on an Intel note.</p>';
  list.forEach((r) => {
    const st = r['Status'] || '—', tone = IPO_TONE[st] || 'n';
    const det = String(r['Details'] || '').split('\n');
    const link = det.find((x) => /^https?:\/\//.test(x));
    const tradable = st === 'Listed (US)' || (st === 'IPO priced' && r['Ticker']);
    h += `<div class="ccard"><div class="head"><div class="grow"><span class="sym">${esc(r['Company'])}</span>
        <div class="name">${r['Found at'] ? esc(r['Found at']) + ' · ' : ''}checked ${esc(String(r['Last checked'] || 'not yet').slice(5, 16))}</div></div>
        <span class="chip2 ${tone}">${esc(st)}</span></div>
      <div class="small" style="margin-top:8px">${r['Ticker'] ? '<strong>' + esc(r['Ticker']) + '</strong>' + (r['Exchange'] ? ' · ' + esc(r['Exchange']) : '') + ' · ' : ''}${r['Date'] ? esc(fmtDay(String(r['Date']).slice(0, 10))) + ' · ' : ''}${esc(det.filter((x) => !/^https?:\/\//.test(x)).join(' '))}</div>
      <div class="chips">${tradable ? `<button class="tickbtn" data-open="${esc(r['Ticker'])}">Open ${esc(r['Ticker'])}</button><button class="tickbtn" data-do="addcompare" data-sym="${esc(r['Ticker'])}" data-found="${esc(r['Found at'] || 'IPO Watch')}">📊 Compare</button>` : ''}
        ${link ? `<a class="tickbtn" href="${esc(link)}" target="_blank" rel="noopener" style="text-decoration:none">SEC filings</a>` : ''}
        <button class="del" data-do="iporemove" data-row="${r._row}" data-name="${esc(r['Company'])}">Remove</button></div></div>`;
  });
  h += `<button class="outline" style="margin-top:14px" data-do="ipocheck" ${busy ? 'disabled' : ''}>${busy ? 'Checking…' : 'Check all now'}</button>
    <p class="muted small" style="margin-top:8px"><strong>What the statuses mean:</strong> Private = no filing found yet. Filed to go public = it filed an S-1/F-1 with the SEC, usually weeks to months before an IPO. IPO scheduled = it has a date. Listed (US) = tradable in GOLDMINEBOT. Listed abroad = trades on a foreign exchange only.</p>`;
  return h;
}

// ---------- More ----------
function moreView() {
  const link = (tabName, label, sub) => `<button class="rowlink" data-do="gotab" data-tab="${tabName}" style="width:100%;background:none;border-left:0;border-right:0;border-top:0;cursor:pointer;text-align:left"><span><strong>${label}</strong><br><span class="muted small">${sub}</span></span><span class="muted">›</span></button>`;
  return header() + '<h2 style="margin-top:22px">More</h2>' +
    link('ask', 'Ask GOLDMINEBOT', 'Questions about your money, stocks and the bot') +
    link('health', 'Health &amp; improvements' + (healthBad() ? ' <span class="stat rejected">Check</span>' : '') + (improvementsPending() ? ' <span class="stat pending">' + improvementsPending() + ' to review</span>' : ''), 'Daily self-check and weekly AI suggestions') +
    link('brief', 'Morning brief' + (briefIsNew() ? ' <span class="stat pending">New</span>' : ''), 'Today’s summary and past briefs') +
    link('compare', 'Compare companies', 'Side-by-side company numbers') +
    link('ipowatch', 'IPO Watch', 'Private companies you’re waiting to go public') +
    link('alerts', 'Alerts', 'Price and % move alerts') +
    link('auto', 'Auto-invest', 'Recurring buys') +
    link('holdings', 'Other accounts', 'Robinhood and other holdings') +
    link('portfolio', 'Portfolio breakdown', 'All your money, by stock and account') +
    link('models', 'Trade models', 'Switch the bot between ready-made rule sets') +
    link('report', 'Report card', 'Bot results vs. the S&P 500') +
    link('settings', 'Settings', 'Limits, notifications, brief, account');
}

// ---------- Settings ----------
function settingsView() {
  const V = D.settingsValues || {}, live = D.mode === 'LIVE';
  let h = header() + '<h2 style="margin-top:22px">Settings</h2><p class="muted small">Changes apply to the bot on its next run and to this app right away.</p><form id="settingsForm">';
  let group = '';
  D.settingsSchema.forEach((f) => {
    if (f.g !== group) { if (group) h += '</div>'; group = f.g; h += `<div class="sgroup"><h2>${esc(f.g)}</h2>`; }
    const v = V[f.k] == null ? '' : V[f.k];
    let input;
    if (f.t === 'select') input = `<select name="${f.k}">${f.o.map((o) => `<option value="${o[0]}" ${String(v) === o[0] ? 'selected' : ''}>${esc(o[1])}</option>`).join('')}</select>`;
    else if (f.t === 'time') input = `<input name="${f.k}" type="time" value="${esc(String(v).padStart(5, '0'))}">`;
    else if (f.t === 'number') input = `<input name="${f.k}" type="number" inputmode="decimal" step="${f.step || 'any'}" min="${f.min}" max="${f.max}" value="${esc(v)}" ${f.opt ? '' : 'required'}>`;
    else input = `<input name="${f.k}" type="${f.t === 'email' ? 'email' : 'text'}" value="${esc(v)}" ${f.k === 'bot_watchlist' ? 'autocapitalize="characters"' : ''}>`;
    h += `<label class="field"><span>${esc(f.l)}</span>${input}${f.h ? `<small>${esc(f.h)}</small>` : ''}</label>`;
  });
  h += `</div><div class="savebar"><button class="primary" ${busy ? 'disabled' : ''}>${busy ? 'Saving…' : 'Save settings'}</button></div></form>
    <div class="sgroup"><h2>Account</h2>
      <div class="kv"><span>Money</span><strong class="${live ? 'loss' : ''}">${live ? 'Live money' : 'Paper money'}</strong></div>
      <div class="kv"><span>Alpaca</span><span>${D.status.alpaca ? (D.alpacaError ? 'Keys set, not connecting' : 'Connected') : 'Keys missing'}</span></div>
      <div class="kv"><span>Intel research</span><span>${D.status.anthropic ? 'On' : 'Add ANTHROPIC_API_KEY'}</span></div>
      <div class="kv"><span>Earnings calendar</span><span>${D.earningsReady ? 'On' : 'Add FINNHUB_API_KEY'}</span></div>
      <div class="kv"><span>Coinbase</span><span>${D.crypto && D.crypto.length ? 'Connected (view-only)' : 'Not connected yet'}</span></div>
      <p class="muted small" style="margin-top:10px">Switching between paper and live money needs live Alpaca keys, so it’s done in Script properties (PAPER, ALPACA_KEY, ALPACA_SECRET) and the matching GitHub settings, not here.</p></div>
    <button class="outline" style="margin-top:26px" data-do="testnotify" ${busy ? 'disabled' : ''}>Send a test notification</button>
    <button class="outline" style="margin-top:10px" data-do="briefnow" ${busy ? 'disabled' : ''}>Send me a morning brief now</button>
    <button class="outline" style="margin-top:10px" data-do="resetsettings" ${busy ? 'disabled' : ''}>Reset all settings to defaults</button>`;
  return h;
}
function applyAppSettings() {
  const V = (D && D.settingsValues) || {};
  if (!applyAppSettings.done) { pillMode = V.app_price_display || 'price'; applyAppSettings.done = true; }
  const secs = Math.max(15, Number(V.app_refresh_seconds) || 60);
  if (applyAppSettings.secs !== secs) {
    clearInterval(applyAppSettings.timer);
    applyAppSettings.secs = secs;
    applyAppSettings.timer = setInterval(() => {
      if (busy || document.hidden || stock) return;
      if (tab === 'home') load(true); else if (tab === 'trading') loadTrading(true);
    }, secs * 1000);
  }
}

// ---------- render ----------
function render() {
  if (!D) return;
  if (stock) return; // detail page is open
  const views = { home: homeView, intel: intelView, trading: tradingView, bot: tradingView, live: liveView, alerts: alertsView, auto: autoView, settings: settingsView, holdings: holdingsView, report: reportView, portfolio: portfolioView, ask: askView, compare: compareView, alpaca: alpacaView, more: moreView, brief: briefView, health: healthView, ipowatch: ipoWatchView };
  applyAppSettings();
  const formFocused = document.activeElement && document.activeElement.form;
  if (busy && formFocused && tab !== 'home' && tab !== 'settings' && tab !== 'holdings' && tab !== 'compare' && tab !== 'ipowatch') return;
  if (tab !== 'home') setTrend(true);
  $('view').classList.toggle('wide', tab === 'home');
  $('view').innerHTML = views[tab]();
  if (tab === 'home') afterHome();
  fillDays();
  const navTab = ['alerts', 'auto', 'compare', 'holdings', 'portfolio', 'report', 'settings', 'more', 'brief', 'health', 'ipowatch', 'ask'].indexOf(tab) >= 0 ? 'more' : tab;
  const moreBtn = document.querySelector('nav button[data-tab="more"]');
  if (moreBtn) moreBtn.innerHTML = 'More' + (briefIsNew() || healthBad() || improvementsPending() ? ' <span style="color:var(--gold)">•</span>' : '');
  document.querySelectorAll('nav button').forEach((b) => b.classList.toggle('active', b.dataset.tab === navTab));
}

// ---------- events ----------
$('nav').addEventListener('click', (e) => {
  const b = e.target.closest('button'); if (!b) return;
  if (stock) closeStock();
  tab = b.dataset.tab; window.scrollTo(0, 0);
  if (tab === 'alpaca') loadAlpaca(); else if (tab === 'trading') loadTrading(); else if (tab === 'live') loadLive(); else render();
});
$('view').addEventListener('change', (e) => {
  if (e.target.id === 'freq') fillDays();
  if (e.target.id === 'cmpSort') { cmpSort = e.target.value; render(); }
  if (e.target.id === 'cmpFilter') { cmpFilter = e.target.value; render(); }
});

document.addEventListener('click', (e) => {
  const open = e.target.closest('[data-open]');
  const b = e.target.closest('[data-do]');
  if (b && b.dataset.do === 'pill') { e.stopPropagation(); pillMode = pillMode === 'price' ? 'pct' : pillMode === 'pct' ? 'change' : 'price'; render(); return; }
  if (!b && open) { openStock(open.dataset.open); return; }
  if (!b) return;
  const what = b.dataset.do;

  if (what === 'refresh' && !busy) { busy = true; render(); load(); }
  else if (what === 'holdings') { tab = 'holdings'; render(); window.scrollTo(0, 0); }
  else if (what === 'gotab') {
    if (stock) closeStock();
    tab = b.dataset.tab; window.scrollTo(0, 0);
    if (tab === 'alpaca') loadAlpaca();
    else if (tab === 'trading') loadTrading();
    else if (tab === 'live') loadLive();
    else if (tab === 'models') { tab = 'trading'; tradeSeg = 'models'; loadModels(); }
    else if (tab === 'report') loadReport(reportRange);
    else render();
  }
  else if (what === 'alprefresh') loadAlpaca();
  else if (what === 'trdrefresh') loadTrading();
  else if (what === 'liverefresh') loadLive();
  else if (what === 'tseg') { tradeSeg = b.dataset.s; if (tradeSeg === 'models') loadModels(); else render(); }
  else if (what === 'quick') openStock(b.dataset.sym, b.dataset.side);
  else if (what === 'cancelorder3') {
    if (!confirm('Cancel this order?')) return;
    call('cancelOrder', KEY, b.dataset.id).then(() => { toast('Order canceled'); loadTrading(true); }).catch((err) => toast(err.message || String(err)));
  }
  else if (what === 'ipocheck') { toast('Checking every company… a few seconds each'); act(call('checkIpoWatchNow', KEY), 'IPO Watch updated'); }
  else if (what === 'iporemove') {
    if (!confirm('Stop watching ' + b.dataset.name + '?')) return;
    act(call('removeIpoWatch', KEY, Number(b.dataset.row), b.dataset.name), 'Removed');
  }
  else if (what === 'ipoaddprompt') {
    const n = prompt('Private company to watch for an IPO:', '');
    if (!n) return;
    act(call('addIpoWatch', KEY, n, b.dataset.found || ''), n + ' added to IPO Watch');
  }
  else if (what === 'selfcheck') act(call('selfCheckNow', KEY), 'Self-check done');
  else if (what === 'improvenow') { toast('Writing your report… up to a minute'); act(call('improvementReportNow', KEY), 'Report ready'); }
  else if (what === 'improve') {
    const ok = b.dataset.ok === '1';
    if (ok && !confirm('Apply this setting change? The bot uses it on its next run.')) return;
    act(call('decideImprovement', KEY, Number(b.dataset.row), b.dataset.time, ok), ok ? 'Setting changed' : 'Dismissed');
  }
  else if (what === 'moverstab') { moversTab = b.dataset.t; render(); }
  else if (what === 'peerscompare') {
    const syms = [stock.symbol].concat((stock.extras && stock.extras.peers) || []);
    const found = prompt('Label for these (where you found them) — optional', 'Peers of ' + stock.symbol) || '';
    toast('Adding ' + syms.length + ' companies… up to a minute');
    call('addCompareBulk', KEY, syms, found).then((d) => { D = d; toast((d.added || []).length + ' added to Compare'); })
      .catch((err) => toast(err.message || String(err)));
  }
  else if (what === 'cancelorder2') {
    if (!confirm('Cancel this order?')) return;
    call('cancelOrder', KEY, b.dataset.id).then(() => { toast('Order canceled'); loadAlpaca(); }).catch((err) => toast(err.message || String(err)));
  }
  else if (what === 'compare') { if (stock) closeStock(); tab = 'compare'; render(); window.scrollTo(0, 0); }
  else if (what === 'addcompare') {
    const found = b.dataset.found || prompt('Where did you find ' + b.dataset.sym + '? (e.g. NAVember 2026) — optional', '') || '';
    call('addCompare', KEY, b.dataset.sym, found).then((d) => { D = d; toast(b.dataset.sym + ' added to Compare'); if (tab === 'compare') render(); })
      .catch((err) => toast(err.message || String(err)));
  }
  else if (what === 'cmprefresh') { toast('Updating numbers… about a second per company'); act(call('refreshCompareNow', KEY), 'Numbers updated'); }
  else if (what === 'cmpremove') {
    if (!confirm('Remove ' + b.dataset.sym + ' from Compare?')) return;
    act(call('removeCompare', KEY, Number(b.dataset.row), b.dataset.sym), 'Removed');
  }
  else if (what === 'askq') sendAsk(b.dataset.q);
  else if (what === 'clearchat') { chat = []; render(); }
  else if (what === 'briefnow') { toast('Writing your brief… up to a minute'); act(call('briefNow', KEY), 'Brief sent. It’s under More › Morning brief.'); }
  else if (what === 'portfolio') { tab = 'portfolio'; render(); window.scrollTo(0, 0); }
  else if (what === 'report') { tab = 'report'; window.scrollTo(0, 0); loadReport(reportRange); }
  else if (what === 'rrange') loadReport(b.dataset.range);
  else if (what === 'otype') { order.type = b.dataset.type; if (order.type !== 'market') { order.mode = 'shares'; order.amount = ''; } renderOrder(); }
  else if (what === 'cancelorder') {
    if (!confirm('Cancel this order?')) return;
    call('cancelOrder', KEY, b.dataset.id).then(() => { toast('Order canceled'); openStock(stock.symbol); }).catch((err) => toast(err.message || String(err)));
  }
  else if (what === 'watchadd') call('addWatch', KEY, b.dataset.sym).then(() => toast(b.dataset.sym + ' added to watchlist')).catch((err) => toast(err.message || String(err)));
  else if (what === 'alertfor') { alertPrefill = b.dataset.sym; tab = 'alerts'; render(); window.scrollTo(0, 0); }
  else if (what === 'testnotify') call('testNotification', KEY).then(() => toast('Test sent. Check your email and phone.')).catch((err) => toast(err.message || String(err)));
  else if (what === 'note') {
    const n = prompt('Journal note for this ' + b.dataset.sym + ' trade:', b.dataset.note || '');
    if (n === null) return;
    act(call('addTradeNote', KEY, Number(b.dataset.row), b.dataset.sym, n), 'Note saved');
  }
  else if (what === 'settings') { if (stock) closeStock(); tab = 'settings'; render(); window.scrollTo(0, 0); }
  else if (what === 'range') {
    const r = b.dataset.range;
    call('getHistory', KEY, r).then((h) => { hist = h; render(); }).catch((err) => toast(err.message || String(err)));
  }
  else if (what === 'seed') act(call('seedWatchlist', KEY), 'Added to your watchlist');
  else if (what === 'back') closeStock();
  else if (what === 'star') {
    call('toggleWatch', KEY, stock.symbol).then((on) => { stock.watch = on; renderDetail(); toast(on ? 'Added to watchlist' : 'Removed from watchlist'); }).catch((err) => toast(err.message || String(err)));
  }
  else if (what === 'srange') {
    const r = b.dataset.range;
    call('getStockChart', KEY, stock.symbol, r).then((c) => { stockRange = r; stock.chart = c; renderDetail(); }).catch((err) => toast(err.message || String(err)));
  }
  else if (what === 'trade') openOrder(b.dataset.side);
  else if (what === 'closeorder') { order = null; renderOrder(); }
  else if (what === 'omode') { order.mode = b.dataset.mode; order.amount = ''; renderOrder(); }
  else if (what === 'oreview') {
    if (order.type !== 'market' && !(Number(order.price) > 0)) { toast('Enter the ' + order.type + ' price.'); return; }
    if (order.mode !== 'all') {
      const a = Number(order.amount);
      if (!(a > 0)) { toast('Enter an amount first.'); return; }
      if (order.mode === 'dollars' && a < 1) { toast('Dollar orders start at $1.'); return; }
      if (order.mode === 'shares' && !stock.fractionable && !Number.isInteger(a)) { toast(stock.symbol + ' only trades in whole shares.'); return; }
    }
    order.step = 'review'; renderOrder();
  }
  else if (what === 'oedit') { order.step = 'edit'; renderOrder(); }
  else if (what === 'osubmit' && !busy) {
    busy = true; renderOrder();
    call('placeOrder', KEY, { symbol: stock.symbol, side: order.side, type: order.type, price: order.price, mode: order.mode, amount: order.amount, estPrice: stock.price })
      .then((r) => { busy = false; order = null; renderOrder(); toast(r.message); setTimeout(() => openStock(stock.symbol), 1500); })
      .catch((err) => { busy = false; renderOrder(); toast(err.message || String(err)); });
  }
  else if (busy) return;
  else if (what === 'switch') {
    const on = isOn(D.settings.enabled);
    if (on && !confirm('Turn bot trading off? The bot closes its own trades on its next run.')) return;
    act(call('setEnabled', KEY, !on), on ? 'Bot trading turned off' : 'Bot trading turned on').then(() => { if (tab === 'trading') loadTrading(true); });
  }
  else if (what === 'closeall') {
    if (!confirm('Sell every position in the account now, including stocks you bought yourself, and turn bot trading off?')) return;
    act(call('closeAllNow', KEY), 'Close-all sent. Bot trading is off.');
  }
  else if (what === 'usemodel') {
    if (!confirm('Switch the bot to ' + b.dataset.name + '? It uses the new rules on its next check. Open trades keep their stop and target.')) return;
    act(call('applyModel', KEY, b.dataset.id), 'Model: ' + b.dataset.name).then(() => { loadModels(true); loadTrading(true); });
  }
  else if (what === 'cryptotoggle') {
    const turnOn = !(trd && trd.cryptoOn);
    if (!turnOn && !confirm('Turn the crypto bot off? It sells the coins it holds on its next check (within 10 minutes).')) return;
    act(call('saveSettings', KEY, { crypto_bot: turnOn ? 'yes' : 'no' }), turnOn ? 'Crypto bot on' : 'Crypto bot off').then(() => loadTrading(true));
  }
  else if (what === 'strat') {
    const list = activeStrats(), id = b.dataset.id, i = list.indexOf(id);
    if (i >= 0) list.splice(i, 1); else list.push(id);
    act(call('setStrategies', KEY, list), 'Strategies saved');
  }
  else if (what === 'resetsettings') {
    if (!confirm('Reset every setting to its default?')) return;
    act(call('resetSettings', KEY), 'Settings reset to defaults');
  }
  else if (what === 'delholding') {
    if (!confirm('Stop tracking ' + b.dataset.sym + '? This doesn’t sell anything.')) return;
    act(call('deleteHolding', KEY, Number(b.dataset.row), b.dataset.sym), 'Removed');
  }
  else if (what === 'recheck') act(call('recheckIntel', KEY, Number(b.dataset.row), b.dataset.time), 'Research updated');
  else if (what === 'toggle') act(call('toggleRow', KEY, b.dataset.tab, Number(b.dataset.row), b.dataset.sym), 'Saved');
  else if (what === 'delete') {
    if (!confirm('Remove ' + b.dataset.sym + '?')) return;
    act(call('deleteRow', KEY, b.dataset.tab, Number(b.dataset.row), b.dataset.sym), 'Removed');
  }
});

document.addEventListener('submit', (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  if (e.target.id === 'askForm') { sendAsk(data.q); return; }
  if (e.target.id === 'tradeSearch') {
    const q = String(data.q || '').trim(); if (!q) return;
    call('searchSymbol', KEY, q).then((r) => openStock(r.symbol)).catch((err) => toast(err.message || String(err)));
    return;
  }
  if (e.target.id === 'searchForm') {
    const q = String(data.q || '').trim(); if (!q) return;
    call('searchSymbol', KEY, q).then((r) => openStock(r.symbol)).catch((err) => toast(err.message || String(err)));
    return;
  }
  if (busy) return;
  if (e.target.id === 'ipoForm') { act(call('addIpoWatch', KEY, data.name, data.found), data.name + ' added to IPO Watch'); return; }
  if (e.target.id === 'compareForm') { act(call('addCompare', KEY, data.symbol, data.found), String(data.symbol).toUpperCase() + ' added to Compare'); return; }
  if (e.target.id === 'holdingForm') { act(call('addHolding', KEY, data), data.symbol.toUpperCase() + ' added'); return; }
  if (e.target.id === 'settingsForm') { act(call('saveSettings', KEY, data), 'Settings saved'); return; }
  if (e.target.id === 'intelForm') { lastEvent = data.event || ''; act(call('addIntel', KEY, data.event, data.note), 'Saved and researched'); }
  if (e.target.id === 'alertForm') act(call('addAlert', KEY, data), 'Alert added');
  if (e.target.id === 'autoForm') act(call('addAutoInvest', KEY, data), 'Recurring buy added');
});

load();
</script>
</body>
</html>
