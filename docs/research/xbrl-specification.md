# EDINET XBRL仕様 調査レポート

## 概要
EDINETは金融庁が運営する有価証券報告書等の電子開示システムであり、2013年からXBRL（eXtensible Business Reporting Language）を用いた財務諸表の開示が行われています。本レポートでは、EDINETのXBRL仕様を調査し、財務諸表データ（BS/PL/CF）の自動抽出に必要な技術情報を体系的にまとめます。

## 基本情報
| 項目 | 内容 |
|------|------|
| 公式サイト | [EDINET（金融庁）](https://disclosure2dl.edinet-fsa.go.jp/) |
| タクソノミ公開 | [EDINETタクソノミ一覧](https://www.fsa.go.jp/search/EDINET_Taxonomy_All.html) |
| 最新バージョン | 2025年版（2024年11月公表） |
| 適用開始 | 2025年3月31日以後終了事業年度から |
| 主要ドキュメント | [EDINETタクソノミ概要説明](https://www.fsa.go.jp/search/20241112/1b-1_GaiyoSetsumei.pdf) |

---

## 1. XBRLとEDINETタクソノミの基本

### 1-1. XBRLとは

**XBRL（eXtensible Business Reporting Language）**は、財務報告等の開示書類に電子的タグを付与し、効率的な情報取得を可能とする国際標準化されたコンピュータ言語です。XMLをベースとしており、以下の特徴があります：

- **構造化データ**: 財務情報が機械可読な形式で記述される
- **標準化**: 国際的に統一されたタクソノミ（電子タグの集合）を使用
- **高度な分析**: プログラムによる自動抽出・加工・分析が可能

### 1-2. タクソノミとインスタンス

XBRLは以下の2つの主要構成要素から成ります：

| 要素 | 説明 |
|------|------|
| **タクソノミ** | 電子的タグの定義集。勘定科目名、データ型、計算式などを定義 |
| **インスタンス** | タクソノミを用いて実際にタグ付けされた財務諸表ファイル |

### 1-3. インラインXBRL（iXBRL）

**インラインXBRL**は、XBRLインスタンスのタグ付きデータをXHTML（Extensible HyperText Markup Language）ファイルに直接埋め込む仕様です。

**特徴**:
- Webブラウザで表示可能
- 人間にとっての可読性と機械処理の両立
- EDINET は 2013年9月からインラインXBRLを採用

---

## 2. EDINETタクソノミの構造

### 2-1. タクソノミの構成

EDINETタクソノミは以下の4つのタクソノミで構成されています：

| タクソノミ名 | 説明 | 名前空間プレフィックス |
|-------------|------|----------------------|
| **DEIタクソノミ** | 提出書類の基本情報と開示書類等提出者の基本情報 | `jpdei` |
| **財務諸表本表タクソノミ** | 貸借対照表、損益計算書、キャッシュフロー計算書等の財務諸表本表 | `jppfs` |
| **内閣府令タクソノミ** | 有価証券報告書、四半期報告書等の財務諸表以外の項目 | `jpcrp` |
| **国際会計基準タクソノミ** | IFRS適用企業向けの財務諸表 | `jpigp` |

### 2-2. 名前空間の命名規則

XBRL要素は**名前空間プレフィックス**と**要素名**を組み合わせて表現されます：

```xml
jppfs_cor:NotesAndAccountsReceivableTrade
```

- `jppfs_cor`: 名前空間プレフィックス（財務諸表タクソノミ）
- `NotesAndAccountsReceivableTrade`: 要素名（売掛金）

**主要な名前空間プレフィックス**:
- `jppfs_cor`: 財務諸表本表タクソノミ（日本基準）
- `jpcrp_cor`: 内閣府令タクソノミ
- `jpdei_cor`: DEIタクソノミ
- `jpigp_cor`: 国際会計基準タクソノミ（IFRS）

### 2-3. 勘定科目コードの体系

貸借対照表及び損益計算書では、約6,400の勘定科目が業種・区分ごとに分類されています：

**コード構造**（9桁の英数字）:
```
業種番号（2桁） + 区分番号（3桁） + 整数（4桁）
```

---

## 3. 財務諸表項目のマッピング

### 3-1. 貸借対照表（BS）の主要項目

| 勘定科目（日本語） | 要素名（英語） | 備考 |
|------------------|---------------|------|
| 資産合計 | `Assets` | 連結・単体で共通 |
| 流動資産 | `CurrentAssets` | |
| 現金及び預金 | `CashAndDeposits` | |
| 受取手形及び売掛金 | `NotesAndAccountsReceivableTrade` | |
| 商品及び製品 | `MerchandiseAndFinishedGoods` | |
| 固定資産 | `NoncurrentAssets` | |
| 有形固定資産 | `PropertyPlantAndEquipment` | |
| 無形固定資産 | `IntangibleAssets` | |
| 投資その他の資産 | `InvestmentsAndOtherAssets` | |
| 負債合計 | `Liabilities` | |
| 流動負債 | `CurrentLiabilities` | |
| 支払手形及び買掛金 | `NotesAndAccountsPayableTrade` | |
| 短期借入金 | `ShortTermLoansPayable` | |
| 固定負債 | `NoncurrentLiabilities` | |
| 長期借入金 | `LongTermLoansPayable` | |
| 純資産合計 | `NetAssets` | 日本基準 |
| 資本金 | `CapitalStock` | |
| 利益剰余金 | `RetainedEarnings` | |

### 3-2. 損益計算書（PL）の主要項目

| 勘定科目（日本語） | 要素名（英語） | 備考 |
|------------------|---------------|------|
| 売上高 | `NetSales` | 日本基準（単体） |
| 売上収益 | `Revenue` | IFRS |
| 営業収益 | `OperatingRevenue` | 業種により使用 |
| 売上原価 | `CostOfSales` | |
| 売上総利益 | `GrossProfit` | |
| 販売費及び一般管理費 | `SellingGeneralAndAdministrativeExpenses` | |
| 営業利益 | `OperatingIncome` | |
| 営業外収益 | `NonOperatingIncome` | |
| 営業外費用 | `NonOperatingExpenses` | |
| 経常利益 | `OrdinaryIncome` | 日本基準特有 |
| 特別利益 | `ExtraordinaryIncome` | |
| 特別損失 | `ExtraordinaryLoss` | |
| 税金等調整前当期純利益 | `ProfitLossBeforeIncomeTaxes` | |
| 法人税、住民税及び事業税 | `IncomeTaxes` | |
| 当期純利益 | `NetIncome` | |

### 3-3. キャッシュフロー計算書（CF）の主要項目

| 勘定科目（日本語） | 要素名（英語） | 備考 |
|------------------|---------------|------|
| 営業活動によるキャッシュフロー | `NetCashProvidedByUsedInOperatingActivities` | |
| 税金等調整前当期純利益 | `ProfitLossBeforeIncomeTaxes` | |
| 減価償却費 | `DepreciationAndAmortization` | |
| 投資活動によるキャッシュフロー | `NetCashProvidedByUsedInInvestmentActivities` | |
| 有形固定資産の取得による支出 | `PurchaseOfPropertyPlantAndEquipment` | |
| 財務活動によるキャッシュフロー | `NetCashProvidedByUsedInFinancingActivities` | |
| 短期借入金の純増減額 | `NetIncreaseDecreaseInShortTermLoansPayable` | |
| 長期借入れによる収入 | `ProceedsFromLongTermLoansPayable` | |
| 配当金の支払額 | `CashDividendsPaid` | |
| 現金及び現金同等物の期末残高 | `CashAndCashEquivalentsEndOfPeriod` | |

**注意**:
- 要素名は会社や会計基準（日本基準/IFRS）により異なる場合があります
- 完全な要素名には名前空間プレフィックス（`jppfs_cor:`等）が必要です

---

## 4. コンテキストの指定方法

### 4-1. コンテキストとは

XBRLの各要素（fact）には、その値が**いつ**の**どの財務諸表**の値かを示す**コンテキスト**が関連付けられています。

### 4-2. コンテキストの構成要素

コンテキストは以下の3つの要素で構成されます：

| 要素 | 説明 |
|------|------|
| **Entity（実体）** | 報告企業の識別情報 |
| **Period（期間）** | 時点（instant）または期間（duration） |
| **Scenario（シナリオ）** | ディメンション情報（連結/単体、当期/前期など） |

### 4-3. 期間の指定

**期間（Duration）**:
```xml
<xbrli:period>
  <xbrli:startDate>2024-04-01</xbrli:startDate>
  <xbrli:endDate>2025-03-31</xbrli:endDate>
</xbrli:period>
```

**時点（Instant）**:
```xml
<xbrli:period>
  <xbrli:instant>2025-03-31</xbrli:instant>
</xbrli:period>
```

### 4-4. 連結・単体の指定

連結/単体の区分は**ディメンション**により指定されます：

```xml
<xbrldi:explicitMember dimension="jppfs_cor:ConsolidatedOrNonConsolidatedAxis">
  jppfs_cor:NonConsolidatedMember
</xbrldi:explicitMember>
```

- **連結**: ディメンション指定なし（デフォルト）
- **単体**: `jppfs_cor:NonConsolidatedMember`を明示的に設定

### 4-5. コンテキストIDの命名規則

コンテキストには命名規則があります：

**命名例**:
- `CurrentYearDuration`: 当期（期間）
- `CurrentYearDuration_NonConsolidatedMember`: 当期単体（期間）
- `CurrentYearInstant`: 当期末時点
- `PriorYearDuration`: 前期（期間）

---

## 5. インラインXBRLの構造

### 5-1. タグの種類

EDINETのインラインXBRLでは、2種類のタグが使用されます：

| タグ種別 | 用途 | 要素名 |
|---------|------|--------|
| **包括タグ** | 文章、表等の複数情報をまとめて囲む | `ix:nonNumeric` |
| **詳細タグ** | 個別の文字列、金額、数値等に付与 | `ix:nonFraction`（数値）<br>`ix:nonNumeric`（文字列） |

### 5-2. 数値データの構造

**例**: 売上高のタグ付け

```xml
<ix:nonFraction
  name="jppfs_cor:NetSales"
  contextRef="CurrentYearDuration"
  unitRef="JPY"
  decimals="-6"
  format="ixt:num-dot-decimal">
  1,234,567
</ix:nonFraction>
```

**属性の意味**:
- `name`: XBRL要素名
- `contextRef`: コンテキストIDの参照
- `unitRef`: 単位（JPY、shares等）
- `decimals`: 精度（-6は百万円単位）
- `format`: 表示形式
- `scale`: スケール（負数処理）

### 5-3. 財務諸表区分の識別

財務諸表の区分は、包括タグの要素名により識別できます：

| 財務諸表 | 要素名パターン |
|---------|---------------|
| 貸借対照表（連結） | `jpcrp_cor:ConsolidatedBalanceSheetTextBlock` |
| 貸借対照表（単体） | `jpcrp_cor:BalanceSheetTextBlock` |
| 損益計算書（連結） | `jpcrp_cor:ConsolidatedStatementOfIncomeTextBlock` |
| 損益計算書（単体） | `jpcrp_cor:StatementOfIncomeTextBlock` |
| キャッシュフロー計算書 | `jpcrp_cor:ConsolidatedStatementOfCashFlowsTextBlock` |

---

## 6. Python向けXBRL解析ライブラリ

### 6-1. ライブラリ比較

| ライブラリ | メンテナンス状況 | EDINET対応 | 複雑性 | 推奨用途 |
|-----------|----------------|-----------|--------|---------|
| **Arelle** | ◎ 活発 | ◎ 対応 | 高 | 本格的なXBRL解析、バリデーション |
| **edinet-xbrl** | ○ 更新あり | ◎ 専用設計 | 低 | EDINETからのダウンロードとパース |
| **BeautifulSoup + lxml** | ◎ 活発 | △ 自前実装 | 中 | 軽量な解析、カスタム実装 |

### 6-2. Arelle

**公式サイト**: [https://arelle.org/](https://arelle.org/)
**GitHub**: [https://github.com/Arelle/Arelle](https://github.com/Arelle/Arelle)
**PyPI**: [arelle-release](https://pypi.org/project/arelle-release/)

**特徴**:
- XBRL Certified Softwareを保有するOSS
- Apache License 2.0
- EDINET専用の処理機能を内蔵
- 親子関係、計算関係などの高度な解析が可能
- デスクトップアプリケーション、Web API、コマンドライン、Python APIとして利用可能

**メリット**:
- 国際標準に準拠した堅牢な実装
- 世界50以上の規制当局・銀行・技術企業が利用
- インラインXBRLの自動変換機能

**デメリット**:
- 学習曲線が急（複雑な仕様）
- 日本のインラインXBRLで一部エラーが発生する場合がある

**基本的な使い方**:
```python
from arelle import Cntlr, ModelManager

# コントローラ作成
ctrl = Cntlr.Cntlr(logFileName='logToPrint')
modelManager = ModelManager.initialize(ctrl)

# XBRLファイル読み込み
modelXbrl = modelManager.load(xbrl_file_path)

# Factデータの取得
for fact in modelXbrl.facts:
    concept = fact.concept  # 要素情報
    context = fact.context  # コンテキスト（期間、ディメンション）
    unit = fact.unit        # 単位
    value = fact.value      # 値
```

### 6-3. edinet-xbrl

**GitHub**: [https://github.com/BuffettCode/edinet_xbrl](https://github.com/BuffettCode/edinet_xbrl)
**PyPI**: [edinet-xbrl](https://pypi.org/project/edinet-xbrl/)

**特徴**:
- EDINET専用のダウンロード&パーサー
- BuffettCodeが開発・メンテナンス
- EDINET API との統合が容易

**メリット**:
- EDINETに特化しているため、使い方がシンプル
- EDINET API からの自動ダウンロード機能
- 日本企業の財務データ取得に最適化

**デメリット**:
- EDINET以外のXBRLには対応していない
- 高度なXBRL仕様（計算リンク等）の解析は限定的

**基本的な使い方**:
```python
from edinet_xbrl import EdinetXbrl

# XBRLファイルの解析
xbrl = EdinetXbrl('path/to/xbrl_file.xbrl')

# 財務データの取得
accounts = xbrl.get_account_data()
```

### 6-4. BeautifulSoup + lxml

**特徴**:
- Python標準的なXML/HTMLパーサー
- 自由度の高いカスタム実装が可能

**メリット**:
- 軽量で高速
- 特定の要素だけ抽出する場合に最適
- XPath、CSSセレクタが使える
- 名前空間の扱いが柔軟

**デメリット**:
- XBRL仕様の深い理解が必要
- 計算リンク、ラベルリンク等の高度な機能は自前実装
- タグ名が100文字を超えると切り捨てられる（BeautifulSoupの制限）

**基本的な使い方**:
```python
from bs4 import BeautifulSoup

# インラインXBRLの読み込み
with open('xbrl_file.htm', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'lxml')

# 数値データの抽出
for tag in soup.find_all('ix:nonfraction'):
    element_name = tag.get('name')
    context_ref = tag.get('contextRef')
    value = tag.get_text()
```

### 6-5. 推奨アプローチ

**用途別推奨**:

| 用途 | 推奨ライブラリ | 理由 |
|------|--------------|------|
| 特定の勘定科目のみ取得 | BeautifulSoup + lxml | 軽量で高速、カスタマイズ性高 |
| 財務三表の体系的な取得 | edinet-xbrl | EDINET特化、実装が簡単 |
| 本格的なXBRL解析・検証 | Arelle | 国際標準準拠、高度な機能 |
| 海外XBRLとの互換性 | Arelle | 多国籍対応 |

---

## 7. 実装アプローチ

### 7-1. 推奨する実装方法

#### ステップ1: ライブラリ選定

**初期実装（PoC）**:
- **BeautifulSoup + lxml**を使った軽量実装
- 主要な財務項目（売上高、営業利益、総資産等）の抽出をテスト
- 複数企業で動作確認

**本番実装**:
- 動作が安定し、拡張性が必要になった段階で**edinet-xbrl**または**Arelle**に移行
- エラーハンドリング、ロギング、データベース保存を実装

#### ステップ2: データ取得フロー

```
1. EDINET API → 書類一覧取得
2. 対象書類の絞り込み（有価証券報告書、決算期など）
3. 書類取得API → XBRLファイルダウンロード
4. ZIPファイル解凍 → インラインXBRLファイル抽出
5. XBRLパーサー → 財務データ抽出
6. データクレンジング → データベース保存
```

#### ステップ3: データ抽出の実装パターン

**パターンA: 要素名直接指定**

```python
# 売上高を取得
net_sales_tags = soup.find_all('ix:nonfraction', attrs={'name': 'jppfs_cor:NetSales'})
for tag in net_sales_tags:
    context_ref = tag.get('contextRef')
    if 'CurrentYearDuration' in context_ref:
        value = tag.get_text().replace(',', '')
```

**パターンB: コンテキスト条件絞り込み**

```python
# 当期・連結の財務データのみ抽出
for tag in soup.find_all('ix:nonfraction'):
    context_ref = tag.get('contextRef')
    if 'CurrentYear' in context_ref and 'NonConsolidated' not in context_ref:
        element_name = tag.get('name')
        value = tag.get_text()
```

**パターンC: 財務諸表区分で絞り込み**

```python
# 貸借対照表内の要素のみ取得
bs_block = soup.find('ix:nonnumeric', attrs={'name': 'jpcrp_cor:ConsolidatedBalanceSheetTextBlock'})
if bs_block:
    for tag in bs_block.find_all('ix:nonfraction'):
        element_name = tag.get('name')
        value = tag.get_text()
```

### 7-2. エラーハンドリング

**主要なエラーケース**:

| エラー種別 | 原因 | 対処法 |
|----------|------|--------|
| 要素名が見つからない | 会計基準・業種により要素名が異なる | 複数の要素名候補を試行 |
| コンテキストIDが想定外 | 企業により命名規則が微妙に異なる | 正規表現による柔軟なマッチング |
| 値がnull | データが存在しない項目 | デフォルト値（0またはNone）を設定 |
| スケール・decimals処理 | 金額の単位変換が必要 | 属性値を読み取り自動変換 |

**実装例**:
```python
def get_financial_value(soup, element_candidates, context_pattern):
    """
    複数の要素名候補から値を取得
    """
    for element_name in element_candidates:
        tags = soup.find_all('ix:nonfraction', attrs={'name': element_name})
        for tag in tags:
            context_ref = tag.get('contextRef', '')
            if re.search(context_pattern, context_ref):
                value = tag.get_text().replace(',', '')
                scale = int(tag.get('scale', 0))
                return float(value) * (10 ** scale)
    return None

# 使用例: 売上高を取得（日本基準またはIFRS）
net_sales = get_financial_value(
    soup,
    element_candidates=['jppfs_cor:NetSales', 'jppfs_cor:Revenue', 'jpigp_cor:Revenue'],
    context_pattern=r'CurrentYear.*Duration'
)
```

### 7-3. データクレンジング

**必須のクレンジング処理**:
1. **カンマ除去**: `1,234,567` → `1234567`
2. **スケール変換**: `scale="-6"`の場合、値を10^(-6)倍
3. **負数処理**: `sign="-"`の場合、値を負数に変換
4. **単位統一**: 千円、百万円、円単位の統一
5. **NULL処理**: 欠損値の適切なハンドリング

---

## 8. 制限事項・注意点

### 8-1. データ取得の制約

| 制約項目 | 内容 | 対処法 |
|---------|------|--------|
| **過去データ期間** | 有価証券報告書は10年前まで | 過去データは別途収集が必要 |
| **APIレート制限** | 大量取得時の制限あり | 段階的ダウンロード、待機時間挿入 |
| **提出日ベース検索** | 銘柄コードでの事前フィルタ不可 | 全件取得後にフィルタリング |
| **取下げ書類** | 一度開示された書類が非開示になる場合あり | 取下区分のチェック |

### 8-2. データの不完全性

**主要な課題**:

1. **要素名の不統一**
   - 業種により勘定科目名が異なる（例: 売上高 vs 営業収益）
   - 日本基準とIFRSで要素名が異なる
   - 連結と単体で要素の有無が異なる

2. **企業・年度による構造の違い**
   - XBRLの構造が企業や年度により微妙に異なる
   - コンテキストIDの命名規則が企業により異なる

3. **非財務データのタグ不足**
   - 財務データに比べ、非財務データではタグが不十分な場合が多い

4. **タグ付けの精度**
   - 企業により詳細タグの付与レベルが異なる
   - 包括タグのみで詳細タグがない場合がある

### 8-3. ライセンス・利用規約

| 項目 | 内容 |
|------|------|
| **EDINET利用規約** | 金融庁の利用規約に従う必要がある |
| **APIキー** | API利用にはアカウント作成とAPIキー発行が必須 |
| **データの二次利用** | 商用利用の場合は規約を確認すること |

### 8-4. データ品質の確保

**推奨事項**:
- 複数企業でのテスト実施（最低10社以上）
- 異なる業種、会計基準でのバリデーション
- 公表されている決算短信との金額照合
- エラーログの詳細記録と分析
- 定期的なタクソノミ更新への対応

---

## 9. トラブルシューティング

### 9-1. よくある問題1: 要素が見つからない

**症状**:
特定の勘定科目のタグが見つからない

**原因**:
- 要素名が企業・会計基準により異なる
- 財務諸表に該当項目が存在しない

**解決策**:
```python
# 複数の要素名候補を用意
ELEMENT_CANDIDATES = {
    'net_sales': [
        'jppfs_cor:NetSales',           # 日本基準・単体
        'jppfs_cor:Revenue',            # 日本基準・一部企業
        'jpigp_cor:Revenue',            # IFRS
        'jppfs_cor:OperatingRevenue'    # 金融業等
    ]
}

# いずれかの要素名でマッチング
for candidate in ELEMENT_CANDIDATES['net_sales']:
    result = soup.find('ix:nonfraction', attrs={'name': candidate})
    if result:
        break
```

### 9-2. よくある問題2: 金額の単位が不正

**症状**:
取得した金額が実際の値と桁が異なる

**原因**:
- `scale`属性、`decimals`属性の未処理
- 単位（円、千円、百万円）の違い

**解決策**:
```python
def parse_numeric_value(tag):
    """
    ix:nonfractionタグから数値を正しく取得
    """
    value_text = tag.get_text().replace(',', '').strip()
    value = float(value_text)

    # scale属性の処理
    scale = tag.get('scale')
    if scale:
        value *= (10 ** int(scale))

    # sign属性の処理（負数）
    sign = tag.get('sign')
    if sign == '-':
        value *= -1

    return value
```

### 9-3. よくある問題3: コンテキストの判別ができない

**症状**:
当期・前期、連結・単体の判別が正しくできない

**原因**:
- コンテキストIDの命名規則が企業により異なる
- ディメンション情報の読み取り不足

**解決策**:
```python
def parse_context(soup, context_id):
    """
    コンテキストIDから期間とディメンションを解析
    """
    context_tag = soup.find('xbrli:context', attrs={'id': context_id})
    if not context_tag:
        return None

    # 期間の取得
    period = context_tag.find('xbrli:period')
    start_date = period.find('xbrli:startDate')
    end_date = period.find('xbrli:endDate')
    instant = period.find('xbrli:instant')

    # ディメンション（連結/単体）の取得
    scenario = context_tag.find('xbrli:scenario')
    is_consolidated = True
    if scenario:
        member = scenario.find('xbrldi:explicitMember')
        if member and 'NonConsolidated' in member.get_text():
            is_consolidated = False

    return {
        'start_date': start_date.get_text() if start_date else None,
        'end_date': end_date.get_text() if end_date else None,
        'instant': instant.get_text() if instant else None,
        'is_consolidated': is_consolidated
    }
```

### 9-4. よくある問題4: メモリ不足・処理が遅い

**症状**:
大量のXBRLファイルを処理する際にメモリ不足やパフォーマンス低下

**原因**:
- BeautifulSoupは大きなXMLファイルでメモリを大量消費
- 不要なデータも全てメモリに読み込んでいる

**解決策**:
```python
from lxml import etree

# lxml.etreeのiterparseを使用（逐次読み込み）
def parse_xbrl_iterative(file_path):
    """
    メモリ効率の良いXBRL解析
    """
    context = etree.iterparse(file_path, events=('end',), tag='{http://www.xbrl.org/2003/instance}context')

    for event, elem in context:
        # 必要な処理
        process_element(elem)

        # メモリ解放
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]
```

---

## 10. 参考リソース

### 10-1. 公式ドキュメント

- [金融庁 EDINET](https://disclosure2dl.edinet-fsa.go.jp/) - EDINET公式サイト
- [EDINETタクソノミ一覧](https://www.fsa.go.jp/search/EDINET_Taxonomy_All.html) - 最新タクソノミのダウンロード
- [2025年版EDINETタクソノミの公表について](https://www.fsa.go.jp/search/20241112.html) - 2025年版の公表情報
- [EDINETタクソノミ概要説明](https://www.fsa.go.jp/search/20241112/1b-1_GaiyoSetsumei.pdf) - タクソノミの詳細仕様
- [EDINETタクソノミ設定規約書](https://disclosure2dl.edinet-fsa.go.jp/guide/static/disclosure/download/ESE140124.pdf) - 技術仕様書

### 10-2. XBRL関連

- [XBRL Japan](https://www.xbrl.or.jp/) - XBRL Japanの公式サイト
- [XBRL International](https://www.xbrl.org/) - XBRL国際組織

### 10-3. Pythonライブラリ

- [Arelle公式サイト](https://arelle.org/) - Arelle公式ドキュメント
- [Arelle GitHub](https://github.com/Arelle/Arelle) - Arelleソースコード
- [edinet-xbrl PyPI](https://pypi.org/project/edinet-xbrl/) - edinet-xbrlパッケージ
- [edinet-xbrl GitHub](https://github.com/BuffettCode/edinet_xbrl) - edinet-xbrlソースコード

### 10-4. 実装例・チュートリアル

- [Beautiful SoupでEDINETのXBRLから財務諸表のデータベースを構築する](https://qiita.com/XBRLJapan/items/d23bc251c53d81d49852) - BeautifulSoupによる実装例
- [ゼロから始めないXBRL解析(Arelleの活用)](https://qiita.com/xtarou/items/fb3cc72b1b600b4309db) - Arelleによる実装例
- [まるっとわかるXBRL入門：(4) 財務諸表から売上高を自動で取得しよう](https://onto-logy.com/column/2096/) - XBRL入門チュートリアル
- [インラインXBRLの解析方法](https://lifetechia.com/inline-xbrl-analysis/) - インラインXBRL解析のガイド
- [財務分析に欠かせない、XBRLを理解する Part2](https://medium.com/programming-soda/財務分析に欠かせない-xbrlを理解する-part2-65e9243e9587) - XBRLコンテキストの解説

### 10-5. 技術資料

- [新EDINETの概要とXBRLデータに関する監査人の留意事項（日本公認会計士協会）](https://jicpa.or.jp/specialized_field/publication/files/2-10-44-2-20140418.pdf) - XBRL技術解説
- [提出者別タクソノミ作成要領（東京証券取引所）](https://www.jpx.co.jp/equities/listing/disclosure/xbrl/nlsgeu000005vk0b-att/TeisyutusyaTaxonomy_2025-01-31.pdf) - タクソノミ作成ガイド

---

## 11. 結論と推奨事項

### 11-1. 自前実装の必要性

**既存ライブラリの制約**:
- Arelle: 高機能だが複雑。日本のインラインXBRLで一部エラー発生
- edinet-xbrl: EDINET特化だが、カスタマイズ性に制約
- BeautifulSoup: 軽量だが、XBRL仕様の実装が必要

**推奨**:
- **初期段階**: BeautifulSoup + lxmlで軽量実装し、データ取得の実現可能性を検証
- **拡張段階**: edinet-xbrlまたはArelleをベースに、必要な機能を追加実装
- **本番運用**: エラーハンドリング、ロギング、データ品質チェックを強化

### 11-2. 実装の優先順位

**フェーズ1（PoC）**:
1. EDINET APIによる書類一覧・書類取得の実装
2. BeautifulSoupによる主要財務項目（売上高、営業利益、総資産等）の抽出
3. 10社程度でのテスト実施

**フェーズ2（本格実装）**:
1. 複数の要素名候補による柔軟な抽出ロジック
2. コンテキスト解析による当期/前期、連結/単体の判別
3. エラーハンドリングとロギングの実装
4. データベースへの保存機能

**フェーズ3（品質向上）**:
1. 100社以上での動作検証
2. 業種別、会計基準別のバリデーション
3. 決算短信との照合による品質チェック
4. 定期的なタクソノミ更新への対応

### 11-3. 最重要ポイント

1. **要素名の多様性を考慮する**: 1つの勘定科目に対して複数の要素名候補を用意
2. **コンテキストを正確に解析する**: 当期/前期、連結/単体の判別は必須
3. **エラーハンドリングを徹底する**: データが取得できない場合の処理を明確化
4. **段階的に実装する**: 一度に全機能を実装せず、段階的に拡張
5. **データ品質を継続的にチェックする**: 複数企業での検証とエラーログ分析

---

## 付録: 主要勘定科目の要素名一覧

### A. 貸借対照表（BS）

#### 資産の部

| 日本語 | 要素名 | 期間/時点 |
|--------|--------|----------|
| 資産合計 | `jppfs_cor:Assets` | Instant |
| 流動資産 | `jppfs_cor:CurrentAssets` | Instant |
| 現金及び預金 | `jppfs_cor:CashAndDeposits` | Instant |
| 受取手形 | `jppfs_cor:NotesReceivableTrade` | Instant |
| 売掛金 | `jppfs_cor:AccountsReceivableTrade` | Instant |
| 有価証券 | `jppfs_cor:Securities` | Instant |
| 商品 | `jppfs_cor:Merchandise` | Instant |
| 製品 | `jppfs_cor:FinishedGoods` | Instant |
| 原材料 | `jppfs_cor:RawMaterials` | Instant |
| 固定資産 | `jppfs_cor:NoncurrentAssets` | Instant |
| 有形固定資産 | `jppfs_cor:PropertyPlantAndEquipment` | Instant |
| 建物及び構築物 | `jppfs_cor:BuildingsAndStructures` | Instant |
| 機械装置及び運搬具 | `jppfs_cor:MachineryEquipmentAndVehicles` | Instant |
| 土地 | `jppfs_cor:Land` | Instant |
| 無形固定資産 | `jppfs_cor:IntangibleAssets` | Instant |
| のれん | `jppfs_cor:Goodwill` | Instant |
| 投資その他の資産 | `jppfs_cor:InvestmentsAndOtherAssets` | Instant |
| 投資有価証券 | `jppfs_cor:InvestmentSecurities` | Instant |

#### 負債の部

| 日本語 | 要素名 | 期間/時点 |
|--------|--------|----------|
| 負債合計 | `jppfs_cor:Liabilities` | Instant |
| 流動負債 | `jppfs_cor:CurrentLiabilities` | Instant |
| 支払手形 | `jppfs_cor:NotesPayableTrade` | Instant |
| 買掛金 | `jppfs_cor:AccountsPayableTrade` | Instant |
| 短期借入金 | `jppfs_cor:ShortTermLoansPayable` | Instant |
| 未払金 | `jppfs_cor:AccountsPayableOther` | Instant |
| 未払法人税等 | `jppfs_cor:IncomeTaxesPayable` | Instant |
| 固定負債 | `jppfs_cor:NoncurrentLiabilities` | Instant |
| 長期借入金 | `jppfs_cor:LongTermLoansPayable` | Instant |
| 社債 | `jppfs_cor:Bonds` | Instant |

#### 純資産の部

| 日本語 | 要素名 | 期間/時点 |
|--------|--------|----------|
| 純資産合計 | `jppfs_cor:NetAssets` | Instant |
| 株主資本 | `jppfs_cor:ShareholdersEquity` | Instant |
| 資本金 | `jppfs_cor:CapitalStock` | Instant |
| 資本剰余金 | `jppfs_cor:CapitalSurplus` | Instant |
| 利益剰余金 | `jppfs_cor:RetainedEarnings` | Instant |
| 自己株式 | `jppfs_cor:TreasuryStock` | Instant |

### B. 損益計算書（PL）

| 日本語 | 要素名 | 期間/時点 |
|--------|--------|----------|
| 売上高 | `jppfs_cor:NetSales` | Duration |
| 売上原価 | `jppfs_cor:CostOfSales` | Duration |
| 売上総利益 | `jppfs_cor:GrossProfit` | Duration |
| 販売費及び一般管理費 | `jppfs_cor:SellingGeneralAndAdministrativeExpenses` | Duration |
| 営業利益 | `jppfs_cor:OperatingIncome` | Duration |
| 営業外収益 | `jppfs_cor:NonOperatingIncome` | Duration |
| 受取利息 | `jppfs_cor:InterestIncome` | Duration |
| 受取配当金 | `jppfs_cor:DividendIncome` | Duration |
| 営業外費用 | `jppfs_cor:NonOperatingExpenses` | Duration |
| 支払利息 | `jppfs_cor:InterestExpenses` | Duration |
| 経常利益 | `jppfs_cor:OrdinaryIncome` | Duration |
| 特別利益 | `jppfs_cor:ExtraordinaryIncome` | Duration |
| 固定資産売却益 | `jppfs_cor:GainOnSalesOfNoncurrentAssets` | Duration |
| 特別損失 | `jppfs_cor:ExtraordinaryLoss` | Duration |
| 固定資産売却損 | `jppfs_cor:LossOnSalesOfNoncurrentAssets` | Duration |
| 減損損失 | `jppfs_cor:ImpairmentLoss` | Duration |
| 税金等調整前当期純利益 | `jppfs_cor:ProfitLossBeforeIncomeTaxes` | Duration |
| 法人税、住民税及び事業税 | `jppfs_cor:IncomeTaxes` | Duration |
| 法人税等調整額 | `jppfs_cor:IncomeTaxesAdjustments` | Duration |
| 当期純利益 | `jppfs_cor:NetIncome` | Duration |

### C. キャッシュフロー計算書（CF）

| 日本語 | 要素名 | 期間/時点 |
|--------|--------|----------|
| 営業活動によるキャッシュフロー | `jppfs_cor:NetCashProvidedByUsedInOperatingActivities` | Duration |
| 税金等調整前当期純利益 | `jppfs_cor:ProfitLossBeforeIncomeTaxes` | Duration |
| 減価償却費 | `jppfs_cor:DepreciationAndAmortization` | Duration |
| 売上債権の増減額 | `jppfs_cor:IncreaseDecreaseInNotesAndAccountsReceivableTrade` | Duration |
| 棚卸資産の増減額 | `jppfs_cor:IncreaseDecreaseInInventories` | Duration |
| 仕入債務の増減額 | `jppfs_cor:IncreaseDecreaseInNotesAndAccountsPayableTrade` | Duration |
| 投資活動によるキャッシュフロー | `jppfs_cor:NetCashProvidedByUsedInInvestmentActivities` | Duration |
| 有形固定資産の取得による支出 | `jppfs_cor:PurchaseOfPropertyPlantAndEquipment` | Duration |
| 有形固定資産の売却による収入 | `jppfs_cor:ProceedsFromSalesOfPropertyPlantAndEquipment` | Duration |
| 投資有価証券の取得による支出 | `jppfs_cor:PurchaseOfInvestmentSecurities` | Duration |
| 財務活動によるキャッシュフロー | `jppfs_cor:NetCashProvidedByUsedInFinancingActivities` | Duration |
| 短期借入金の純増減額 | `jppfs_cor:NetIncreaseDecreaseInShortTermLoansPayable` | Duration |
| 長期借入れによる収入 | `jppfs_cor:ProceedsFromLongTermLoansPayable` | Duration |
| 長期借入金の返済による支出 | `jppfs_cor:RepaymentsOfLongTermLoansPayable` | Duration |
| 配当金の支払額 | `jppfs_cor:CashDividendsPaid` | Duration |
| 現金及び現金同等物の増減額 | `jppfs_cor:IncreaseDecreaseInCashAndCashEquivalents` | Duration |
| 現金及び現金同等物の期首残高 | `jppfs_cor:CashAndCashEquivalentsBeginningOfPeriod` | Instant |
| 現金及び現金同等物の期末残高 | `jppfs_cor:CashAndCashEquivalentsEndOfPeriod` | Instant |

**注意事項**:
- 上記は日本基準（連結）の要素名です
- 単体財務諸表の場合も多くは同じ要素名ですが、一部異なる場合があります
- IFRS適用企業の場合、名前空間が`jpigp_cor:`となり、要素名も異なります
- 企業により使用する要素名が異なる場合があるため、複数候補を試行する必要があります

---

**作成日**: 2026年1月16日
**対象バージョン**: EDINET 2025年版タクソノミ
**調査ツール**: Web検索、公式ドキュメント、技術記事
