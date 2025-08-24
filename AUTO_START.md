# 🤖 自動起動設定ガイド

工場現場での完全自動化：Raspberry Pi起動から工具管理システム使用可能まで

## 🎯 自動化の流れ

```
電源ON → 自動ログイン → アプリ起動 → ブラウザ起動 → 即座に使用可能！
```

## ⚡ 自動設定（推奨）

**前提条件**: `SETUP.md` の手順1-4が完了していること

```bash
# プロジェクトディレクトリに移動
cd ~/tool-management-system

# 自動設定スクリプト実行
chmod +x setup_auto_start.sh
./setup_auto_start.sh

# 再起動して確認
sudo reboot
```

## 📝 手動設定（詳細制御したい場合）

### 1. systemdサービス作成

```bash
sudo nano /etc/systemd/system/tool-management.service
```

内容：
```ini
[Unit]
Description=Tool Management System
After=network.target docker.service
Requires=docker.service
StartLimitIntervalSec=0

[Service]
Type=simple
User=denkon5
Group=denkon5
WorkingDirectory=/home/denkon5/tool-management-system
Environment=PATH=/home/denkon5/tool-management-system/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/home/denkon5/tool-management-system/venv/bin/python app_flask.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

サービス有効化：
```bash
sudo systemctl daemon-reload
sudo systemctl enable tool-management.service
sudo systemctl start tool-management.service
```

### 2. デスクトップ自動ログイン

```bash
sudo raspi-config
```

**Advanced Options** → **Login** → **Desktop Autologin**

または：
```bash
sudo raspi-config nonint do_boot_behaviour B4
```

### 3. ブラウザ自動起動設定

```bash
# autostart ディレクトリ作成
mkdir -p ~/.config/autostart

# デスクトップファイル作成
nano ~/.config/autostart/tool-management-browser.desktop
```

内容：
```ini
[Desktop Entry]
Type=Application
Name=Tool Management Browser
Comment=Auto start tool management system browser
Exec=/home/denkon5/tool-management-system/start_browser.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
```

### 4. ブラウザ起動スクリプト

```bash
nano ~/tool-management-system/start_browser.sh
chmod +x ~/tool-management-system/start_browser.sh
```

内容：
```bash
#!/bin/bash
# サービス起動まで待機
for i in {1..60}; do
    if curl -s http://127.0.0.1:8501 > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# スクリーンセーバー無効化
xset s off
xset -dpms
xset s noblank

# キオスクモードでブラウザ起動
chromium-browser \
    --start-fullscreen \
    --kiosk \
    --incognito \
    --disable-translate \
    --disable-infobars \
    --no-first-run \
    --no-sandbox \
    --disable-gpu \
    http://127.0.0.1:8501
```

## 🎨 カスタマイズオプション

### 画面回転設定

```bash
# config.txt編集
sudo nano /boot/firmware/config.txt

# 以下を追加（必要に応じて）
display_rotate=1  # 90度回転
display_rotate=2  # 180度回転
display_rotate=3  # 270度回転
```

### 解像度設定

```bash
# config.txt に追加
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=82  # 1920x1080 60Hz
```

### タッチスクリーン対応

```bash
# 仮想キーボードインストール
sudo apt install onboard

# 自動起動に追加
echo "onboard &" >> ~/.config/autostart/tool-management-browser.desktop
```

## 🔧 運用・メンテナンス

### サービス状態確認

```bash
# サービス状態
sudo systemctl status tool-management.service

# ログ確認
sudo journalctl -u tool-management.service -f

# PostgreSQL確認
docker ps | grep postgres
```

### 自動起動の停止・開始

```bash
# 停止
sudo systemctl stop tool-management.service
sudo systemctl disable tool-management.service

# 開始
sudo systemctl enable tool-management.service
sudo systemctl start tool-management.service

# ブラウザ自動起動停止
rm ~/.config/autostart/tool-management-browser.desktop
```

### アプリケーション更新

```bash
# アプリ更新時
cd ~/tool-management-system
git pull origin main

# サービス再起動
sudo systemctl restart tool-management.service
```

## 🚨 トラブルシューティング

### アプリが起動しない

```bash
# サービスログ確認
sudo journalctl -u tool-management.service -n 50

# 手動起動テスト
cd ~/tool-management-system
source venv/bin/activate
python app_flask.py
```

### ブラウザが開かない

```bash
# X11転送確認
echo $DISPLAY

# 手動ブラウザ起動テスト
chromium-browser http://127.0.0.1:8501

# デスクトップファイル確認
ls -la ~/.config/autostart/
```

### PostgreSQL接続エラー

```bash
# コンテナ状態確認
docker ps -a | grep postgres

# 再起動
docker restart postgres-tool

# ログ確認
docker logs postgres-tool
```

### 画面表示の問題

```bash
# ディスプレイ設定確認
xrandr

# 解像度強制設定
xrandr --output HDMI-1 --mode 1920x1080

# GPU メモリ増加（config.txt）
gpu_mem=128
```

## ⚙️ 工場環境での最適化

### セキュリティ設定

```bash
# SSH無効化（必要に応じて）
sudo systemctl disable ssh

# ファイアウォール設定
sudo ufw enable
sudo ufw allow 8501/tcp
```

### 安定性向上

```bash
# スワップ無効化（SDカード保護）
sudo swapoff -a
sudo systemctl disable dphys-swapfile

# ログローテーション設定
sudo nano /etc/logrotate.d/tool-management
```

### 省電力設定

```bash
# Wi-Fi省電力無効化
sudo iwconfig wlan0 power off

# USB省電力無効化
echo 'SUBSYSTEM=="usb", ACTION=="add", ATTR{power/control}="on"' | sudo tee /etc/udev/rules.d/50-usb-power.rules
```

## 🎉 完成！

設定完了後：
1. **電源ON** → 自動ログイン
2. **30秒程度** → ブラウザ起動
3. **工具管理画面表示** → 即座に使用可能！

**工場作業者は何もする必要がありません。電源を入れるだけで工具管理システムが使えます！** 🚀
