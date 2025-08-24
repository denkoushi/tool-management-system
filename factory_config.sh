#!/bin/bash
# 工場環境最適化設定スクリプト
# 耐久性・安定性・セキュリティの向上

set -e

echo "🏭 工場環境最適化設定を開始します..."

# 設定可能な変数
COMPANY_NAME="工場名"
ADMIN_PASSWORD="admin123"  # 管理者パスワード（変更推奨）
ENABLE_SSH="no"           # SSH有効化 (yes/no)
SCREEN_ROTATE="0"         # 画面回転 (0,1,2,3)
SCREEN_TIMEOUT="never"    # 画面タイムアウト (never/30/60)

echo "📋 設定内容:"
echo "  会社名: $COMPANY_NAME"
echo "  SSH: $ENABLE_SSH"
echo "  画面回転: $SCREEN_ROTATE"
echo "  画面タイムアウト: $SCREEN_TIMEOUT"
echo ""

# 1. システム最適化
echo "⚙️ 1. システム最適化..."

# スワップ無効化（SDカード保護）
sudo swapoff -a
sudo systemctl disable dphys-swapfile

# ログローテーション設定
sudo tee /etc/logrotate.d/tool-management > /dev/null <<EOF
/var/log/tool-management/*.log {
    weekly
    rotate 4
    compress
    delaycompress
    missingok
    notifempty
    create 644 $(whoami) $(whoami)
}
EOF

# ログディレクトリ作成
sudo mkdir -p /var/log/tool-management
sudo chown $(whoami):$(whoami) /var/log/tool-management

# 2. セキュリティ設定
echo "🔒 2. セキュリティ設定..."

# SSH設定
if [ "$ENABLE_SSH" = "no" ]; then
    sudo systemctl disable ssh
    sudo systemctl stop ssh
    echo "  SSH無効化完了"
else
    echo "  SSH有効のまま"
fi

# ファイアウォール設定
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 8501/tcp  # アプリケーションポート
if [ "$ENABLE_SSH" = "yes" ]; then
    sudo ufw allow ssh
fi

# 自動ロック無効化
gsettings set org.gnome.desktop.session idle-delay 0
gsettings set org.gnome.desktop.screensaver lock-enabled false

# 3. 耐久性向上設定
echo "💪 3. 耐久性向上..."

# Wi-Fi省電力無効化
sudo iwconfig wlan0 power off 2>/dev/null || echo "  Wi-Fi設定スキップ"

# USB省電力無効化
echo 'SUBSYSTEM=="usb", ACTION=="add", ATTR{power/control}="on"' | sudo tee /etc/udev/rules.d/50-usb-power.rules > /dev/null

# GPUメモリ増加
sudo sed -i '/gpu_mem/d' /boot/firmware/config.txt
echo "gpu_mem=128" | sudo tee -a /boot/firmware/config.txt > /dev/null

# 4. ディスプレイ設定
echo "🖥️ 4. ディスプレイ設定..."

# 画面回転設定
if [ "$SCREEN_ROTATE" != "0" ]; then
    sudo sed -i '/display_rotate/d' /boot/firmware/config.txt
    echo "display_rotate=$SCREEN_ROTATE" | sudo tee -a /boot/firmware/config.txt > /dev/null
    echo "  画面回転: ${SCREEN_ROTATE}設定"
fi

# HDMI強制有効化
sudo sed -i '/hdmi_force_hotplug/d' /boot/firmware/config.txt
echo "hdmi_force_hotplug=1" | sudo tee -a /boot/firmware/config.txt > /dev/null

# 5. 停電対策設定
echo "⚡ 5. 停電対策..."

# ファイルシステム最適化
sudo tune2fs -o journal_data_writeback /dev/mmcblk0p2 2>/dev/null || echo "  ファイルシステム最適化スキップ"

# tmpfsマウント（ログ用）
echo "tmpfs /tmp tmpfs defaults,noatime,nosuid,size=100m 0 0" | sudo tee -a /etc/fstab > /dev/null

# 6. 監視・ヘルスチェック設定
echo "📊 6. 監視設定..."

# ヘルスチェックスクリプト作成
cat > ~/tool-management-system/health_check.sh <<'EOF'
#!/bin/bash
# システムヘルスチェックスクリプト

LOG_FILE="/var/log/tool-management/health.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# アプリケーション確認
if curl -s http://127.0.0.1:8501 > /dev/null 2>&1; then
    APP_STATUS="OK"
else
    APP_STATUS="ERROR"
fi

# データベース確認
if docker exec postgres-tool pg_isready -U app > /dev/null 2>&1; then
    DB_STATUS="OK"
else
    DB_STATUS="ERROR"
fi

# NFCリーダー確認
if lsusb | grep -q "Sony Corp"; then
    NFC_STATUS="OK"
else
    NFC_STATUS="ERROR"
fi

# ログ出力
echo "$DATE - APP:$APP_STATUS DB:$DB_STATUS NFC:$NFC_STATUS" >> $LOG_FILE

# エラー時の自動復旧
if [ "$APP_STATUS" = "ERROR" ]; then
    sudo systemctl restart tool-management.service
    echo "$DATE - APP restarted" >> $LOG_FILE
fi

if [ "$DB_STATUS" = "ERROR" ]; then
    docker restart postgres-tool
    echo "$DATE - DB restarted" >> $LOG_FILE
fi
EOF

chmod +x ~/tool-management-system/health_check.sh

# cron設定（5分間隔でヘルスチェック）
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/$(whoami)/tool-management-system/health_check.sh") | crontab -

# 7. 管理者向けショートカット作成
echo "👤 7. 管理者ツール作成..."

# デスクトップにショートカット作成
mkdir -p ~/Desktop

# システム管理ショートカット
cat > ~/Desktop/system_admin.desktop <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=システム管理
Comment=工具管理システムの管理画面
Exec=lxterminal -e "bash -c 'echo 工具管理システム管理; echo; echo 1. サービス状況確認; sudo systemctl status tool-management.service; echo; echo 2. アプリケーションログ; sudo journalctl -u tool-management.service -n 20; echo; echo Enterで終了; read'"
Icon=system-run
Terminal=false
Categories=System;
EOF

chmod +x ~/Desktop/system_admin.desktop

# システム再起動ショートカット
cat > ~/Desktop/restart_system.desktop <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=システム再起動
Comment=システムを再起動します
Exec=bash -c 'zenity --question --text="システムを再起動しますか？" && sudo reboot'
Icon=system-reboot
Terminal=false
Categories=System;
EOF

chmod +x ~/Desktop/restart_system.desktop

# 8. 起動時メッセージ設定
echo "📢 8. 起動メッセージ設定..."

# motd設定
sudo tee /etc/motd > /dev/null <<EOF

🧰 工具持出返却管理システム
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 システム状況: http://127.0.0.1:8501
🔧 管理者向け: デスクトップのショートカットを使用
📞 サポート: システム管理者に連絡

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
$COMPANY_NAME
EOF

# 9. 設定完了の確認
echo ""
echo "🎉 工場環境最適化設定が完了しました！"
echo ""
echo "📋 適用された設定:"
echo "  ✅ システム最適化（スワップ無効化、ログローテーション）"
echo "  ✅ セキュリティ設定（ファイアウォール、自動ロック無効）"
echo "  ✅ 耐久性向上（省電力無効化、GPU最適化）"
echo "  ✅ 停電対策（ファイルシステム最適化）"
echo "  ✅ 監視設定（自動ヘルスチェック）"
echo "  ✅ 管理者ツール（デスクトップショートカット）"
echo ""
echo "⚠️  注意事項:"
echo "  - システム再起動が必要です: sudo reboot"
echo "  - 管理者パスワードを変更してください"
echo "  - 定期的なシステム更新を実施してください"
echo ""
echo "🔧 管理コマンド:"
echo "  サービス確認: sudo systemctl status tool-management.service"
echo "  ログ確認: sudo journalctl -u tool-management.service -f"
echo "  ヘルス確認: cat /var/log/tool-management/health.log"
echo ""
EOF
