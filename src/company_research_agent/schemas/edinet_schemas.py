"""Pydantic schemas for EDINET API responses."""

from pydantic import BaseModel, Field, field_validator


class RequestParameter(BaseModel):
    """Request parameter information in EDINET API response.

    Attributes:
        date: The requested date in YYYY-MM-DD format.
        type: The request type (1=metadata only, 2=with document list).
    """

    date: str = Field(..., description="Requested date (YYYY-MM-DD)")
    type: str = Field(..., description="Request type (1 or 2)")


class ResultSet(BaseModel):
    """Result set information in EDINET API response.

    Attributes:
        count: Total number of documents for the requested date.
    """

    count: int = Field(..., description="Total document count")


class ResponseMetadata(BaseModel):
    """Metadata in EDINET API response.

    Attributes:
        title: API title description.
        parameter: Request parameters.
        resultset: Result set information.
        process_date_time: Processing date and time.
        status: Internal EDINET status code (e.g., "200", "404").
        message: Status message.
    """

    title: str = Field(..., description="API title")
    parameter: RequestParameter = Field(..., description="Request parameters")
    resultset: ResultSet = Field(..., description="Result set info")
    process_date_time: str = Field(..., alias="processDateTime", description="Processing datetime")
    status: str = Field(..., description="Internal status code")
    message: str = Field(..., description="Status message")


class DocumentMetadata(BaseModel):
    """Individual document metadata from EDINET API.

    All flag fields (xbrl_flag, pdf_flag, etc.) are converted from
    string "0"/"1" to boolean for easier handling.

    Attributes:
        seq_number: Sequential number for the file date.
        doc_id: Document management number (8 characters).
        edinet_code: Filer's EDINET code (6 characters).
        sec_code: Filer's securities code (5 digits), None if not applicable.
        jcn: Filer's corporate number (13 digits), None if not applicable.
        filer_name: Filer's name.
        fund_code: Fund code for investment trusts.
        ordinance_code: Ordinance code (3 digits).
        form_code: Form code (6 digits).
        doc_type_code: Document type code (3 digits).
        period_start: Period start date (YYYY-MM-DD), None if not applicable.
        period_end: Period end date (YYYY-MM-DD), None if not applicable.
        submit_date_time: Submission datetime (YYYY-MM-DD hh:mm).
        doc_description: Document description.
        issuer_edinet_code: Issuer's EDINET code for disclosure documents.
        subject_edinet_code: Subject's EDINET code.
        subsidiary_edinet_code: Subsidiary's EDINET code.
        current_report_reason: Reason for extraordinary report.
        parent_doc_id: Parent document ID for corrections.
        ope_date_time: Operation datetime.
        withdrawal_status: Withdrawal status (0=normal, 1=withdrawal, 2=withdrawn).
        doc_info_edit_status: Document info edit status.
        disclosure_status: Disclosure status.
        xbrl_flag: True if XBRL is available.
        pdf_flag: True if PDF is available.
        attach_doc_flag: True if attachment documents are available.
        english_doc_flag: True if English documents are available.
        csv_flag: True if CSV is available.
        legal_status: Legal status (0=expired, 1=viewing, 2=extended).
    """

    seq_number: int = Field(..., alias="seqNumber", description="Sequential number")
    doc_id: str = Field(..., alias="docID", description="Document ID")
    edinet_code: str | None = Field(None, alias="edinetCode", description="EDINET code")
    sec_code: str | None = Field(None, alias="secCode", description="Securities code")
    jcn: str | None = Field(None, alias="JCN", description="Corporate number")
    filer_name: str | None = Field(None, alias="filerName", description="Filer name")
    fund_code: str | None = Field(None, alias="fundCode", description="Fund code")
    ordinance_code: str | None = Field(None, alias="ordinanceCode", description="Ordinance code")
    form_code: str | None = Field(None, alias="formCode", description="Form code")
    doc_type_code: str | None = Field(None, alias="docTypeCode", description="Document type code")
    period_start: str | None = Field(None, alias="periodStart", description="Period start date")
    period_end: str | None = Field(None, alias="periodEnd", description="Period end date")
    submit_date_time: str | None = Field(
        None, alias="submitDateTime", description="Submission datetime"
    )
    doc_description: str | None = Field(
        None, alias="docDescription", description="Document description"
    )
    issuer_edinet_code: str | None = Field(
        None, alias="issuerEdinetCode", description="Issuer EDINET code"
    )
    subject_edinet_code: str | None = Field(
        None, alias="subjectEdinetCode", description="Subject EDINET code"
    )
    subsidiary_edinet_code: str | None = Field(
        None, alias="subsidiaryEdinetCode", description="Subsidiary EDINET code"
    )
    current_report_reason: str | None = Field(
        None, alias="currentReportReason", description="Extraordinary report reason"
    )
    parent_doc_id: str | None = Field(None, alias="parentDocID", description="Parent document ID")
    ope_date_time: str | None = Field(None, alias="opeDateTime", description="Operation datetime")
    withdrawal_status: str = Field(..., alias="withdrawalStatus", description="Withdrawal status")
    doc_info_edit_status: str | None = Field(
        None, alias="docInfoEditStatus", description="Doc info edit status"
    )
    disclosure_status: str | None = Field(
        None, alias="disclosureStatus", description="Disclosure status"
    )
    xbrl_flag: bool = Field(..., alias="xbrlFlag", description="XBRL availability")
    pdf_flag: bool = Field(..., alias="pdfFlag", description="PDF availability")
    attach_doc_flag: bool = Field(..., alias="attachDocFlag", description="Attachment availability")
    english_doc_flag: bool = Field(
        ..., alias="englishDocFlag", description="English doc availability"
    )
    csv_flag: bool = Field(..., alias="csvFlag", description="CSV availability")
    legal_status: str = Field(..., alias="legalStatus", description="Legal status")

    @field_validator(
        "xbrl_flag",
        "pdf_flag",
        "attach_doc_flag",
        "english_doc_flag",
        "csv_flag",
        mode="before",
    )
    @classmethod
    def convert_flag_to_bool(cls, v: str | bool | None) -> bool:
        """Convert EDINET flag values ("0"/"1") to boolean."""
        if isinstance(v, bool):
            return v
        if v is None:
            return False
        return v == "1"


class DocumentListResponse(BaseModel):
    """Complete response from EDINET document list API.

    Attributes:
        metadata: Response metadata including status and counts.
        results: List of document metadata, None for type=1 requests.
    """

    metadata: ResponseMetadata = Field(..., description="Response metadata")
    results: list[DocumentMetadata] | None = Field(
        None, description="Document list (None for type=1)"
    )
