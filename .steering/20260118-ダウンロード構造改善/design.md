# 設計書: ダウンロード構造改善

## アーキテクチャ概要

```
┌─────────────────────────────────────────┐
│  QueryOrchestrator                      │
│  └─ ツール実行時に進捗表示              │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Tools                                  │
│  ├─ download_document (更新)            │
│  │   └─ DocumentMetadata受け取り        │
│  │   └─ キャッシュ優先検索              │
│  │   └─ 階層パスで保存                  │
│  └─ search_documents (進捗表示追加)     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Services                               │
│  └─ LocalCacheService (新規)            │
│      └─ ローカルファイル検索            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Core                                   │
│  ├─ logging.py (新規) - ログ設定        │
│  ├─ progress.py (新規) - 進捗表示       │
│  ├─ doc_type_mapping.py (新規)          │
│  └─ download_path.py (新規)             │
└─────────────────────────────────────────┘
```

## 新規ファイル

### 1. `core/logging.py`

```python
def setup_logging(level: str = "INFO") -> None:
    """アプリケーションのログ設定を初期化"""
```

### 2. `core/progress.py`

```python
from rich.console import Console
console = Console()

def print_status(message: str) -> None:
    """進捗メッセージを表示（青色）"""

def print_success(message: str) -> None:
    """成功メッセージを表示（緑色）"""

def print_error(message: str) -> None:
    """エラーメッセージを表示（赤色）"""
```

### 3. `core/doc_type_mapping.py`

```python
DOC_TYPE_NAMES: dict[str, str] = {
    "120": "有価証券報告書",
    "130": "訂正有価証券報告書",
    "140": "四半期報告書",
    ...
}

def get_doc_type_name(doc_type_code: str) -> str:
    """doc_type_codeから日本語名を取得"""
```

### 4. `core/download_path.py`

```python
def sanitize_filename(name: str) -> str:
    """ファイル名に使用できない文字を置換"""

def build_download_path(
    base_dir: Path,
    sec_code: str | None,
    filer_name: str | None,
    doc_type_code: str | None,
    period_end: str | None,
    doc_id: str,
) -> Path:
    """階層的なダウンロードパスを構築"""
```

### 5. `services/local_cache_service.py`

```python
class LocalCacheService:
    def find_document_by_doc_id(self, doc_id: str) -> Path | None:
        """doc_idでローカルファイルを検索"""
```

### 6. `schemas/cache_schemas.py`

```python
@dataclass
class CachedDocumentInfo:
    doc_id: str
    sec_code: str | None
    company_name: str | None
    doc_type_code: str | None
    period: str | None
    file_path: Path
```

## 変更ファイル

### 1. `tools/download_document.py`

- DocumentMetadataを引数に追加
- LocalCacheServiceでキャッシュ優先検索
- build_download_pathで階層パス生成
- 進捗表示追加

### 2. `pyproject.toml`

- `rich` 依存関係追加

### 3. `core/config.py`

- LoggingConfig追加（環境変数からログレベル取得）

## フォルダ構造

```
downloads/
├── 72030_トヨタ自動車/
│   ├── 120_有価証券報告書/
│   │   ├── 202412/
│   │   │   └── S100ABCD.pdf
│   │   └── 202312/
│   │       └── S100EFGH.pdf
│   └── 140_四半期報告書/
│       └── 202501/
│           └── S100IJKL.pdf
└── 99050_ソニーグループ/
    └── ...
```
