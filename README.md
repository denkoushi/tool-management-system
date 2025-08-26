# 🧰 工具持出返却管理システム

Flask + PostgreSQL + NFCを使用したリアルタイム工具管理システム

## ✨ 機能
- 🔄 自動NFCスキャンによる工具の貸出・返却
- 👤 ユーザー・工具のタグ登録  
- 📚 工具名マスタ管理
- 🌐 リアルタイムWebUI
- 📊 貸出履歴・現在の貸出状況表示

## 📁 構成
- `app_flask.py` - メインのFlaskアプリケーション
- `templates/index.html` - レスポンシブWebUI
- PostgreSQL データベース（Docker）

## 🚀 起動方法
```bash
# リポジトリをクローン
git clone https://github.com/denkoushi/tool-management-system.git
cd tool-management-system

# 仮想環境を作成・アクティベート
python3 -m venv venv
source venv/bin/activate

# 依存パッケージをインストール
pip install flask flask-socketio psycopg2-binary pyscard

# アプリケーション起動
python app_flask.py
```

## 🌐 アクセス
起動後、ブラウザで以下にアクセス：
- ローカル: http://127.0.0.1:8501
- ネットワーク: http://[RaspberryPiのIP]:8501

## 🛠 開発環境
- **OS**: Raspberry Pi OS
- **言語**: Python 3
- **フレームワーク**: Flask + SocketIO
- **データベース**: PostgreSQL (Docker)
- **ハードウェア**: NFCリーダー (PC/SC対応)

## 🏭 実環境での重要な注意事項

**⚠️ 実装時の重要な相違点**

このリポジトリは標準的な環境用に記載されていますが、実際の動作確認は以下の特別な環境で行われています。

### **環境の違い**

| 項目 | 📖 ドキュメント記載 | 🖥️ 実際の動作環境 |
|------|-------------------|------------------|
| **プロジェクトフォルダ名** | `tool-management-system` | `pgraf` |
| **PostgreSQLコンテナ名** | `postgres-tool` | `pg` |
| **フォルダパス** | `/home/user/tool-management-system` | `/home/denkon5/pgraf` |
| **ユーザー名** | `user` | `denkon5` |

### **実装時の対応方法**

**新規環境構築の場合：**
- 📚 このドキュメント通りに実装してください
- 標準的な名称（`tool-management-system`, `postgres-tool`）を使用

**既存環境への適用の場合：**
- 🔧 環境に合わせてコマンドのフォルダ名・コンテナ名を読み替えてください
- 例：`cd ~/tool-management-system` → `cd ~/pgraf`

### **詳細な実環境情報**

📋 **実際に動作確認済みの詳細な手順については以下を参照：**
- **[🎯 Raspberry Pi自動起動 - 実践成功事例](./docs/RASPBERRY_PI_AUTO_START_SUCCESS.md)** - 実環境での完全な設定手順
- **[🌐 オフライン対応設定ガイド](./OFFLINE_SETUP.md)** - インターネット未接続環境での動作設定

### **フォルダ構成の実例**

**実際のRaspberry Pi環境：**
```
/home/denkon5/pgraf/
├── 📂 __pycache__/
├── 📂 static/
│   └── 📂 js/
│       └── socket.io.js     ← オフライン対応
├── 📂 templates/
│   └── index.html
├── 📂 venv/
├── 📄 app_flask.py
├── 📄 docker-compose.yml
└── 📄 setup_auto_start.sh
```

**PostgreSQL関連：**
```bash
# 実環境でのコンテナ確認
docker ps | grep pg    # "postgres-tool" ではなく "pg"

# 実環境での自動起動設定  
docker update --restart unless-stopped pg    # コンテナ名が "pg"
```

## 📋 前提条件
- Docker (PostgreSQL用)
- NFCリーダー
- Python 3.8+

## 🗄️ データベーステーブル
- `users` - ユーザー情報
- `tools` - 工具情報  
- `tool_master` - 工具名マスタ
- `loans` - 貸出・返却履歴
- `scan_events` - スキャンログ

## 🎯 使用方法
1. 「🟢 自動スキャン開始」をクリック
2. ユーザータグをかざす
3. 工具タグをかざす  
4. 自動的に貸出/返却処理が完了

## 📖 詳細ドキュメント

- [初期セットアップガイド](./SETUP.md)
- [自動起動設定ガイド](./AUTO_START.md)
- **[🎯 Raspberry Pi自動起動 - 実践成功事例](./docs/RASPBERRY_PI_AUTO_START_SUCCESS.md)** - 2025年8月実環境での動作確認済み手順

## 📝 ライセンス
MIT License
