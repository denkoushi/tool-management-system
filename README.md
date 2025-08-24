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

## 📝 ライセンス
MIT License
