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

## ダッシュボード（将来拡張）
目的: 運用状況を一目で把握し、異常の早期発見と現場改善に役立てる。

- 可視化対象（例）
  - 貸出中点数/未返却率（しきい値超え件数）
  - 端末ステータス（stationごとの最終スキャン時刻/心拍）
  - スキャン件数の推移（5分/時/日）
  - 利用上位の工具/ユーザー（過去30日）
  - 最新アラート（通信断/DB未達/スキャンエラー）

- データソース
  - `loans`（未返却の把握、返却時間差の算出）
  - `scan_events`（端末心拍、スキャン量の可視化、稼働率推定）

- 代表クエリ（例）
  - 貸出中点数: `SELECT COUNT(*) FROM loans WHERE returned_at IS NULL;`
  - 端末心拍: `SELECT station_id, MAX(ts) AS last_seen FROM scan_events GROUP BY station_id;`
  - 5分間のスキャン件数: `SELECT date_trunc('minute', ts) AS m, COUNT(*) FROM scan_events WHERE ts > now() - interval '1 hour' GROUP BY m ORDER BY m;`
  - 上位工具: `SELECT COALESCE(t.name, l.tool_uid) tool, COUNT(*) c FROM loans l LEFT JOIN tools t ON t.uid=l.tool_uid GROUP BY tool ORDER BY c DESC LIMIT 10;`

- 実装アプローチ
  - API: `/api/metrics`（JSONで上記指標を返す）
  - UI: 既存画面に「ダッシュボード」タブを追加（カード＋簡易チャート）
  - 集計: 初期は生SQLでOK。必要に応じてビュー/マテビューで最適化
  - 端末別可視化: `scan_events.station_id` を軸にテーブル/カード表示

- アラート（段階導入）
  - 心拍閾値（例: 最終スキャン>5分）で「要確認」表示
  - 未返却しきい値（例: 24h超）で強調表示
  - 将来: Slack/Webhook連携を追加

## NFCリーダー（RC‑S300/S1, Sony PaSoRi 4.0）
- 接続方式: PC/SC（`pcscd` + `pyscard`）で動作確認済み
- 取得方法: `FF CA 00 00 00` によりUID/IDmを取得する実装（`read_one_uid()`）
- 運用メモ:
  - 旧機種に比べPython向けライブラリの情報は少ないが、PC/SC経由で安定運用可能
  - 公式SDKの存在は認識。現状はPC/SC標準での実装を採用（移植性/保守性優先）
  - 認識不良時は `pcsc_scan` でReader/タグの反応を確認し、`pcscd` の再起動を実施
  - 端末差がある場合は `GET DATA` 取得の可否/戻り値差異をフィールドノートに記録

参考ドキュメント: `SETUP.md`（RC‑S300/S1の設定/確認手順）、`docs/RASPBERRY_PI_AUTO_START_SUCCESS.md`（実機での成功手順/注意点）
