"""Document type code to Japanese name mapping."""

from __future__ import annotations

# EDINET書類種別コードと日本語名のマッピング
# 参照: EDINET API仕様書
DOC_TYPE_NAMES: dict[str, str] = {
    # 有価証券報告書関連
    "120": "有価証券報告書",
    "130": "訂正有価証券報告書",
    # 四半期報告書関連
    "140": "四半期報告書",
    "150": "訂正四半期報告書",
    # 半期報告書関連
    "160": "半期報告書",
    "170": "訂正半期報告書",
    # 臨時報告書関連
    "180": "臨時報告書",
    "190": "訂正臨時報告書",
    # 有価証券届出書関連
    "030": "有価証券届出書",
    "040": "訂正有価証券届出書",
    "050": "有価証券届出書（組込方式）",
    "060": "訂正有価証券届出書（組込方式）",
    # 大量保有報告書関連
    "360": "大量保有報告書",
    "370": "訂正大量保有報告書",
    "380": "変更報告書",
    "390": "訂正変更報告書",
    # 公開買付関連
    "350": "公開買付届出書",
    "410": "公開買付報告書",
    # 自己株券買付関連
    "420": "自己株券買付状況報告書",
    "430": "訂正自己株券買付状況報告書",
    # 内部統制関連
    "250": "内部統制報告書",
    "255": "訂正内部統制報告書",
    # その他
    "010": "目論見書",
    "020": "訂正目論見書",
}


def get_doc_type_name(doc_type_code: str | None) -> str:
    """Get Japanese name for a document type code.

    Args:
        doc_type_code: EDINET document type code (e.g., "120").

    Returns:
        Japanese name for the document type, or "その他" if unknown.

    Example:
        >>> get_doc_type_name("120")
        '有価証券報告書'
        >>> get_doc_type_name("999")
        'その他'
    """
    if doc_type_code is None:
        return "その他"
    return DOC_TYPE_NAMES.get(doc_type_code, "その他")
