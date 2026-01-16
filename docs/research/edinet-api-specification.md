# EDINET API 調査レポート

## 概要

EDINET API（金融庁が提供する有価証券報告書等の開示書類電子開示システムのAPI）は、利用者がプログラムを介してEDINETのデータベースから効率的に開示情報を取得できるREST API です。有価証券報告書、四半期報告書、臨時報告書などの企業開示書類を、JSON形式のメタデータ取得やZIP/PDF形式での書類ダウンロードにより、自動的に収集・処理することが可能です。

## 基本情報

| 項目 | 内容 |
|------|------|
| 公式サイト | https://disclosure2.edinet-fsa.go.jp/ |
| API仕様書バージョン | Version 2（2025年10月版） |
| ベースURL | https://api.edinet-fsa.go.jp/api/v2/ |
| 通信方式 | HTTPS (TLS 1.2以上) |
| データ形式 | JSON (UTF-8), ZIP, PDF, CSV |
| 認証方式 | APIキー（Subscription-Key） |
| 提供元 | 金融庁 企画市場局 企業開示課 |
| 利用規約 | https://disclosure2dl.edinet-fsa.go.jp/guide/static/disclosure/WZEK0030.html |

## アーキテクチャ

EDINET APIは2つの主要なAPIで構成されています。

### 1. 書類一覧API（Document List API）
- **目的**: 提出された書類の一覧を日付ごとに取得
- **機能**:
  - メタデータのみの取得（件数、更新日時など）
  - 提出書類一覧とメタデータの取得（書類の詳細情報）
- **更新頻度**: 8:30以降、原則1分毎に更新

### 2. 書類取得API（Document Download API）
- **目的**: 具体的な書類データを取得
- **取得可能形式**:
  - 提出本文書及び監査報告書（ZIP）
  - PDF
  - 代替書面・添付文書（ZIP）
  - 英文ファイル（ZIP）
  - CSV（XBRLからの変換）

### データフロー

```
1. 書類一覧API（メタデータ）
   ↓ 件数確認
2. 書類一覧API（提出書類一覧）
   ↓ 必要な書類を特定
3. 書類取得API
   ↓ 書類管理番号を指定
4. 書類データ取得（ZIP/PDF）
```

### データ保持期間

- **閲覧期間**: 縦覧期間 + 延長期間
- **有価証券報告書**: 5年 + 5年 = 10年
- **四半期報告書**: 3年 + 7年 = 10年
- **半期報告書**: 5年 + 5年 = 10年

## 導入手順

### 前提条件

- サポートされているOS・Webブラウザ（製品サポートが継続しているもの）
- メールアドレス（アカウント登録用）
- TLS 1.2以上をサポートする開発環境
- **注意**: ブラウザ上のJavaScriptからの直接呼び出しは不可（クロスドメイン通信非対応）

### ステップ1: アカウント登録とAPIキー取得

1. **ポップアップ許可設定**（初回のみ）
   - ブラウザ（Microsoft Edge推奨）でポップアップブロックを許可

2. **APIキー発行画面へアクセス**
   ```
   https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1
   ```

3. **アカウント作成**
   - メールアドレスを入力
   - 確認コードを受信・入力
   - パスワードを設定（大文字、小文字、数字、記号のうち3種類以上、8文字以上）

4. **APIキー発行**
   - 連絡先情報を入力
   - APIキーが画面に表示される（控えておく）

### ステップ2: APIの基本的な利用方法

#### 1. メタデータの取得（件数確認）

```bash
curl "https://api.edinet-fsa.go.jp/api/v2/documents.json?date=2023-04-03&type=1&Subscription-Key=YOUR_API_KEY"
```

**レスポンス例:**
```json
{
  "metadata": {
    "title": "提出された書類を把握するためのAPI",
    "parameter": {
      "date": "2023-04-03",
      "type": "1"
    },
    "resultset": {
      "count": 13
    },
    "processDateTime": "2023-04-03 13:01",
    "status": "200",
    "message": "OK"
  }
}
```

#### 2. 提出書類一覧の取得

```bash
curl "https://api.edinet-fsa.go.jp/api/v2/documents.json?date=2023-04-03&type=2&Subscription-Key=YOUR_API_KEY"
```

