from __future__ import annotations

import threading
import time

from flask_socketio import SocketIO

from . import socketio as socketio_ext
from .config import SCAN_DEBOUNCE_SEC, SCAN_POLL_TIMEOUT_SEC
from .db import (
    borrow_or_return,
    get_conn,
    insert_scan,
    name_of_tool,
    name_of_user,
)
from .nfc import read_one_uid


scan_state = {
    "active": False,
    "user_uid": "",
    "tool_uid": "",
    "last_scanned_uid": "",
    "last_scan_time": 0.0,
    "message": "",
}


def scan_monitor(sock: SocketIO | None = None):
    """Background NFC scan loop.

    Emits Socket.IO events to update UI.
    """
    sio = sock or socketio_ext
    global scan_state

    while True:
        if not scan_state["active"]:
            time.sleep(0.5)
            continue

        try:
            uid = read_one_uid(timeout=int(SCAN_POLL_TIMEOUT_SEC))
            if uid:
                # Debounce same UID for a short period
                now = time.time()
                if (
                    uid == scan_state["last_scanned_uid"]
                    and (now - scan_state["last_scan_time"]) < SCAN_DEBOUNCE_SEC
                ):
                    continue

                scan_state["last_scanned_uid"] = uid
                scan_state["last_scan_time"] = now

                conn = get_conn()
                try:
                    if not scan_state["user_uid"]:
                        scan_state["user_uid"] = uid
                        scan_state["message"] = (
                            f"👤 ユーザー読取: {name_of_user(conn, uid)} ({uid})"
                        )
                        insert_scan(conn, uid, "user")

                        sio.emit(
                            "scan_update",
                            {
                                "user_uid": scan_state["user_uid"],
                                "user_name": name_of_user(conn, uid),
                                "tool_uid": scan_state["tool_uid"],
                                "tool_name": "",
                                "message": scan_state["message"],
                            },
                        )

                    elif not scan_state["tool_uid"]:
                        scan_state["tool_uid"] = uid
                        scan_state["message"] = (
                            f"🛠️ 工具読取: {name_of_tool(conn, uid)} ({uid})"
                        )
                        insert_scan(conn, uid, "tool")

                        try:
                            action, info = borrow_or_return(
                                conn, scan_state["user_uid"], scan_state["tool_uid"]
                            )
                            if action == "borrow":
                                message = (
                                    f"✅ 貸出：{name_of_tool(conn, scan_state['tool_uid'])} → "
                                    f"{name_of_user(conn, scan_state['user_uid'])}"
                                )
                            else:
                                message = (
                                    f"✅ 返却：{name_of_tool(conn, scan_state['tool_uid'])} by "
                                    f"{name_of_user(conn, scan_state['user_uid'])}"
                                    f"（借用者: {name_of_user(conn, info.get('prev_user', ''))}）"
                                )

                            sio.emit(
                                "transaction_complete",
                                {
                                    "user_uid": scan_state["user_uid"],
                                    "user_name": name_of_user(conn, scan_state["user_uid"]),
                                    "tool_uid": scan_state["tool_uid"],
                                    "tool_name": name_of_tool(conn, scan_state["tool_uid"]),
                                    "message": message,
                                    "action": action,
                                },
                            )

                            print(f"✅ 処理完了: {message}")

                            def _reset():
                                time.sleep(3)
                                scan_state["user_uid"] = ""
                                scan_state["tool_uid"] = ""
                                scan_state["message"] = (
                                    "📡 スキャン待機中... ユーザータグをかざしてください"
                                )
                                sio.emit("state_reset", {"message": scan_state["message"]})
                                print("🔄 次の処理待ち")

                            threading.Thread(target=_reset, daemon=True).start()
                        except Exception as e:  # noqa: BLE001
                            error_msg = f"❌ エラー: {e}"
                            print(error_msg)
                            sio.emit("error", {"message": error_msg})
                finally:
                    conn.close()

        except Exception as e:  # noqa: BLE001
            if "Time-out" not in str(e) and "Command timeout" not in str(e):
                print(f"スキャンループエラー: {e}")
            time.sleep(1)

        time.sleep(0.1)


def start_scan_thread(sock: SocketIO | None = None) -> threading.Thread:
    t = threading.Thread(target=scan_monitor, kwargs={"sock": sock}, daemon=True)
    t.start()
    return t

