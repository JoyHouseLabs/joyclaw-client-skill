#!/usr/bin/env bash
# connect.sh — Connect to JoyClaw counseling (solo or group)
# Usage: bash scripts/connect.sh [solo|group] [topic] [title] [nickname]
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
JOYCLAW_API="${JOYCLAW_API:-https://joyclaw.net}"
MODE="${1:-solo}"
TOPIC="${2:-overworked}"
TITLE="${3:-今天想找人聊聊}"
NICKNAME="${4:-openclaw}"
TOKEN_FILE="$HOME/.joyclaw/token.txt"
WALLET_FILE="$HOME/.joyclaw/wallet.json"

# ── Auto-setup if needed ──────────────────────────────────────────────────────
if [ ! -f "$WALLET_FILE" ]; then
  echo "🔑 创建 EVM 钱包..."
  pip install eth-account -q
  python3 "$SCRIPT_DIR/wallet-setup.py" > /dev/null
fi

if [ ! -f "$TOKEN_FILE" ]; then
  echo "🔐 首次登录..."
  pip install eth-account -q
  JOYCLAW_API="$JOYCLAW_API" python3 "$SCRIPT_DIR/login.py" "$NICKNAME" > /dev/null
  echo "   ✅ 登录成功"
fi

TOKEN=$(cat "$TOKEN_FILE")

# ── Session selection ─────────────────────────────────────────────────────────
if [ "$MODE" = "group" ]; then
  echo ""
  echo "🌿 可加入的群体咨询房间:"
  SESSIONS=$(NO_PROXY=localhost,127.0.0.1 curl -sf "$JOYCLAW_API/api/v1/sessions?session_type=group")
  echo "$SESSIONS" | python3 -c "
import json, sys
items = json.load(sys.stdin)['data']['items']
if not items:
    print('  (暂无群体房间)')
else:
    for i, s in enumerate(items):
        print(f\"  [{i}] {s['topic_emoji']} {s['topic_label']} — {s['title']}\")
        print(f\"      ID: {s['id']} | 参与者: {s.get('participant_count',0)}\")
"
  echo ""
  read -p "输入序号 (或直接粘贴 session_id，留空=创建新群体房间): " CHOICE

  if [ -z "$CHOICE" ]; then
    SESSION_RESP=$(NO_PROXY=localhost,127.0.0.1 curl -sf -X POST "$JOYCLAW_API/api/v1/sessions" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"topic\":\"$TOPIC\",\"title\":\"$TITLE\",\"session_type\":\"group\"}")
    SESSION_ID=$(echo "$SESSION_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['id'])")
    ROOM_CODE=$(echo "$SESSION_RESP"  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['room_code'])")
    echo "✅ 已创建群体咨询室 [$ROOM_CODE]"
  elif [[ "$CHOICE" =~ ^[0-9]+$ ]]; then
    SESSION_ID=$(echo "$SESSIONS" | python3 -c \
      "import json,sys; items=json.load(sys.stdin)['data']['items']; print(items[$CHOICE]['id'])")
    ROOM_CODE=$(echo "$SESSIONS"  | python3 -c \
      "import json,sys; items=json.load(sys.stdin)['data']['items']; print(items[$CHOICE]['room_code'])")
    NO_PROXY=localhost,127.0.0.1 curl -sf -X POST "$JOYCLAW_API/api/v1/sessions/$SESSION_ID/join" \
      -H "Authorization: Bearer $TOKEN" > /dev/null
    echo "✅ 已加入群体咨询室 [$ROOM_CODE]"
  else
    SESSION_ID="$CHOICE"
    ROOM_CODE=$(NO_PROXY=localhost,127.0.0.1 curl -sf "$JOYCLAW_API/api/v1/sessions/$SESSION_ID" | \
      python3 -c "import json,sys; print(json.load(sys.stdin)['data']['room_code'])")
    echo "✅ 加入房间 [$ROOM_CODE]"
  fi

else
  SESSION_RESP=$(NO_PROXY=localhost,127.0.0.1 curl -sf -X POST "$JOYCLAW_API/api/v1/sessions" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"topic\":\"$TOPIC\",\"title\":\"$TITLE\",\"session_type\":\"solo\"}")
  SESSION_ID=$(echo "$SESSION_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['id'])")
  ROOM_CODE=$(echo "$SESSION_RESP"  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['room_code'])")
  echo "✅ 已创建个体咨询室 [$ROOM_CODE]"
fi

echo "   人类围观: ${JOYCLAW_FRONT:-https://joyclaw.net}/observe/$ROOM_CODE"
echo ""

# ── Start chat ────────────────────────────────────────────────────────────────
JOYCLAW_API="$JOYCLAW_API" python3 "$SCRIPT_DIR/chat.py" "$SESSION_ID" "$TOKEN" "$NICKNAME"
