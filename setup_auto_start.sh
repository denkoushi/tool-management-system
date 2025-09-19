#!/bin/bash
# 工具管理システム - 自動起動設定スクリプト
# 工場現場での完全自動化用

set -e

echo "🚀 工具管理システム自動起動設定を開始します..."

# 現在のユーザーとパス
USER_NAME=$(whoami)
PROJECT_DIR=$(pwd)

echo "ユーザー: $USER_NAME"
echo "プロジェクトディレクトリ: $PROJECT_DIR"

# 1. systemdサービスファイル作成
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
ExecStart=$PROJECT_DIR/venv/bin/python -m app.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 2. デスクトップ自動ログイン設定
echo "📝 2. デスクトップ自動ログイン設定..."

sudo raspi-config nonint do_boot_behaviour B4  # デスクトップ自動ログイン

# 3. ブラウザ自動起動設定（キオスクモード）
echo "📝 3. ブラウザ自動起動設定..."

# .config/autostart ディレクトリ作成
mkdir -p /home/$USER_NAME/.config/autostart

# 自動起動用デスクトップファイル作成
cat > /home/$USER_NAME/.config/autostart/tool-management-browser.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Tool Management Browser
Comment=Auto start tool management system browser
Exec=/home/$USER_NAME/tool-management-system/start_browser.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

# 4. ブラウザ起動スクリプト作成
echo "📝 4. ブラウザ起動スクリプト作成..."

cat > $PROJECT_DIR/start_browser.sh <<'EOF'
#!/bin/bash
# ブラウザ自動起動スクリプト

# サービス起動まで待機
echo "工具管理システムの起動を待機中..."

# 最大60秒待機
for i in {1..60}; do
    if curl -s http://127.0.0.1:8501 > /dev/null 2>&1; then
        echo "✅ システム起動確認 - ブラウザを開始します"
        break
    fi
    echo "待機中... ($i/60)"
    sleep 1
done

# スクリーンセーバー無効化
xset s off
xset -dpms
xset s noblank

# フルスクリーンでブラウザ起動（キオスクモード）
chromium-browser \
    --start-fullscreen \
    --kiosk \
    --incognito \
    --disable-translate \
    --disable-infobars \
    --disable-suggestions-service \
    --disable-save-password-bubble \
    --disable-session-crashed-bubble \
    --disable-restore-session-state \
    --disable-new-tab-first-run \
    --no-first-run \
    --no-sandbox \
    --disable-3d-apis \
    --disable-accelerated-2d-canvas \
    --disable-gpu \
    http://127.0.0.1:8501
EOF

chmod +x $PROJECT_DIR/start_browser.sh

# 5. systemdサービス有効化
echo "📝 5. サービス有効化・起動..."

sudo systemctl daemon-reload
sudo systemctl enable tool-management.service
sudo systemctl start tool-management.service

# 6. Docker PostgreSQL自動起動設定（既存確認）
echo "📝 6. PostgreSQL自動起動確認..."

if docker ps -a | grep -q postgres-tool; then
    docker update --restart unless-stopped postgres-tool
    echo "✅ PostgreSQL自動起動設定完了"
else
    echo "⚠️  PostgreSQL コンテナが見つかりません。SETUP.mdの手順2を実行してください。"
fi

# 7. 画面設定（解像度・回転）
echo "📝 7. ディスプレイ設定..."

# config.txt バックアップ
sudo cp /boot/firmware/config.txt /boot/firmware/config.txt.backup

# 画面回転（必要に応じて）
# sudo bash -c 'echo "display_rotate=1" >> /boot/firmware/config.txt'  # 90度回転
# sudo bash -c 'echo "display_rotate=2" >> /boot/firmware/config.txt'  # 180度回転

echo ""
echo "🎉 自動起動設定が完了しました！"
echo ""
echo "📋 設定内容:"
echo "  ✅ systemd サービス: tool-management.service"
echo "  ✅ デスクトップ自動ログイン"
echo "  ✅ ブラウザ自動起動（キオスクモード）"
echo "  ✅ PostgreSQL自動起動"
echo ""
echo "🔄 再起動して動作確認してください:"
echo "   sudo reboot"
echo ""
echo "🛑 自動起動を停止する場合:"
echo "   sudo systemctl disable tool-management.service"
echo "   rm ~/.config/autostart/tool-management-browser.desktop"
echo ""
