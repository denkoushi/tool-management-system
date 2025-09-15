# 🌐 オフライン対応設定ガイド（簡潔版）

本システムは、外部CDNに依存せずローカル配信したSocket.IOクライアントを使うことで、インターネット未接続環境でも貸出/返却スキャンを動作させます。

## 手順（必要最小限）
1) Socket.IOクライアントのローカル配置（実施済みの想定）
```bash
mkdir -p static/js
curl -o static/js/socket.io.js \
  https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js
```

2) HTMLの読み込み先をローカルに変更（実施済みの想定）
`templates/index.html` の `<head>` 内で以下を参照します:
```html
<script src="/static/js/socket.io.js"></script>
```

3) 再起動と確認
```bash
python -m app.main
# ブラウザ: http://127.0.0.1:8501
```

## 確認ポイント
- 画面が表示される
- 「スキャン開始」→ ユーザー → 工具の順でスキャンできる
- 貸出/返却が自動で判定・登録され、UIに反映される

## トラブルシューティング
- 404で `socket.io.js` が見つからない
  - `static/js/socket.io.js` の存在とパーミッションを確認
- WebSocket接続エラー
  - サーバのログを確認して再起動（`python app_flask.py`）
- 変更が反映されない
  - ブラウザでハードリロード（Ctrl/Cmd + Shift + R）

## 補足
- 年1回程度、`static/js/socket.io.js` を更新する運用を推奨
- 簡易ヘルスチェック例:
```bash
curl -s http://127.0.0.1:8501/static/js/socket.io.js | head -1
```
