# Admonish Grumbler ガイドライン

## プロジェクト概要

### なぜ作ったか

Twitter風の愚痴投稿アプリ。日常のストレスを気軽にアウトプットする場所として開発した。

### 何を解決したいか

ストレスの可視化とメンタルヘルスケア。投稿を蓄積しAIで定期的に分析することで、自分のメンタル状態の傾向を客観的に把握できるようにする。

## ドメインモデル

### Post（投稿）

ユーザーが投稿する愚痴・つぶやき。Markdown形式で記述でき、URLが含まれる場合はOGPプレビューが自動付与される。

### User（ユーザー）

アプリケーションの利用者。認証情報とアバター画像を持つ。

### Summary（サマリー）

AIによる投稿分析結果。週次・月次で生成され、ストレススコア・幸福度・感情スコア・トピック抽出・カウンセリングメッセージなどを含む。ユーザーからのフィードバックを次回分析に反映する仕組みを持つ。

## アーキテクチャ

オニオンアーキテクチャを採用している。依存方向は外側から内側への一方向のみ許可する。

```
app/
├── domain/           # ドメイン層（最内層）
│   ├── model/        #   エンティティ・値オブジェクト
│   └── services/     #   ドメインサービス（純粋なビジネスロジック）
├── usecase/          # ユースケース層
│   └── *_interactor.py
├── infrastructure/   # インフラ層（最外層）
│   ├── *_repository.py    # データ永続化
│   ├── *_client.py        # 外部API・HTTP通信
│   └── *_converter.py     # 外部ライブラリ依存の変換処理
└── presentation/     # プレゼンテーション層
    └── (Flask routes, templates)
```

## コーディングガイドライン

### 各層の責務

| 層 | 責務 | 許可される依存 |
|----|------|---------------|
| **domain** | ビジネスルール、エンティティ定義、ドメインロジック | なし（純粋なPythonのみ） |
| **usecase** | アプリケーション固有のビジネスルール、ワークフロー制御 | domain |
| **infrastructure** | DB操作、外部API呼び出し、外部ライブラリ利用 | domain, usecase |
| **presentation** | HTTPリクエスト/レスポンス処理、テンプレート描画 | domain, usecase, infrastructure |

### ファイル命名規則

各層のファイル名・クラス名は、用途に応じたサフィックスで統一する。

| 層 | サフィックス | 用途 | 例 |
|----|------------|------|-----|
| **domain/model** | なし（エンティティ名そのまま） | エンティティ・値オブジェクト | `user.py` → `User` |
| **domain/services** | `*_builder.py` など（役割に応じた動詞） | ドメインサービス | `ai_prompt_builder.py` → `build_prompt()` |
| **usecase** | `*_interactor.py` | ユースケース（アプリケーションロジック） | `post_interactor.py` → `PostInteractor` |
| **infrastructure** | `*_repository.py` | DB永続化 | `post_repository.py` → `PostRepository` |
| **infrastructure** | `*_client.py` | 外部API・HTTP通信 | `ai_client.py` → `AIClient` |
| **infrastructure** | `*_converter.py` | 外部ライブラリ依存の変換処理 | `message_converter.py` → `MessageConverter` |
| **interface/http** | `*_controller.py` | HTTPエンドポイント（Flask Blueprint） | `post_controller.py` → Blueprint `"post"` |

**ルール:**
- ファイル名のサフィックスとクラス名のサフィックスは一致させる（例: `*_client.py` には `*Client` クラス）
- infrastructure層のファイルが増えた場合は、サフィックス単位でサブディレクトリへの分割を検討する

### ファイルヘッダコメント

各Pythonファイルの先頭には、以下の情報を含むドキュメントコメント（docstring）を記述する。

- **責務**: そのファイル（クラス/モジュール）が担う責任の範囲
- **概要**: 主要なクラスや関数の簡単な説明
- **層**: オニオンアーキテクチャ上の配置（domain / usecase / infrastructure / interface）

```python
"""
[層] ファイルの責務を1行で説明

概要:
  主要なクラスや処理の簡単な説明。
"""
```

### 依存方向のルール

- **domain層は他の層に依存してはならない**。標準ライブラリ以外のimportは禁止。
- **usecase層はdomain層のみに依存する**。infrastructure層のクラスを直接importしてよいが、フレームワーク固有のコードは含めない。
- 外部API呼び出し、HTTP通信、外部ライブラリ（`requests`, `markdown`, `google.genai` 等）に依存するコードは必ず **infrastructure層** に配置する。
- フレームワーク固有のコード（Flask, flask_login 等）はドメインモデルに混入させない。
