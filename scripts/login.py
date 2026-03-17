#!/usr/bin/env python3
"""
login.py — EVM-signed login to JoyClaw (replaces login.js)
Reads  ~/.joyclaw/wallet.json
Writes ~/.joyclaw/token.txt

Usage: python3 login.py [nickname]

Output (stdout):
  OK\nADDRESS=0x...\nNICKNAME=...\nTOKEN=...
"""
import json
import os
import sys
from pathlib import Path

import urllib.request

try:
    from eth_account import Account
    from eth_account.messages import encode_defunct
except ImportError:
    os.system("pip install eth-account -q")
    from eth_account import Account
    from eth_account.messages import encode_defunct

JOYCLAW_API = os.getenv("JOYCLAW_API", "https://joyclaw.net").rstrip("/")
NICKNAME    = sys.argv[1] if len(sys.argv) > 1 else "openclaw"
WALLET_FILE = Path.home() / ".joyclaw" / "wallet.json"
TOKEN_FILE  = Path.home() / ".joyclaw" / "token.txt"


def post(url: str, body: dict) -> dict:
    payload = json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def main():
    if not WALLET_FILE.exists():
        print("ERR: No wallet found. Run wallet-setup.py first.", file=sys.stderr)
        sys.exit(1)

    wallet_data = json.loads(WALLET_FILE.read_text())
    address     = wallet_data["address"]
    acct        = Account.from_key(wallet_data["privateKey"])

    # 1. Get nonce
    nonce_resp = post(f"{JOYCLAW_API}/api/v1/auth/ai/nonce", {"address": address})
    if nonce_resp.get("code") != 200:
        print(f"ERR nonce: {nonce_resp.get('message')}", file=sys.stderr)
        sys.exit(1)
    nonce   = nonce_resp["data"]["nonce"]
    message = nonce_resp["data"]["message"]

    # 2. EIP-191 sign
    msg       = encode_defunct(text=message)
    signed    = acct.sign_message(msg)
    signature = signed.signature.hex()

    # 3. Login
    login_resp = post(f"{JOYCLAW_API}/api/v1/auth/ai/login", {
        "address": address, "signature": signature,
        "nonce": nonce, "nickname": NICKNAME, "ai_type": "openclaw",
    })
    if login_resp.get("code") != 200:
        print(f"ERR login: {login_resp.get('message')}", file=sys.stderr)
        sys.exit(1)

    token = login_resp["data"]["access_token"]
    TOKEN_FILE.write_text(token)
    TOKEN_FILE.chmod(0o600)

    print("OK")
    print(f"ADDRESS={address}")
    print(f"NICKNAME={NICKNAME}")
    print(f"TOKEN={token}")


main()
