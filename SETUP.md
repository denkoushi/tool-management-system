# 🔧 完全環境構築ガイド

新しいRaspberry Piでの工具管理システムの完全セットアップ手順

## 📋 前提条件
- Raspberry Pi OS (Bookworm推奨)
- インターネット接続
- **NFCリーダー**: RC-S300/S1 (Sony PaSoRi 4.0) 推奨、その他PC/SC対応機器
- 最低4GB RAM推奨
- **NFCタグ**: FeliCa、MIFARE、ISO14443対応タグ

## 🚀 1. システム更新

```bash
sudo apt update
sudo apt upgrade -y
```

## 🐳 2. Docker インストール・PostgreSQL設定

```bash
# Dockerインストール
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 再ログインまたは
newgrp docker

# PostgreSQLコンテナ起動
docker run --name postgres-tool \
  -e POSTGRES_DB=sensordb \
  -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=app \
  -p 5432:5432 \
  -d postgres:16

# 自動起動設定
docker update --restart unless-stopped postgres-tool
```

## 📡 3. NFCリーダー設定（RC-S300/S1 PaSoRi対応）

### 3-1. PC/SCスタック導入・起動

```bash
# PC/SCライブラリとドライバーをインストール
sudo apt update
sudo apt install -y pcscd pcsc-tools libccid libpcsclite1 libpcsclite-dev opensc swig

# PC/SCサービス自動起動設定・開始
sudo systemctl enable --now pcscd

# ユーザーをdialoutグループに追加（権限設定）
sudo usermod -a -G dialout $USER
```

**⚠️ 重要**: この時点ではNFCリーダーを接続しないでください

### 3-2. NFCリーダー接続・認識確認

NFCリーダー（RC-S300/S1等）をUSBポートに接続後：

```bash
# USB接続確認
lsusb | grep -i -E 'sony|rc-|felica|nfc'
```

**成功例**：
```
Bus 001 Device 002: ID 054c:0dc8 Sony Corp. FeliCa Port/PaSoRi 4.0
```

### 3-3. タグ反応テスト（最重要）

```bash
# PC/SCスキャンテスト
pcsc_scan
```

**成功時の表示例**：
- `Reader 0: Sony FeliCa Port/PaSoRi 4.0...`
- タグをかざすと：`Card inserted`
- ATR（応答データ）が表示される

**Ctrl+C で終了**

### 3-4. Python pyscard インストール

```bash
# 開発ツールとpyscard
sudo apt install -y python3-pip python3-dev
pip install --break-system-packages pyscard
```

**注意**: `--break-system-packages` はRaspberry Pi OSのpip制限回避用です

## 🐍 4. Python環境・アプリケーションセットアップ

```bash
# 必要なシステムパッケージ
sudo apt install -y python3-venv python3-pip python3-dev git

# リポジトリクローン
git clone https://github.com/denkoushi/tool-management-system.git
cd tool-management-system

# 仮想環境作成・アクティベート
python3 -m venv venv
source venv/bin/activate

# Pythonパッケージインストール
# Raspberry Pi OS環境では仮想環境内なので通常のpipでOK
pip install -r requirements.txt

# pyscardが仮想環境で問題がある場合のみ：
# pip install --break-system-packages pyscard

# データベース接続テスト
python3 -c "import psycopg2; conn=psycopg2.connect(host='127.0.0.1', port=5432, dbname='sensordb', user='app', password='app'); print('✅ データベース接続成功'); conn.close()"

# NFCスキャンテスト
python3 -c "from smartcard.CardRequest import CardRequest; print('✅ pyscard正常インストール')"
```

## 🎯 5. アプリケーション起動・テスト

```bash
# アプリケーション起動（新構成）
python -m app.main
# 互換: python app_flask.py でも可
```

成功すると以下が表示：
```
🚀 Flask 工具管理システムを開始します...
📡 NFCスキャン監視スレッド開始
🌐 http://0.0.0.0:8501 でアクセス可能
```

## 🌐 6. ブラウザでアクセス

- **ローカル**: http://127.0.0.1:8501
- **ネットワーク**: http://[RaspberryPiのIP]:8501

