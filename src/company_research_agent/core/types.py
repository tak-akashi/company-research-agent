"""Type definitions for Company Research Agent."""

from typing import Literal

# Document download type for EDINET API
# 1: XBRL (ZIP) - 提出本文書及び監査報告書
# 2: PDF - 提出本文書及び監査報告書
# 3: 添付文書 (ZIP)
# 4: 英文ファイル (ZIP)
# 5: CSV (ZIP) - 財務諸表データ
type DocumentDownloadType = Literal[1, 2, 3, 4, 5]
