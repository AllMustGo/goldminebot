"""
GOLDMINEBOT: Coinbase sync (view-only)
Reads your Coinbase balances and prices and sends them to the Google Sheet (Holdings tab),
so they show in the app next to Alpaca and Robinhood. It never trades or moves anything.

GitHub secrets needed:
  COINBASE_KEY_NAME     organizations/.../apiKeys/...   (from Coinbase, ECDSA key)
  COINBASE_PRIVATE_KEY  -----BEGIN EC PRIVATE KEY----- ... -----END EC PRIVATE KEY-----
  SHEET_WEBHOOK_URL, SHEET_TOKEN  (same ones the bot uses)
"""
import os
import sys
import time
import secrets
from datetime import datetime
from zoneinfo import ZoneInfo

import base64

import jwt
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519

HOST = "api.coinbase.com"
ET = ZoneInfo("America/New_York")
KEY_NAME = (os.environ.get("COINBASE_KEY_NAME") or "").strip()
KEY_SECRET = (os.environ.get("COINBASE_PRIVATE_KEY") or "").strip().strip('"').strip("'").replace("\\n", "\n").strip()
SHEET_URL = (os.environ.get("SHEET_WEBHOOK_URL") or "").strip()
SHEET_TOKEN = (os.environ.get("SHEET_TOKEN") or "").strip()
STABLE = {"USD", "USDC", "USDT", "DAI", "PYUSD"}


def load_key():
    """Accepts an ECDSA key (PEM block) or an Ed25519 key (base64 string), as Coinbase gives them."""
    if "BEGIN" in KEY_SECRET:
        key = serialization.load_pem_private_key(KEY_SECRET.encode(), password=None)
    else:
        raw = base64.b64decode("".join(KEY_SECRET.split()))
        if len(raw) in (32, 64):
            key = ed25519.Ed25519PrivateKey.from_private_bytes(raw[:32])
        else:
            key = serialization.load_der_private_key(raw, password=None)
    if isinstance(key, ec.EllipticCurvePrivateKey):
        return key, "ES256"
    if isinstance(key, ed25519.Ed25519PrivateKey):
        return key, "EdDSA"
    raise RuntimeError("Unsupported key type. Create the key with ECDSA or Ed25519.")


def describe_secrets():
    """Explains what's wrong with the secrets without printing them."""
    name, sec = KEY_NAME, KEY_SECRET
    print("Key name: ", "MISSING" if not name else
          f"present, {len(name)} characters, " + ("starts with organizations/" if name.startswith("organizations/") else "an ID (no organizations/ prefix)"))
    if not sec:
        print("Private key: MISSING (check the secret is named exactly COINBASE_PRIVATE_KEY)")
    else:
        kind = "PEM block (ECDSA)" if "BEGIN" in sec else "single-line text (looks like Ed25519 / base64)"
        print(f"Private key: present, {len(sec)} characters, {kind}")


def build_jwt(method, path):
    key, alg = load_key()
    now = int(time.time())
    payload = {"sub": KEY_NAME, "iss": "cdp", "nbf": now, "exp": now + 120, "uri": f"{method} {HOST}{path}"}
    return jwt.encode(payload, key, algorithm=alg, headers={"kid": KEY_NAME, "nonce": secrets.token_hex()})


def coinbase(path, params=None):
    token = build_jwt("GET", path)  # the signed path excludes the query string
    r = requests.get(f"https://{HOST}{path}", params=params, headers={"Authorization": f"Bearer {token}"}, timeout=20)
    if r.status_code == 401:
        raise RuntimeError("Coinbase rejected the key (401). Check COINBASE_KEY_NAME and COINBASE_PRIVATE_KEY, "
                           "and that the key has the View permission.")
    if r.status_code >= 400:
        raise RuntimeError(f"Coinbase {path} failed ({r.status_code}): {r.text[:200]}")
    return r.json()


def price(currency):
    """Public market price in USD and 24h change; None if Coinbase has no USD market for it."""
    r = requests.get(f"https://{HOST}/api/v3/brokerage/market/products/{currency}-USD", timeout=20)
    if r.status_code >= 400:
        return None
    d = r.json()
    try:
        return float(d.get("price") or 0), float(d.get("price_percentage_change_24h") or 0)
    except (TypeError, ValueError):
        return None


def send(kind, **data):
    print(kind, {k: v for k, v in data.items() if k != "items"})
    if not SHEET_URL:
        return
    try:
        requests.post(SHEET_URL, json={"token": SHEET_TOKEN, "kind": kind,
                                       "time": datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S"), **data}, timeout=30)
    except Exception as e:
        print("Sheet update failed:", e)


def main():
    describe_secrets()
    if not KEY_NAME or not KEY_SECRET:
        sys.exit("Add both GitHub secrets, named exactly COINBASE_KEY_NAME and COINBASE_PRIVATE_KEY.")
    try:
        load_key()
    except Exception as e:
        sys.exit(f"The private key couldn't be read ({type(e).__name__}). Re-copy it from Coinbase: the whole key, nothing extra.")
    balances, cursor = {}, None
    for _ in range(10):
        params = {"limit": 250}
        if cursor:
            params["cursor"] = cursor
        d = coinbase("/api/v3/brokerage/accounts", params)
        for a in d.get("accounts", []):
            cur = a.get("currency", "")
            qty = float((a.get("available_balance") or {}).get("value") or 0) + float((a.get("hold") or {}).get("value") or 0)
            if qty > 0:
                balances[cur] = balances.get(cur, 0) + qty
        if not d.get("has_next"):
            break
        cursor = d.get("cursor")

    items = []
    for cur, qty in sorted(balances.items()):
        if cur in STABLE:
            px, chg = 1.0, 0.0
        else:
            p = price(cur)
            if not p:
                print(f"No USD price for {cur}; skipped value.")
                px, chg = 0.0, 0.0
            else:
                px, chg = p
        value = qty * px
        if px and value < 0.01:
            continue  # dust
        items.append({"symbol": cur, "qty": round(qty, 8), "price": px, "value": round(value, 2), "change24h": round(chg, 2)})
        print(f"  {cur}: {qty:g} ≈ ${value:,.2f} ({chg:+.2f}% 24h)")

    total = sum(i["value"] for i in items)
    print(f"Coinbase total ≈ ${total:,.2f} across {len(items)} assets")
    send("HOLDINGS", source="Coinbase", items=items)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e)
        send("COINBASE_ERROR", message=str(e)[:400])
        sys.exit(1)
