# 🚀 Raspberry Pi 完全自動起動設定 - 実践成功手順

**2025年8月24日に実際に成功した詳細手順の完全記録**

## 📌 重要な実環境情報

| 項目 | 実際の値 |
|------|---------|
| プロジェクトフォルダ | `/home/denkon5/pgraf/` |
| PostgreSQLコンテナ名 | `pg` |
| Pythonファイル | `app_flask.py` (要修正) |
| ポート番号 | 8501 |
| 動作確認OS | Raspberry Pi OS (Bookworm) |
| ユーザー名 | denkon5 |

## ✅ 実現できたこと

- **電源ON → 30秒で全自動起動**
- PostgreSQL自動起動
- 工具管理システム自動起動
- ブラウザ全画面自動起動
- NFCタグ読み取り可能
- **工場作業者は電源を入れるだけ**

## 📝 詳細設定手順

### Step 1: 作業ディレクトリ移動

```bash
cd ~/pgraf
pwd
# 確認: /home/denkon5/pgraf
```

### Step 2: app_flask.py修正（必須）

```bash
nano app_flask.py
```

最終行を修正：

**変更前:**
```python
socketio.run(app, host='0.0.0.0', port=8501, debug=False)
```

**変更後:**（`allow_unsafe_werkzeug=True` を追加）
```python
socketio.run(app, host='0.0.0.0', port=8501, debug=False, allow_unsafe_werkzeug=True)
```

> ⚠️ **注意**: インデントを上の行と同じにする（スペースの数を合わせる）

### Step 3: 自動起動スクリプト作成

```bash
nano setup_auto_start.sh
```

以下の内容を貼り付け：

```bash
#!/bin/bash
set -e

echo "🚀 工具管理システム自動起動設定を開始します..."

USER_NAME=$(whoami)
PROJECT_DIR=$(pwd)

echo "ユーザー: $USER_NAME"
echo "プロジェクトディレクトリ: $PROJECT_DIR"

# systemdサービスファイル作成
echo "📝 1. systemdサービス設定..."

sudo tee /etc/systemd/system/tool-management.service > /dev/null <<EOF
[Unit]
Description=Tool Management System
After=network.target docker.service
Requires=docker.service
StartLimitIntervalSec=0

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$PROJECT_DIR/venv/bin/python app_flask.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "✅ サービス設定完了"
```

保存して実行権限を付与：

```bash
chmod +x setup_auto_start.sh
./setup_auto_start.sh
```

### Step 4: サービス有効化

```bash
sudo systemctl enable tool-management.service
sudo systemctl start tool-management.service
sudo systemctl status tool-management.service
```

### Step 5: PostgreSQL自動起動設定

```bash
# PostgreSQLコンテナ確認
docker ps -a | grep pg

# 自動起動設定
docker update --restart unless-stopped pg
```

### Step 6: ブラウザ自動起動設定

```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/tool-browser.desktop
```

以下を貼り付け：

```ini
[Desktop Entry]
Type=Application
Name=Tool Management Browser
Comment=Auto start tool management browser in kiosk mode
Exec=chromium-browser --start-fullscreen --kiosk --incognito --disable-infobars --no-first-run --no-sandbox --disable-gpu http://127.0.0.1:8501
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
```

### Step 7: 再起動して確認

```bash
sudo reboot
```

## 🔍 トラブルシューティング

### エラー1: IndentationError

**症状:**
```
IndentationError: unindent does not match any outer indentation level
```

**解決方法:** 
app_flask.pyの最終行のインデントを修正

### エラー2: PostgreSQL接続エラー

**症状:**
```
psycopg2.OperationalError: connection to server at "127.0.0.1", port 5432 failed
```

**解決方法:**
```bash
docker start pg
docker update --restart unless-stopped pg
```

### エラー3: Werkzeugエラー

**症状:**
```
RuntimeError: The Werkzeug web server
```

**解決方法:** 
app_flask.py最終行に`allow_unsafe_werkzeug=True`を追加

## 📊 管理コマンド

### サービス状態確認
```bash
sudo systemctl status tool-management.service
```

### ログ確認
```bash
sudo journalctl -u tool-management.service -f
```

### サービス再起動
```bash
sudo systemctl restart tool-management.service
```

### 自動起動停止
```bash
sudo systemctl disable tool-management.service
rm ~/.config/autostart/tool-browser.desktop
```

## ✅ 動作確認チェックリスト

- [ ] 電源ON後、自動ログイン
- [ ] PostgreSQL自動起動（約10秒）
- [ ] 工具管理サービス自動起動（約20秒）
- [ ] ブラウザ自動起動（全画面）（約30秒）
- [ ] 工具管理画面表示
- [ ] NFCタグ読み取り可能

## 📝 重要な注意点

1. **pgrafフォルダ使用**: GitHubのREADMEでは`tool-management-system`だが、実際は`pgraf`
2. **PostgreSQLコンテナ名**: `postgres-tool`ではなく`pg`
3. **app_flask.py修正必須**: `allow_unsafe_werkzeug=True`追加
4. **インデント注意**: Pythonのインデントエラーに注意
5. **自動ログイン**: Raspberry Piは既に設定済み

## 🔄 標準環境への適用方法

標準的な`tool-management-system`環境で使用する場合は、以下を変更：

1. フォルダ名: `pgraf` → `tool-management-system`
2. PostgreSQLコンテナ名: `pg` → `postgres-tool`
3. 必要に応じてユーザー名を変更

---

**作成日**: 2025年8月24日  
**動作確認済み環境**: Raspberry Pi OS (Bookworm) + pgraf環境  
**成功事例**: denkon5環境で完全動作確認済み
