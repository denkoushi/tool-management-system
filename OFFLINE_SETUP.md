# 🌐 オフライン対応設定ガイド

工場・インターネット未接続環境での完全自立動作を実現するための設定手順

## 🎯 概要

工具管理システムをインターネット未接続の環境でも完全に動作させるための設定です。**電源ONだけで工具の借用/返却が可能**になります。

### **実現できること**
- ✅ インターネット未接続でも借用/返却の自動スキャン機能が正常動作
- ✅ 外部CDNに依存しない完全自立システム  
- ✅ ネットワーク障害の影響を受けない安定稼働
- ✅ 工場環境での24時間連続運用

## 🔍 問題の背景

### **オフライン環境での問題**

**症状：** インターネット未接続時に借用/返却のスキャン機能が動作しない

**原因：** Socket.IOライブラリをCDNから読み込んでいるため
```html
<!-- 問題のあるコード -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
```

### **機能別の動作状況**
| 機能 | 通信方式 | オフライン時の動作 |
|------|---------|-------------------|
| **タグ情報確認** | HTTP API | ✅ 正常動作 |
| **借用/返却スキャン** | WebSocket | ❌ 動作しない |
| **手動登録** | HTTP API | ✅ 正常動作 |

## ⚡ 解決方法：Socket.IOのローカル化

### **Step 1: Socket.IOライブラリをダウンロード**

```bash
# プロジェクトディレクトリで実行
cd ~/tool-management-system

# staticディレクトリ作成
mkdir -p static/js

# Socket.IOライブラリをダウンロード
curl -o static/js/socket.io.js https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js

# ダウンロード確認
ls -la static/js/socket.io.js
```

**期待結果：** 約181KBのファイルが作成される

### **Step 2: HTMLファイルの修正**

**ファイル：** `templates/index.html`

**7行目を変更：**
```html
<!-- 変更前 -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>

<!-- 変更後 -->
<script src="/static/js/socket.io.js"></script>
```

### **Step 3: 動作確認**

```bash
# アプリケーション再起動
python app_flask.py
```

**成功時の表示：**
```
🚀 Flask 工具管理システムを開始します...
📡 NFCスキャン監視スレッド開始
🌐 http://0.0.0.0:8501 でアクセス可能
```

### **Step 4: オフライン動作テスト**

**Wi-Fi無効化してテスト：**
```bash
# Wi-Fi無効化
sudo iwconfig wlan0 txpower off

# ブラウザでアクセステスト
# http://127.0.0.1:8501

# テスト完了後、Wi-Fi有効化
sudo iwconfig wlan0 txpower on
```

**テスト項目：**
- [ ] ブラウザで画面表示
- [ ] 「スキャン開始」ボタンが機能
- [ ] ユーザータグのスキャン
- [ ] 工具タグのスキャン  
- [ ] 借用/返却処理の完了

## 📊 パフォーマンス分析

### **レスポンス時間測定**
```bash
# Socket.IOファイル読み込み時間測定
curl -w "Time: %{time_total}s\n" -o /dev/null -s http://127.0.0.1:8501/static/js/socket.io.js
```

**実測結果：** `Time: 0.002286s`（約2.3ミリ秒）

### **CDN vs ローカル比較**
| 項目 | CDN読み込み | ローカル読み込み |
|------|-------------|------------------|
| **読み込み時間** | 50-200ms | 2.3ms |
| **可用性** | ネット依存 | 100%独立 |
| **安定性** | 外部要因あり | 完全制御 |

## 🏭 工場環境でのメリット

### **1. 確実な動作保証**
- インターネット回線の状況に左右されない
- CDNサーバーの障害の影響を受けない
- 電源ONで確実に動作開始

### **2. セキュリティ向上**
- 外部への通信が不要
- ネットワーク分離された環境での運用可能
- 外部攻撃のリスク軽減

### **3. 運用コスト削減**
- インターネット回線が不要
- ネットワーク管理の負担軽減
- トラブル要因の削減

### **4. パフォーマンス向上**  
- ローカル読み込みによる高速化
- 外部ネットワークの遅延なし
- 安定したレスポンス時間

## 🔧 トラブルシューティング

### **ファイルが読み込まれない**

**症状：** ブラウザコンソールに404エラー

**確認方法：**
```bash
# ファイル存在確認
ls -la static/js/socket.io.js

# パーミッション確認
chmod 644 static/js/socket.io.js
```

**解決方法：**
```bash
# ファイル再ダウンロード
curl -o static/js/socket.io.js https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js
```

### **WebSocket接続エラー**

**症状：** 「接続エラー」がブラウザに表示

**確認方法：**
```bash
# アプリケーションログ確認
python app_flask.py
```

**解決方法：**
```bash
# アプリケーション再起動
# Ctrl+C で停止後、再実行
python app_flask.py
```

### **ブラウザキャッシュの問題**

**症状：** 修正後もCDNから読み込もうとする

**解決方法：**
```bash
# ブラウザのハードリロード
# Ctrl+Shift+R (Windows/Linux)
# Cmd+Shift+R (Mac)
```

### **ファイルサイズの違い**

**期待サイズ：** 約181KB

**確認方法：**
```bash
ls -lh static/js/socket.io.js
# -rw-r--r-- 1 user user 181K Aug 26 10:30 socket.io.js
```

**問題時：** ファイルサイズが異常に小さい場合は再ダウンロード

## 📋 運用・メンテナンス

### **定期メンテナンス（推奨：年1回）**

```bash
# Socket.IOの最新版確認・更新
cd ~/tool-management-system/static/js

# バックアップ作成
cp socket.io.js socket.io.js.backup

# 最新版ダウンロード
curl -o socket.io.js.new https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js

# テスト後に置き換え
mv socket.io.js.new socket.io.js
```

### **システム監視**

```bash
# ヘルスチェック用スクリプト
cat > check_offline.sh << 'EOF'
#!/bin/bash
if curl -s http://127.0.0.1:8501/static/js/socket.io.js | head -1 | grep -q "socket.io"; then
    echo "✅ Socket.IOローカルファイル正常"
else
    echo "❌ Socket.IOローカルファイル異常"
fi
EOF

chmod +x check_offline.sh
./check_offline.sh
```

### **バックアップ**

```bash
# 重要ファイルのバックアップ
tar -czf offline-backup-$(date +%Y%m%d).tar.gz \
    static/js/socket.io.js \
    templates/index.html
```

## 🎉 完成！

**これで工場環境でのインターネット未接続運用が可能になりました。**

### **実現された機能：**
- 🔄 完全オフラインでの借用/返却自動スキャン
- 🛡️ 外部依存なしの安定稼働  
- ⚡ 高速レスポンス（2.3ms）
- 🏭 24時間連続運用対応

### **工場作業者への影響：**
- 📱 従来通りの操作（変更なし）
- 🚀 より高速な動作
- 💯 確実な動作保証

---

**設定日：** 2025年8月26日  
**動作確認済み：** インターネット未接続環境での完全動作確認済み  
**パフォーマンス：** Socket.IO読み込み時間 2.3ms