**レスポンス例:**
```json
{
  "metadata": { ... },
  "results": [
    {
      "seqNumber": 1,
      "docID": "S1000001",
      "edinetCode": "E10001",
      "secCode": "10000",
      "JCN": "6000012010023",
      "filerName": "エディネット株式会社",
      "docDescription": "有価証券届出書（内国投資信託受益証券）",
      "submitDateTime": "2023-04-03 12:34",
      "xbrlFlag": "1",
      "pdfFlag": "1",
      "csvFlag": "1",
      "legalStatus": "1"
    }
  ]
}
```

#### 3. 書類の取得

```bash
# 提出本文書及び監査報告書（ZIP）
curl "https://api.edinet-fsa.go.jp/api/v2/documents/S1000001?type=1&Subscription-Key=YOUR_API_KEY" -o document.zip

# PDF
curl "https://api.edinet-fsa.go.jp/api/v2/documents/S1000001?type=2&Subscription-Key=YOUR_API_KEY" -o document.pdf

# CSV（XBRL変換）
curl "https://api.edinet-fsa.go.jp/api/v2/documents/S1000001?type=5&Subscription-Key=YOUR_API_KEY" -o document.zip
```

## API仕様リファレンス

### 書類一覧API

#### エンドポイント
```
GET https://api.edinet-fsa.go.jp/api/v2/documents.json
```

#### リクエストパラメータ

| パラメータ名 | 必須 | 型 | 説明 |
|-------------|------|-----|------|
| date | ○ | string | ファイル日付（YYYY-MM-DD形式）。当日以前で直近の財務局営業日の24時において10年を経過していない日付 |
| type | - | string | 1: メタデータのみ（デフォルト）<br>2: 提出書類一覧及びメタデータ |
| Subscription-Key | ○ | string | APIキー |

#### レスポンス（type=2の場合の主要フィールド）

| 項目名 | 項目ID | 型 | 説明 |
|--------|--------|-----|------|
| 連番 | seqNumber | number | ファイル日付ごとの連番 |
| 書類管理番号 | docID | string | 書類管理番号（8桁） |
| 提出者EDINETコード | edinetCode | string | 提出者のEDINETコード（6桁） |
| 提出者証券コード | secCode | string | 提出者の証券コード（5桁） |
| 提出者法人番号 | JCN | string | 提出者の法人番号（13桁） |
| 提出者名 | filerName | string | 提出者の名前（全角128文字以下） |
| 府令コード | ordinanceCode | string | 府令コード（3桁） |
| 様式コード | formCode | string | 様式コード（6桁） |
| 書類種別コード | docTypeCode | string | 書類種別コード（3桁） |
| 期間（自） | periodStart | string | 期間開始日（YYYY-MM-DD形式） |
| 期間（至） | periodEnd | string | 期間終了日（YYYY-MM-DD形式） |
| 提出日時 | submitDateTime | string | 提出日時（YYYY-MM-DD hh:mm形式） |
| 提出書類概要 | docDescription | string | 提出書類の概要（全半角147文字以下） |
| 取下区分 | withdrawalStatus | string | 0: 通常, 1: 取下書, 2: 取り下げられた書類 |
| XBRL有無フラグ | xbrlFlag | string | 1: あり, 0: なし |
| PDF有無フラグ | pdfFlag | string | 1: あり, 0: なし |
| CSV有無フラグ | csvFlag | string | 1: あり, 0: なし |
| 縦覧区分 | legalStatus | string | 1: 縦覧中, 2: 延長期間中, 0: 閲覧期間満了 |

### 書類取得API

#### エンドポイント
```
GET https://api.edinet-fsa.go.jp/api/v2/documents/{書類管理番号}
```

#### リクエストパラメータ

| パラメータ名 | 必須 | 型 | 説明 |
|-------------|------|-----|------|
| type | ○ | string | 1: 提出本文書及び監査報告書<br>2: PDF<br>3: 代替書面・添付文書<br>4: 英文ファイル<br>5: CSV |
| Subscription-Key | ○ | string | APIキー |

#### レスポンス形式

| type | Content-Type | 形式 |
|------|--------------|------|
| 1 | application/octet-stream | ZIP |
| 2 | application/pdf | PDF |
| 3 | application/octet-stream | ZIP |
| 4 | application/octet-stream | ZIP |
| 5 | application/octet-stream | ZIP |

