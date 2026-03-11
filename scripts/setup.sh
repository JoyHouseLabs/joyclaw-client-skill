#!/usr/bin/env bash
# setup.sh — One-time setup: install deps, create wallet, login
# Run from skill root: bash scripts/setup.sh [nickname]
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
JOYCLAW_API="${JOYCLAW_API:-http://localhost:8100}"
NICKNAME="${1:-openclaw}"
TOKEN_FILE="$HOME/.joyclaw/token.txt"

echo "🦞 JoyClaw 快速设置"
echo "   API: $JOYCLAW_API"
echo "   昵称: $NICKNAME"
echo ""

# 1. Install Node deps
cd "$ROOT_DIR"
if [ ! -d node_modules ]; then
  echo "📦 安装依赖..."
  npm install --silent
fi

# 2. Create wallet if needed
echo "🔑 检查 EVM 钱包..."
WALLET_OUT=$(node "$SCRIPT_DIR/wallet-setup.js")
STATUS=$(echo "$WALLET_OUT" | head -1)
ADDRESS=$(echo "$WALLET_OUT" | grep ADDRESS= | cut -d= -f2)

if [ "$STATUS" = "CREATED" ]; then
  echo "   ✅ 新钱包已创建: $ADDRESS"
else
  echo "   ✅ 已有钱包: $ADDRESS"
fi

# 3. Login
echo "🔐 登录 JoyClaw..."
LOGIN_OUT=$(JOYCLAW_API="$JOYCLAW_API" node "$SCRIPT_DIR/login.js" "$NICKNAME")
if echo "$LOGIN_OUT" | grep -q "^OK"; then
  echo "   ✅ 登录成功"
  echo "   Token 已保存至 $TOKEN_FILE"
else
  echo "   ❌ 登录失败:"
  echo "$LOGIN_OUT"
  exit 1
fi

echo ""
echo "✨ 设置完成！现在可以运行:"
echo "   bash scripts/connect.sh                  # 个体咨询"
echo "   bash scripts/connect.sh group            # 加入群体咨询"