## 🔧 7. トラブルシューティング

### PostgreSQL接続エラー
```bash
# コンテナ状態確認
docker ps
docker logs postgres-tool

# 再起動
docker restart postgres-tool
```

### NFCリーダー認識されない（RC-S300/S1対応）
```bash
# 1. USB機器確認
lsusb | grep -i -E 'sony|rc-|felica|nfc'
# 期待値: Bus 001 Device 002: ID 054c:0dc8 Sony Corp. FeliCa Port/PaSoRi 4.0

# 2. PC/SCサービス再起動
sudo systemctl restart pcscd
sudo systemctl status pcscd

# 3. 権限確認
groups $USER  # dialoutが含まれているか確認

# 4. PC/SCでの認識確認
pcsc_scan
# 成功時: "Reader 0: Sony FeliCa Port/PaSoRi 4.0" が表示

# 5. リーダー物理的な再接続
# USBを抜き差しして lsusb で再確認
```

### pyscard インストールエラー
```bash
# 仮想環境内での問題の場合
pip install pyscard

# システム全体での問題の場合
pip install --break-system-packages pyscard

# 依存関係の問題の場合
sudo apt install -y python3-dev swig libpcsclite-dev
pip install pyscard
```

### タグスキャンでタイムアウトエラー
```bash
# 1. PC/SCサービス確認
sudo systemctl status pcscd

# 2. リーダー認識確認
pcsc_scan  # タグをかざして反応確認

# 3. タグの種類確認
# FeliCa（おサイフケータイ）、MIFARE、ISO14443対応タグを使用

# 4. 物理的な問題
# - リーダーとタグの距離（1-2cm推奨）
# - タグの汚れや破損確認
# - 金属による干渉回避
```

### 仮想環境の問題
```bash
# 仮想環境削除・再作成
deactivate  # 仮想環境から出る
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### アプリケーション起動時のエラー
```bash
# 1. 依存関係確認
pip list | grep -E 'flask|socketio|psycopg2|pyscard'

# 2. データベース接続確認
python3 -c "import psycopg2; psycopg2.connect(host='127.0.0.1', port=5432, dbname='sensordb', user='app', password='app')"

# 3. NFCリーダー確認
python3 -c "from smartcard.CardRequest import CardRequest; print('OK')"

# 4. ポート使用状況確認
sudo netstat -tulpn | grep 8501
```

## ⚙️ 8. 自動起動設定（オプション）

### systemdサービス作成
```bash
sudo nano /etc/systemd/system/tool-management.service
```

ファイル内容：
```ini
[Unit]
Description=Tool Management System
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=denkon5
WorkingDirectory=/home/denkon5/tool-management-system
ExecStart=/home/denkon5/tool-management-system/venv/bin/python -m app.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

サービス有効化：
```bash
sudo systemctl daemon-reload
sudo systemctl enable tool-management.service
sudo systemctl start tool-management.service

# 状態確認
sudo systemctl status tool-management.service
```

## 📊 9. データベース管理（オプション）

### pgAdminでの管理
```bash
# pgAdmin起動（Web版）
docker run --name pgadmin-tool \
  -e PGADMIN_DEFAULT_EMAIL=admin@example.com \
  -e PGADMIN_DEFAULT_PASSWORD=admin \
  -p 5050:80 \
  -d dpage/pgadmin4

# http://[RaspberryPiのIP]:5050 でアクセス
# サーバー追加: Host=host.docker.internal, Port=5432
```

### バックアップ・復元
```bash
# データベースバックアップ
docker exec postgres-tool pg_dump -U app sensordb > backup.sql

# 復元
docker exec -i postgres-tool psql -U app sensordb < backup.sql
```

## 🎉 完了！

これで完全な工具管理システム環境が構築されました。

### 次のステップ：
1. 工具名マスタに工具を登録
2. ユーザーをNFCタグで登録
3. 工具にNFCタグを割り当て
4. 自動スキャン開始！

---

## 🆘 サポート

問題が発生した場合：
1. このガイドのトラブルシューティング参照
2. GitHub Issues で報告
3. ログファイル確認：`sudo journalctl -u tool-management.service -f`