#### ZIPファイル構成（type=1）

```
ZIP
├── PublicDoc/          提出本文書
├── AuditDoc/           監査報告書
└── XBRL/
    ├── PublicDoc/      提出本文書（XBRL）
    ├── AuditDoc/       監査報告書（XBRL）
    └── EnglishDoc/     英文ファイル
```

## 実装例

### Python実装例

#### 基本的な使い方

```python
import requests
from datetime import datetime

# APIキー
API_KEY = "YOUR_API_KEY"
BASE_URL = "https://api.edinet-fsa.go.jp/api/v2"

def get_document_list(date: str, api_key: str):
    """書類一覧を取得"""
    url = f"{BASE_URL}/documents.json"
    params = {
        "date": date,
        "type": "2",  # 提出書類一覧及びメタデータ
        "Subscription-Key": api_key
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

# 使用例
date = "2023-04-03"
data = get_document_list(date, API_KEY)

print(f"件数: {data['metadata']['resultset']['count']}")
for doc in data['results']:
    print(f"{doc['docID']}: {doc['filerName']} - {doc['docDescription']}")
```

#### 実践的な実装（エラーハンドリング含む）

```python
import requests
import os
from typing import Optional, Dict, Any
from pathlib import Path

class EDINETClient:
    """EDINET API クライアント"""

    BASE_URL = "https://api.edinet-fsa.go.jp/api/v2"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()

    def get_document_list(self, date: str, include_details: bool = True) -> Dict[str, Any]:
        """
        書類一覧を取得

        Args:
            date: ファイル日付（YYYY-MM-DD形式）
            include_details: 提出書類一覧を含むか（Falseの場合メタデータのみ）

        Returns:
            書類一覧のJSON

        Raises:
            requests.HTTPError: APIエラー
        """
        url = f"{self.BASE_URL}/documents.json"
        params = {
            "date": date,
            "type": "2" if include_details else "1",
            "Subscription-Key": self.api_key
        }

        response = self.session.get(url, params=params, timeout=30)

        # ステータスコードのチェック
        if response.status_code == 200:
            data = response.json()
            # EDINET独自のステータスコードをチェック
            if data['metadata']['status'] != '200':
                raise ValueError(
                    f"EDINET API Error: {data['metadata']['status']} - "
                    f"{data['metadata']['message']}"
                )
            return data
        else:
            response.raise_for_status()

    def download_document(
        self,
        doc_id: str,
        doc_type: int = 1,
        save_path: Optional[Path] = None
    ) -> bytes:
        """
        書類をダウンロード

        Args:
            doc_id: 書類管理番号
            doc_type: 1=本文書, 2=PDF, 3=添付文書, 4=英文, 5=CSV
            save_path: 保存先パス（指定しない場合はバイト列を返す）

        Returns:
            書類データ（バイト列）
        """
        url = f"{self.BASE_URL}/documents/{doc_id}"
        params = {
            "type": str(doc_type),
            "Subscription-Key": self.api_key
        }

        response = self.session.get(url, params=params, timeout=60)

        # Content-Typeでエラーチェック
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            # エラーレスポンス
            error_data = response.json()
            raise ValueError(
                f"Document download failed: {error_data.get('message', 'Unknown error')}"
            )

        response.raise_for_status()

        # ファイル保存
        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(response.content)

        return response.content

    def get_latest_documents(self, date: str, doc_type_code: Optional[str] = None):
        """
        指定日の書類一覧を取得し、フィルタリング

        Args:
            date: ファイル日付（YYYY-MM-DD形式）
            doc_type_code: 書類種別コード（例: "120"=有価証券報告書）

        Returns:
            フィルタリングされた書類リスト
        """
        data = self.get_document_list(date, include_details=True)
        documents = data['results']

        if doc_type_code:
            documents = [
                doc for doc in documents
                if doc['docTypeCode'] == doc_type_code
            ]

        return documents


# 使用例
if __name__ == "__main__":
    # クライアント初期化
    client = EDINETClient(api_key="YOUR_API_KEY")

    # 2023年4月3日の有価証券報告書を検索
    docs = client.get_latest_documents(
        date="2023-04-03",
        doc_type_code="120"  # 有価証券報告書
    )

    for doc in docs:
        print(f"{doc['filerName']}: {doc['docDescription']}")

        # PDF有無をチェック
        if doc['pdfFlag'] == '1':
            # PDFをダウンロード
            save_path = Path(f"downloads/{doc['docID']}.pdf")
            client.download_document(
                doc_id=doc['docID'],
                doc_type=2,  # PDF
                save_path=save_path
            )
            print(f"  → PDF saved to {save_path}")
```

