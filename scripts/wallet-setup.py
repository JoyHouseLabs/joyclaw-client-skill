#!/usr/bin/env python3
"""
wallet-setup.py — EVM wallet init for JoyClaw
Writes ~/.joyclaw/wallet.json if it doesn't exist.

Output (stdout):
  CREATED\nADDRESS=0x...   (first run)
  EXISTS\nADDRESS=0x...    (subsequent runs)
"""
import json
import os
import sys
from pathlib import Path

try:
    from eth_account import Account
except ImportError:
    os.system("pip install eth-account -q")
    from eth_account import Account

jc_dir = Path.home() / ".joyclaw"
jc_dir.mkdir(exist_ok=True)
wallet_file = jc_dir / "wallet.json"

if wallet_file.exists():
    data = json.loads(wallet_file.read_text())
    print("EXISTS")
    print(f"ADDRESS={data['address']}")
else:
    acct = Account.create()
    data = {"address": acct.address, "privateKey": acct.key.hex()}
    wallet_file.write_text(json.dumps(data, indent=2))
    wallet_file.chmod(0o600)
    print("CREATED")
    print(f"ADDRESS={acct.address}")
