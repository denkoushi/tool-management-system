# 🧰 工具持出返却管理システム

Raspberry Pi + NFC + Flask + PostgreSQL で、工具の貸出/返却をリアルタイムに記録・可視化するシステムです。工場のローカルLANやオフライン環境でも動作し、将来的に複数端末（≈20台）でも1つのデータベースで集中管理する運用を想定しています。

## できること
- 🔄 NFCタグによる貸出/返却の自動判定（ユーザー → 工具の順でスキャン）
- 👤 ユーザー・🛠 工具のタグ登録、📚 工具名マスタ管理
- 🌐 リアルタイムWeb UI（Socket.IO）、📊 貸出中一覧と履歴の表示
- 🌐 オフラインでも動作（Socket.IOクライアントをローカル配備）

## 構成（概要）
- `app_flask.py`: Flask + Flask‑SocketIO サーバ（PC/SC経由でNFC UIDを取得、PostgreSQLへ記録）
- `templates/index.html`: 操作用Web UI（レスポンシブ）
- `static/js/socket.io.js`: ローカル配備のSocket.IOクライアント
- データベース: PostgreSQL（Docker推奨）

アーキテクチャと処理ロジックの詳細は `ARCHITECTURE.md` を参照してください。

## クイックスタート
```bash
# 依存: pcscd（PC/SC）、Docker（PostgreSQL）、Python3

# リポジトリ取得
git clone https://github.com/denkoushi/tool-management-system.git
cd tool-management-system

# Python仮想環境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# PostgreSQL をDockerで起動（初回のみ）
docker run --name postgres-tool \
  -e POSTGRES_DB=sensordb \
  -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=app \
  -p 5432:5432 -d postgres:16

# アプリ起動
python app_flask.py
```

アクセス:
- ローカル: http://127.0.0.1:8501
- 同一LAN: http://[RaspberryPiのIP]:8501

## 使い方（現場オペレーション）
1. 画面の「スキャン開始」を押す
2. ユーザータグをスキャン → 次に工具タグをスキャン
3. 貸出中なら返却、未貸出なら貸出として自動登録（結果が画面に反映）

## データモデル（要約）
- `users(uid, full_name)`: ユーザー
- `tool_master(id, name)`: 工具名マスタ
- `tools(uid, name)`: 工具（タグUIDと工具名の対応）
- `loans(tool_uid, borrower_uid, loaned_at, returned_at, return_user_uid)`: 貸出/返却履歴
- `scan_events(ts, station_id, tag_uid, role_hint)`: スキャンログ

## オフライン/自動起動
- オフライン対応: `OFFLINE_SETUP.md`（Socket.IOをローカルから配信）
- 自動起動（キオスク運用）: `AUTO_START.md`（systemd + Chromium）

## 複数端末・単一DB運用の方針（将来拡張）
- 複数のRaspberry Piが同一PostgreSQLに接続して集中管理（LAN内）
- 端末識別には `scan_events.station_id` を利用（UI/集計で端末別可視化）
- 競合防止のため「同一工具は同時に1件のみ貸出中」のDB制約の導入を推奨
- GPIO（LED/ブザー）連動やダッシュボード拡張も可能

詳細の設計・ロジック・拡張案は `ARCHITECTURE.md` を参照してください。

## ドキュメント
- 初期セットアップ: `SETUP.md`
- オフライン対応: `OFFLINE_SETUP.md`
- 自動起動（systemd/キオスク）: `AUTO_START.md`
- アーキテクチャ/ロジック: `ARCHITECTURE.md`
- 参考（実機ログ・フィールドノート）: `docs/RASPBERRY_PI_AUTO_START_SUCCESS.md`

## 動作環境
- Raspberry Pi OS（Pi 4で確認） / Python 3
- Flask + Flask‑SocketIO / PostgreSQL（Docker）
- NFCリーダー（PC/SC対応）

## ライセンス
MIT License