### データの増分取得（当日分の効率的な取得）

```python
def get_incremental_documents(client: EDINETClient, date: str, last_seq_number: int = 0):
    """
    前回取得以降の新規書類のみを取得

    Args:
        client: EDINETクライアント
        date: ファイル日付
        last_seq_number: 前回取得時の最終連番

    Returns:
        新規書類のリスト
    """
    data = client.get_document_list(date, include_details=True)

    # 連番が前回より大きいものだけを抽出
    new_documents = [
        doc for doc in data['results']
        if doc['seqNumber'] > last_seq_number
    ]

    return new_documents, data['metadata']['resultset']['count']


# 使用例: 定期実行で新規書類を監視
last_count = 0
last_seq = 0

while True:
    # メタデータで件数確認
    metadata = client.get_document_list("2023-04-03", include_details=False)
    current_count = metadata['metadata']['resultset']['count']

    # 件数が増えていれば詳細取得
    if current_count > last_count:
        new_docs, total = get_incremental_documents(client, "2023-04-03", last_seq)

        for doc in new_docs:
            print(f"新規: {doc['filerName']} - {doc['docDescription']}")
            last_seq = max(last_seq, doc['seqNumber'])

        last_count = total

    # 1分待機（APIは1分毎に更新）
    time.sleep(60)
```

## 制限事項・注意点

| 制限項目 | 内容 | 対処法 |
|----------|------|--------|
| **クロスドメイン通信** | ブラウザJavaScriptから直接呼び出し不可 | サーバーサイドでAPI呼び出しを実装 |
| **データ取得期間** | 当日以前で直近の財務局営業日の24時において10年を経過していない日付まで | 過去10年以内のデータのみ取得可能 |
| **レート制限** | 明示的な記載なし（ただし、過度なリクエストは避ける） | 適切な間隔でリクエスト（1分毎の更新に合わせる） |
| **APIキーの管理** | APIキーは再発行可能だが、削除すると即座に無効化 | APIキーは環境変数等で安全に管理 |
| **HTTPステータスコード** | API内部エラーでもHTTPステータスは200 | レスポンスのContent-Typeとステータスフィールドを確認 |
| **EDINETコードの変更** | 提出者情報は提出時点のものが記録される | 最新情報が必要な場合はEDINETコードリストを参照 |
| **書類の取下げ** | 取下げられた書類は非表示だが情報は残る | withdrawalStatusフラグで判定 |
| **閲覧期間満了** | 期間満了の書類は自動的に一覧から削除 | 定期的にバックアップ取得を推奨 |

### セキュリティ上の注意

- **APIキーの露出防止**: ソースコードに直接記述せず、環境変数や設定ファイルで管理
- **HTTPS通信**: TLS 1.2以上を使用（古いライブラリでは接続できない可能性）
- **多要素認証**: APIキー発行画面では多要素認証が有効（電話番号登録）

## トラブルシューティング

### よくある問題1: APIキーエラー（401 Unauthorized）

**症状**: 以下のいずれかの形式でエラーが返却される

形式1（トップレベル）:
```json
{
  "statusCode": 401,
  "message": "Access denied due to invalid subscription key..."
}
```

形式2（メタデータ内）:
```json
{
  "metadata": {
    "status": "401",
    "message": "Access denied..."
  }
}
```

**原因**:
- APIキーが誤っている
- APIキーがリクエストに含まれていない
- APIキーが削除された
- サブスクリプションが無効

**解決策**:
1. `.env`ファイルに`EDINET_API_KEY`が正しく設定されているか確認
2. APIキー発行画面で正しいキーを確認
3. パラメータ名が`Subscription-Key`であることを確認（大文字小文字区別あり）
4. 必要に応じてAPIキーを再発行

### よくある問題2: データが取得できない（404 Not Found）

**症状**:
```json
{
  "metadata": {
    "status": "404",
    "message": "Not Found"
  }
}
```

