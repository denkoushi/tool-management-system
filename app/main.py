from __future__ import annotations

from . import create_app, socketio
from .background import start_scan_thread
from .config import HOST, PORT
from .db import ensure_tables


def run():
    app = create_app()
    ensure_tables()
    start_scan_thread(sock=socketio)

    print("🚀 Flask 工具管理システムを開始します...")
    print("📡 NFCスキャン監視スレッド開始")
    print(f"🌐 http://{HOST}:{PORT} でアクセス可能")
    print("💡 タイムアウトエラーは正常動作（タグ待機中）なので無視してください")

    socketio.run(app, host=HOST, port=PORT, debug=False)


if __name__ == "__main__":
    run()

