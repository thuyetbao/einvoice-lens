#!/bin/python3

# Global
from typing import TypedDict, Literal
from datetime import date, datetime


class DigitalSignature(TypedDict):
    # "digital_signature": {
    #   "certificate_serial": "1234567890ABCDEF",
    #   "issuer": "VNPT-CA",
    #   "signed_at": "2025-09-28T14:32:00+07:00",
    #   "signature_value": "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A..."
    # }
    certificate_serial: str
    issuer: str | None
    signed_at: str
    signature_value: str


class DocumentAttribute(TypedDict):
    document_type: Literal["SALES_INVOICE", "UNKNOWN"] | None
    display_format: str | None
    issue_date: date | None
    tax_agent_code: str | None
    serial_no: str | None
    invoice_number: str | None
    digital_signature: str | None


class SellerInformation(TypedDict):
    name: str
    tax_code: str
    address: str
    tel: str | None
    email: str | None
    fax: str | None
    account_number: str | None


class BuyerInformation(TypedDict):
    name: str | None
    company: str | None
    tax_code: str
    address: str | None
    tel: str | None
    email: str | None
    fax: str | None
    account_number: str | None


class InvoicePartnerInformation(TypedDict):
    name: str
    endpoint_search_invoice: str | None
    search_keyword_id: str | None
    tax_code: str | None
    contact: str | None
    logo: str | None


class CommericalInvoiceProfile(TypedDict):
    attribute: DocumentAttribute
    seller: SellerInformation
    buyer: BuyerInformation
    invoice_partner: InvoicePartnerInformation


class PipelineMetadata(TypedDict):
    start: datetime
    end: datetime
    processing_in_seconds: float


class RuntimeMetadata(TypedDict):
    source_path: str
    checksum_crc32c: str | None
    total_pages: int
    file_size_mb: float
    pipeline: PipelineMetadata
    # container: dict[str, Any] # Not meaningful


class CommericalInvoiceResult(TypedDict):
    runtime_metadata: RuntimeMetadata
    profile: CommericalInvoiceProfile
    dataset: list[dict[Literal["no", "production_description", "unit", "quantity", "unit_price", "amount"], str | int | float]]