**原因**:
- 指定した日付にデータが存在しない
- 書類管理番号が誤っている
- 閲覧期間が満了している

**解決策**:
1. 日付フォーマットが`YYYY-MM-DD`形式であることを確認
2. 土日祝日でもデータがあれば取得可能（財務局営業日でなくても可）
3. 書類管理番号は書類一覧APIから取得したものを使用

### よくある問題3: ZIPファイルの解凍エラー

**症状**: ダウンロードしたZIPファイルが壊れている

**原因**:
- レスポンスをテキストとして処理してしまった
- エラーレスポンス（JSON）をZIPとして保存した

**解決策**:
```python
# Content-Typeを必ず確認
content_type = response.headers.get('Content-Type', '')
if 'application/json' in content_type:
    # エラー処理
    error_data = response.json()
    print(f"Error: {error_data['message']}")
else:
    # バイナリデータとして保存
    with open('document.zip', 'wb') as f:
        f.write(response.content)
```

### よくある問題4: 提出者情報が古い

**症状**: 書類一覧APIで取得した証券コードや提出者名が最新ではない

**原因**: 提出書類一覧の情報は提出時点のものが記録される

**解決策**:
- 最新情報が必要な場合はEDINETコードリストを参照
  - https://disclosure2dl.edinet-fsa.go.jp/searchdocument/codelist/Edinetcode.zip
- EDINETコードをキーに最新の属性情報を取得

## 参考リソース

### 公式ドキュメント
- [EDINET トップページ](https://disclosure2.edinet-fsa.go.jp/) - EDINET閲覧サイト
- [EDINET API 仕様書](https://disclosure2.edinet-fsa.go.jp/weee0010.aspx) - 公式仕様書（PDF）
- [利用規約](https://disclosure2dl.edinet-fsa.go.jp/guide/static/disclosure/WZEK0030.html) - EDINET API利用規約

### コードリスト・参照データ
- [EDINETコードリスト](https://disclosure2dl.edinet-fsa.go.jp/searchdocument/codelist/Edinetcode.zip) - 提出者情報（日本語）
- [ファンドコードリスト](https://disclosure2dl.edinet-fsa.go.jp/searchdocument/codelist/Fundcode.zip) - ファンド情報
- [EDINETコード集約一覧](https://disclosure2dl.edinet-fsa.go.jp/guide/static/disclosure/download/ESE140190.csv) - EDINETコード変更履歴

### 書類種別コード（主要なもの）

| コード値 | 書類種別 |
|---------|---------|
| 120 | 有価証券報告書 |
| 130 | 訂正有価証券報告書 |
| 140 | 四半期報告書 |
| 150 | 訂正四半期報告書 |
| 160 | 半期報告書 |
| 170 | 訂正半期報告書 |
| 180 | 臨時報告書 |
| 190 | 訂正臨時報告書 |
| 350 | 大量保有報告書 |
| 360 | 訂正大量保有報告書 |

詳細は仕様書の別紙1「様式コードリスト」を参照。

### 府令コード

| コード値 | 府令名 |
|---------|--------|
| 010 | 企業内容等の開示に関する内閣府令 |
| 030 | 特定有価証券の内容等の開示に関する内閣府令 |
| 040 | 発行者以外の者による株券等の公開買付けの開示に関する内閣府令 |
| 060 | 株券等の大量保有の状況の開示に関する内閣府令 |

## 実装時のベストプラクティス

### 1. エラーハンドリング
- HTTPステータスだけでなく、レスポンスの`metadata.status`も確認
- Content-Typeを確認してからデータを処理

### 2. パフォーマンス最適化
- メタデータ（type=1）で件数確認してから詳細取得（type=2）
- 増分取得時は`seqNumber`を活用
- セッション（requests.Session）を使い回す

### 3. データ管理
- 書類管理番号（docID）をプライマリキーとして管理
- 取下げ・訂正・不開示のフラグを適切に処理
- 定期的にEDINETコードリストを更新

### 4. 運用設計
- 8:30以降の定期実行（1分〜数分間隔）
- リトライ処理の実装（500エラー時など）
- ログ記録とモニタリング

---

**調査日**: 2026年01月16日
**仕様書バージョン**: EDINET API 仕様書 Version 2（2025年10月版）
**対象API**: EDINET API v2
