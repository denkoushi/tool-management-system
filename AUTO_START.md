# 🤖 自動起動（キオスク）設定ガイド（簡潔版）

電源ON → 自動ログイン → サービス起動 → ブラウザ全画面 までを自動化します。

## いちばん簡単な方法（推奨）
```bash
cd ~/tool-management-system
chmod +x setup_auto_start.sh
./setup_auto_start.sh
sudo reboot
```

`setup_auto_start.sh` が以下を自動で行います:
- systemdサービス `tool-management.service` の作成/有効化
- デスクトップ自動ログイン
- Chromiumをキオスクモードで自動起動

## 手動で行いたい場合（概要）
1) systemd サービスを作成
```bash
sudo tee /etc/systemd/system/tool-management.service >/dev/null <<'EOF'
[Unit]
Description=Tool Management System
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/tool-management-system
Environment=PATH=/home/$USER/tool-management-system/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/home/$USER/tool-management-system/venv/bin/python app_flask.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now tool-management.service
```

2) ブラウザを自動起動（キオスク）
```bash
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/tool-management-browser.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Tool Management Browser
Exec=/home/$USER/tool-management-system/start_browser.sh
X-GNOME-Autostart-enabled=true
EOF

cat > ~/tool-management-system/start_browser.sh <<'EOF'
#!/bin/bash
for i in {1..60}; do
  if curl -s http://127.0.0.1:8501 >/dev/null 2>&1; then break; fi
  sleep 1
done
xset s off; xset -dpms; xset s noblank
chromium-browser --start-fullscreen --kiosk --incognito --no-first-run --disable-gpu http://127.0.0.1:8501
EOF
chmod +x ~/tool-management-system/start_browser.sh
```

## 運用メモ
- 状態確認: `sudo systemctl status tool-management.service`
- ログ確認: `sudo journalctl -u tool-management.service -f`
- 停止/再起動: `sudo systemctl stop|restart tool-management.service`

