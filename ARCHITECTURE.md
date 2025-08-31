# 🧩 アーキテクチャとロジック

本システムの目的・構成・処理ロジックを、初見でも把握しやすくまとめています。

## 目的
- 工具の貸出/返却を「誰が・何を・いつ」行ったかを、現場で素早く正確に残す
- NFCタグとRaspberry Pi端末で操作を簡素化し、工場のローカルLANやオフラインでも使える
- 将来的に複数端末（≈20台）で1つのDBを共有し、集中管理できるようにする

## 全体構成
- フロントエンド: `templates/index.html`（ブラウザ）
  - Socket.IOでサーバとリアルタイム通信
  - スキャン進行状況、貸出中一覧、履歴を表示
- アプリサーバ: `app_flask.py`（Flask + Flask‑SocketIO）
  - PC/SC（pyscard）でNFCリーダーからUID（IDm/UID）を取得
  - PostgreSQLへ貸出/返却・スキャンログを記録
- データベース: PostgreSQL
  - users/tools/loans/scan_events などのスキーマ

## スキャンと取引ロジック
1. UIで「スキャン開始」を押すと、サーバ側のスキャンスレッドが動作
2. タグ読取は「ユーザー → 工具」の順
3. 2つ揃うと、自動で貸出/返却を判定して登録（トグル方式）
4. 完了後は一定時間で新しい取引の待機状態にリセット

簡易状態遷移（擬似コード）:
```
state = { active: bool, user_uid: str, tool_uid: str }

while True:
  if not state.active: sleep()
  uid = read_one_uid()
  if not uid: continue

  if not state.user_uid:
      state.user_uid = uid  # ユーザー確定
      emit(scan_update)
  elif not state.tool_uid:
      state.tool_uid = uid  # 工具確定
      action = borrow_or_return(user_uid, tool_uid)
      emit(transaction_complete)
      reset_after_delay()
```

デバウンス: 同一UIDの連続読取は一定時間（デフォルト2秒）無視

貸出/返却判定:
- その工具の未返却レコードがあれば「返却」
- なければ新規に「貸出」を作成

## データベース（概要）
- `users(uid TEXT PRIMARY KEY, full_name TEXT)`
- `tool_master(id BIGSERIAL, name TEXT UNIQUE)`
- `tools(uid TEXT PRIMARY KEY, name TEXT REFERENCES tool_master(name))`
- `loans(id BIGSERIAL, tool_uid TEXT, borrower_uid TEXT, loaned_at TIMESTAMPTZ, returned_at TIMESTAMPTZ, return_user_uid TEXT)`
- `scan_events(id BIGSERIAL, ts TIMESTAMPTZ, station_id TEXT, tag_uid TEXT, role_hint TEXT)`

推奨（将来拡張）:
- 同一工具の同時貸出を防止する部分ユニーク制約
  - `CREATE UNIQUE INDEX ... ON loans(tool_uid) WHERE returned_at IS NULL;`
- 端末識別（station_id）の設定・可視化（ダッシュボード等）

## オフライン対応の考え方
- フロントのSocket.IOをローカル配信（CDN依存を排除）
- サーバ・DBともにローカルで完結
- 詳細手順は `OFFLINE_SETUP.md`

## 20台運用・単一DBの指針
- 各Piが同一PostgreSQLへ接続（LAN内）
- `scan_events.station_id` に端末IDを記録し、運用レポートや障害切り分けに活用
- DB側の一貫性（1工具1貸出の保証）を制約/トランザクションで担保
- ネットワーク断対策（キューイングや再試行）は段階的に導入可能

## 安全性/運用（要点）
- PC/SCの安定稼働（pcscd常時起動）
- systemd + ブラウザキオスクで電源ON即運用
- ログのローテーション/バックアップ、UPS等の電源対策

---
実装上の該当箇所は以下を参照:
- NFC読取: `app_flask.py:173` 付近
- 連続スキャン防止（デバウンス）: `app_flask.py:203-208`
- 貸出/返却の自動判定: `app_flask.py:232-239`
- UI更新（Socket.IO emit）: `app_flask.py:218-247`

