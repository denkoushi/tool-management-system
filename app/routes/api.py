from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..background import scan_state
from ..config import SCAN_POLL_TIMEOUT_SEC
from ..db import (
    add_tool_name,
    delete_tool_name,
    fetch_open_loans,
    fetch_recent_history,
    get_conn,
)
from ..nfc import read_one_uid


api_bp = Blueprint("api", __name__)


@api_bp.route("/api/start_scan", methods=["POST"])
def start_scan():
    scan_state["active"] = True
    scan_state["user_uid"] = ""
    scan_state["tool_uid"] = ""
    scan_state["message"] = "📡 スキャン待機中... ユーザータグをかざしてください"
    print("🟢 自動スキャン開始")
    return jsonify({"status": "started", "message": scan_state["message"]})


@api_bp.route("/api/stop_scan", methods=["POST"])
def stop_scan():
    scan_state["active"] = False
    scan_state["message"] = "⏹️ スキャン停止"
    print("🔴 自動スキャン停止")
    return jsonify({"status": "stopped", "message": scan_state["message"]})


@api_bp.route("/api/reset", methods=["POST"])
def reset_state():
    scan_state["user_uid"] = ""
    scan_state["tool_uid"] = ""
    scan_state["message"] = "🔄 リセット完了"
    print("🧹 状態リセット")
    return jsonify({"status": "reset"})


@api_bp.route("/api/loans")
def get_loans():
    conn = get_conn()
    try:
        open_loans = fetch_open_loans(conn)
        history = fetch_recent_history(conn)
        return jsonify(
            {
                "open_loans": [
                    {
                        "tool": r[0],
                        "borrower": r[1],
                        "loaned_at": r[2].isoformat(),
                    }
                    for r in open_loans
                ],
                "history": [
                    {
                        "action": r[0],
                        "tool": r[1],
                        "borrower": r[2],
                        "loaned_at": r[3].isoformat(),
                        "returned_at": r[4].isoformat() if r[4] else None,
                    }
                    for r in history
                ],
            }
        )
    finally:
        conn.close()


@api_bp.route("/api/scan_tag", methods=["POST"])
def scan_tag():
    print("📡 手動スキャン実行中...")
    uid = read_one_uid(timeout=int(SCAN_POLL_TIMEOUT_SEC) or 5)
    if uid:
        print(f"✅ 手動スキャン成功: {uid}")
        return jsonify({"uid": uid, "status": "success"})
    else:
        print("❌ 手動スキャン タイムアウト")
        return jsonify({"uid": None, "status": "timeout"})


@api_bp.route("/api/register_user", methods=["POST"])
def register_user():
    data = request.json or {}
    uid = data.get("uid")
    name = data.get("name")

    if not uid or not name:
        return jsonify({"error": "UID と 氏名 は必須です"}), 400

    conn = get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users(uid, full_name)
                VALUES(%s,%s)
                ON CONFLICT(uid) DO UPDATE SET full_name=EXCLUDED.full_name
                """,
                (uid, name.strip()),
            )
        print(f"👤 ユーザー登録: {name} ({uid})")
        return jsonify({"status": "success", "message": "ユーザーを登録/更新しました"})
    except Exception as e:  # noqa: BLE001
        print(f"❌ ユーザー登録エラー: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@api_bp.route("/api/register_tool", methods=["POST"])
def register_tool():
    data = request.json or {}
    uid = data.get("uid")
    name = data.get("name")

    if not uid or not name:
        return jsonify({"error": "UID と 工具名 は必須です"}), 400

    conn = get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tools(uid, name)
                VALUES(%s,%s)
                ON CONFLICT(uid) DO UPDATE SET name=EXCLUDED.name
                """,
                (uid, name),
            )
        print(f"🛠️ 工具登録: {name} ({uid})")
        return jsonify({"status": "success", "message": "工具を登録/更新しました"})
    except Exception as e:  # noqa: BLE001
        print(f"❌ 工具登録エラー: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@api_bp.route("/api/tool_names")
def get_tool_names():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM tool_master ORDER BY name ASC")
            names = [r[0] for r in cur.fetchall()]
        return jsonify({"names": names})
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@api_bp.route("/api/add_tool_name", methods=["POST"])
def add_tool_name_api():
    data = request.json or {}
    name = data.get("name")

    if not name:
        return jsonify({"error": "工具名を入力してください"}), 400

    conn = get_conn()
    try:
        add_tool_name(conn, name.strip())
        print(f"📚 工具名追加: {name}")
        return jsonify({"status": "success", "message": "追加しました"})
    except Exception as e:  # noqa: BLE001
        print(f"❌ 工具名追加エラー: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@api_bp.route("/api/delete_tool_name", methods=["POST"])
def delete_tool_name_api():
    data = request.json or {}
    name = data.get("name")

    if not name:
        return jsonify({"error": "工具名を指定してください"}), 400

    conn = get_conn()
    try:
        delete_tool_name(conn, name)
        print(f"🗑️ 工具名削除: {name}")
        return jsonify({"status": "success", "message": "削除しました"})
    except Exception as e:  # noqa: BLE001
        print(f"❌ 工具名削除エラー: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@api_bp.route("/api/check_tag", methods=["POST"])
def check_tag():
    print("📡 タグ情報確認スキャン実行中...")
    uid = read_one_uid(timeout=int(SCAN_POLL_TIMEOUT_SEC) or 5)
    if uid:
        print(f"✅ タグ情報確認成功: {uid}")
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT full_name FROM users WHERE uid=%s", (uid,))
                user_result = cur.fetchone()
                cur.execute("SELECT name FROM tools WHERE uid=%s", (uid,))
                tool_result = cur.fetchone()

            result = {"uid": uid, "status": "success"}
            if user_result:
                result["type"] = "user"
                result["name"] = user_result[0]
                result["message"] = f"👤 ユーザー: {user_result[0]}"
            elif tool_result:
                result["type"] = "tool"
                result["name"] = tool_result[0]
                result["message"] = f"🛠️ 工具: {tool_result[0]}"
            else:
                result["type"] = "unregistered"
                result["name"] = ""
                result["message"] = "❓ 未登録のタグです"

            return jsonify(result)
        finally:
            conn.close()
    else:
        print("❌ タグ情報確認 タイムアウト")
        return jsonify({"uid": None, "status": "timeout"})
