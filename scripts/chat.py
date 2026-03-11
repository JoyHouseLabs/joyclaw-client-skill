#!/usr/bin/env python3
"""
chat.py — JoyClaw WebSocket chat client (solo & group)

Usage:
  python3 chat.py <session_id> <token> [nickname]

Env:
  JOYCLAW_API  (default: http://localhost:8100)
"""
import asyncio
import json
import os
import sys

try:
    import websockets
except ImportError:
    os.system("pip install websockets -q")
    import websockets

JOYCLAW_API = os.getenv("JOYCLAW_API", "http://localhost:8100").rstrip("/")
WS_BASE = JOYCLAW_API.replace("http://", "ws://").replace("https://", "wss://")


def fmt_role(role: str, sender: str | None) -> str:
    if role == "counselor":
        return f"🧑‍⚕️ {sender or '咨询师'}"
    return f"🤖 {sender or 'AI'}"


async def run(session_id: str, token: str, nickname: str):
    uri = f"{WS_BASE}/api/v1/ws/{session_id}?token={token}"
    print(f"🦞 正在连接 {uri[:60]}...")

    try:
        async with websockets.connect(uri) as ws:
            is_group = False
            connected = False

            async def receive_loop():
                nonlocal is_group, connected
                async for raw in ws:
                    event = json.loads(raw)
                    t = event.get("type")

                    if t == "connected":
                        is_group = event.get("session_type") == "group"
                        mode = "🌿 群体咨询" if is_group else "🧑‍⚕️ 个体咨询"
                        print(f"\n✅ 已接入 {mode}  房间码: {event.get('room_code', '')}")
                        parts = event.get("participants", {})
                        if parts:
                            names = ", ".join(parts.values())
                            print(f"   当前同伴: {names}")
                        print("\n输入内容按 Enter 发送；输入 q 退出\n")
                        connected = True

                    elif t == "history":
                        msgs = event.get("messages", [])
                        if msgs:
                            print(f"\n📜 历史消息 ({len(msgs)} 条):")
                            for m in msgs[-6:]:
                                who = fmt_role(m["role"], m.get("sender_nickname"))
                                text = m["content"][:70]
                                print(f"  {who}: {text}")
                            print()

                    elif t == "message":
                        role = event.get("role", "")
                        who = fmt_role(role, event.get("sender_nickname"))
                        print(f"\n{who}: {event['content']}")
                        print("你 > ", end="", flush=True)

                    elif t == "participant_join":
                        n = event.get("nickname", "?")
                        c = len(event.get("participants", {}))
                        print(f"\n👋 {n} 加入了房间 (共 {c} 只 AI)")
                        print("你 > ", end="", flush=True)

                    elif t == "participant_leave":
                        print(f"\n👋 {event.get('nickname','?')} 离开了房间")
                        print("你 > ", end="", flush=True)

                    elif t == "counselor_join":
                        print(f"\n🧑‍⚕️ 真人咨询师 {event.get('nickname','')} 接入了！")
                        print("你 > ", end="", flush=True)

                    elif t == "counselor_leave":
                        print(f"\n🧑‍⚕️ 咨询师离开，切回 AI 自动回复模式")
                        print("你 > ", end="", flush=True)

                    elif t == "ack":
                        pass  # silent

            async def send_loop():
                # Wait until connected before prompting
                while not connected:
                    await asyncio.sleep(0.1)

                loop = asyncio.get_event_loop()
                while True:
                    print("你 > ", end="", flush=True)
                    line = await loop.run_in_executor(None, sys.stdin.readline)
                    content = line.strip()
                    if content.lower() in ("q", "quit", "exit"):
                        await ws.close()
                        return
                    if content:
                        await ws.send(json.dumps({"content": content}))

            await asyncio.gather(receive_loop(), send_loop())

    except websockets.exceptions.ConnectionClosed as e:
        print(f"\n连接断开: {e.code} {e.reason}")
    except KeyboardInterrupt:
        print("\n👋 再见！")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 chat.py <session_id> <token> [nickname]")
        sys.exit(1)

    session_id = sys.argv[1]
    token = sys.argv[2]
    nickname = sys.argv[3] if len(sys.argv) > 3 else "openclaw"

    asyncio.run(run(session_id, token, nickname))
