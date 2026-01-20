#!/bin/python3

# Global
import sys
import os
from datetime import datetime, date

# Append
sys.path.append(os.path.abspath(os.curdir))

# External
import pytest
import polars as pl

# Internal
import einvoice_lens


@pytest.fixture(scope="module")
def resource_path() -> str:
    return os.path.join("tests", "data", "sample-sale-invoice.pdf")


@pytest.mark.filterwarnings("ignore:PolarsInefficientMapWarning")
def test_extract_document_base_case(resource_path):

    expected_profile: dict[str, dict[str, str | None]] = {
        "attribute": {
            "document_type": "SALES_INVOICE",
            "tax_agent_code": "09DOFI999FDEEE921399FFFAKS29FF9A",
            "display_format": "ELECTRONIC_INVOICE_DISPLAY",
            "issue_date": date(2025, 8, 28),
            "serial_no": "3C35OKP",
            "invoice_number": "123",
            "digital_signature": None,
        },
        "seller": {
            "name": "HỘ KINH DOANH VĨNH LONG 999",
            "tax_code": "0301118723-001",
            "address": "Phường Chợ Lớn, TP Hồ Chí Minh",
            # "tel": "0988789828",
            # "email": "vinhlong999@gmail.com",
            # "fax": "",
            # "account_number": "0440003331234 Ngân hàng Vietcombank",
        },
        "buyer": {
            "name": "Lê Hoàng Minh Phương",
            "company": "HỘ KINH DOANH CHÍ VỸ 102",
            "address": "999 Lý Thường Kiệt, Phường Buôn Ma Thuột, Tỉnh Đắk Lắk, Việt Nam",
            "tax_code": "7000999999",
            "account_number": "",
        },
        "invoice_partner": {
            "endpoint_search_invoice": "http://tracuu.hoadon.com",
            "tax_code": "0401486901",
        },
    }

    expected_dataset = pl.DataFrame({
        "no": [1, 2, 3],
        "product_description": ["Xe cảnh sát SH", "Xe rác SH", "Xe chở hàng SH"],
        "unit": ["chiếc", "chiếc", "chiếc"],
        "quantity": [40, 20, 10],
        "unit_price": [37000.0, 40000.0, 40000.0],
        "amount": [1480000.0, 800000.0, 400000.0],
    }, orient="col")

    # Pare
    output = einvoice_lens.parse_commerical_invoice(path=resource_path)

    # Validate
    assert all([x in ("runtime_metadata", "profile", "dataset") for x in output]), (
        f"Expected required keys in (\"runtime_metadata\", \"profile\", \"dataset\"). Got {output!s}"
    )

    # Extract
    runtime_metadata = output["runtime_metadata"]
    profile = output["profile"]
    dataset = output["dataset"]

    # Validate runtime
    assert runtime_metadata["source_path"] == "tests/data/sample-sale-invoice.pdf"
    assert runtime_metadata["checksum_crc32c"] == "a6f1bd83"
    assert runtime_metadata["total_pages"] == 1
    assert runtime_metadata["file_size_mb"] > 0
    assert all([
        isinstance(runtime_metadata["pipeline"]["start"], datetime),
        isinstance(runtime_metadata["pipeline"]["end"], datetime),
        runtime_metadata["pipeline"]["processing_in_seconds"] > 0,
    ])

    # Validate profile
    for ekey, evalue in expected_profile.items():
        for eekey, eevalue in evalue.items():
            assert profile[ekey][eekey] == eevalue, f"{ekey} > {eekey} not match. Required {eevalue} but got {profile[ekey][eekey]}"

    # Validate dataset
    assert len(dataset) == 3
    assert sum([x["amount"] for x in dataset]) == 2680000.0, f"Expected sum of amount is 2680000.0, got {sum([x['amount'] for x in dataset])}"
    assert pl.DataFrame(data=dataset, infer_schema_length=10).equals(other=expected_dataset), f"Required match dataset. Got:\n{dataset}"
