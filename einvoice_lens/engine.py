#!/bin/python3

# Global
import os
from typing import TypedDict, Literal
import pathlib
from datetime import date, datetime, UTC as timezoneUTC
import re
import unicodedata

# External
import pdfplumber
import polars as pl
import google_crc32c
import strx


def calculate_checksum_crc32c_on(path):
    crc = google_crc32c.Checksum()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            crc.update(chunk)
    return crc.digest().hex()


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


def _is_main_header(element: list[str]) -> bool:
    "Handle ['STT\n(No.)', 'Tên hàng hóa, dịch vụ\n(Description)', 'Đơn vị tính\n(Unit)', 'Số lượng\n(Quantity)', 'Đơn giá\n(Unit price)', 'Thành tiền\n(Amount)']"
    if element[0].lower().startswith("stt") or "No." in element[0]:
        return True
    return False


def _is_sub_header(element: list[str]) -> bool:
    "Handle ['(1)', '(2)', '(3)', '(4)', '(5)', '(6) = (4) x (5)']"
    if element[0] == "(1)":
        if element[1] == "(2)":
            return True
    return False


def _is_list_contain_empty(element: list[str]) -> bool:
    "Handle ['', '', '', '', '', '']"
    if all([x == "" for x in element]):
        return True
    return False


def _is_group_total_amount_number(element: list[str]) -> bool:
    "Handle ['Tổng tiền thanh toán(Total amount): 20.752.000', None, None, None, None, None]"
    if element[0].startswith("Tổng tiền thanh toán") or "Total amount" in element[0]:
        return True
    return False


def _is_group_total_amount_in_words(element: list[str]) -> bool:
    "Handle ['Số tiền viết bằng chữ(In words):Hai mươi triệu bảy trăm năm mươi hai nghìn đồng', None, None, None, None, None]"
    if element[0].startswith("Số tiền viết bằng chữ") or "In words" in element[0]:
        return True
    return False


def parse_commerical_invoice(path: str) -> CommericalInvoiceResult:
    """Parse commerical invoice from PDF file into structured output

    Args
    ----
    path (str): The path into PDF file

    Return
    ------
    CommericalInvoiceResult: The result of commerical invoice parsing

    Usage
    -----
    >>> from einvoice_lens import parse_commerical_invoice
    >>> path = "path/to/input.pdf"
    >>> result = parse_commerical_invoice(path)
    """

    if not pathlib.Path(path).exists():
        raise ValueError(f"Not exist the document on path={path!r}")

    if not path.endswith(".pdf"):
        raise ValueError(f"Invaid extension of pdf. Got {path.split('.')[1]} file type")

    # Local use
    def _pipeline_text_transform(*, string: str) -> str:
        return strx.str_normalize(string=string.encode("utf-8").decode("utf-8"), form="NFKC", strip=True).replace("\xad", "")

    # Checkpoint
    _start = datetime.now(tz=timezoneUTC)

    # Calculate
    file_checksum = calculate_checksum_crc32c_on(path)
    file_stat = os.stat(path)

    # Get
    document = pdfplumber.open(path, unicode_norm="NFKC")

    # Extract: Document Attribute
    attribute = DocumentAttribute(document_type="UNKNOWN", tax_agent_code=None, digital_signature=None)
    seller = SellerInformation()
    buyer = BuyerInformation(name=None, company=None, tax_code=None, tel=None)
    invoice_partner = InvoicePartnerInformation(endpoint_search_invoice=None, tax_code=None)

    # Hold content from profile off document
    profile_content = {}

    # Component
    # (Information) The attribute of the document mostly in the first page only
    #   and it's repeatable for format (same with others page)
    # So that we can regex on the first page line by line
    first_page_content = _pipeline_text_transform(string=document.pages[0].extract_text())

    # Format is somehow can't not defined by rule
    if "electronic invoice display" in first_page_content.lower():
        attribute["display_format"] = "ELECTRONIC_INVOICE_DISPLAY"

    # Loop
    first_page_bucket_line_content = first_page_content.split("\n")
    on_scrool_over_type: str = "" # One of seller, buyer for search role play
    for on_ind, on_text in enumerate(first_page_bucket_line_content, start=0):

        # Normalized
        nor_on_text = _pipeline_text_transform(string=on_text)
        nor_on_next_text = None

        try:
            nor_on_next_text = _pipeline_text_transform(string=first_page_bucket_line_content[on_ind + 1])
        except IndexError:
            pass

        # Define
        if any([unicodedata.normalize("NFKC", _otext) in nor_on_text.lower() for _otext in ("sales invoice", "hóa đơn bán hàng", "đơn bán hàng")]):
            attribute["document_type"] = "SALES_INVOICE"

        # Detect issue date. Example: Ngày (date) 25 tháng (month) 09 năm (year) 2025
        issue_date = None
        if all([
            any([
                unicodedata.normalize("NFKC", "date") in nor_on_text,
                unicodedata.normalize("NFKC", "day") in nor_on_text
            ]),
            unicodedata.normalize("NFKC", "month") in nor_on_text,
            unicodedata.normalize("NFKC", "year") in nor_on_text
        ]):

            # Extract
            e_day = re.search(r"(?<=date\))\s?\d{1,}+", nor_on_text, re.A) or re.search(r"(?<=day\))\s?\d{1,}+", nor_on_text, re.A)
            e_month = re.search(r"(?<=month\))\s?\d{1,}+", nor_on_text, re.A)
            e_year = re.search(r"(?<=year\))\s?\d{1,}+", nor_on_text, re.A)
            at_day = int(e_day.group(0)) if e_day is not None else None
            at_month = int(e_month.group(0)) if e_month is not None else None
            at_year = int(e_year.group(0)) if e_year is not None else None

            # Note: The value of (year) can be broken into of flow steps.
            # So if e_day, e_month is not None but e_year is None, required search for next '2xxx' in the next lines
            if all([e_day is not None, e_month is not None, e_year is None]):
                for n_ind in range(on_ind+1, len(first_page_bucket_line_content)):
                    search_result_on_year = re.search(r"^2\d{3}$", first_page_bucket_line_content[n_ind].strip(), re.A)
                    if search_result_on_year is not None:
                        at_year = int(search_result_on_year.group(0))
                        break

            if all([at_day is not None, at_month is not None, at_year is not None]):
                issue_date = date(year=at_year, month=at_month, day=at_day)

            # Append
            attribute["issue_date"] = issue_date

        # Parse mapping value
        if ":" in nor_on_text:
            key, val = nor_on_text.split(":", maxsplit=1)
            val = unicodedata.normalize("NFKD", val.strip())

            if "Serial No" in key:
                attribute["serial_no"] = val

            elif "No." in key:
                attribute["invoice_number"] = val

            elif "No." in key:
                attribute["document_type"] = val

            elif any([_imap in key.lower() for _imap in ("mã của cơ quan thuế", "mã cơ quan thuế")]):
                attribute["tax_agent_code"] = val

            # Handlers
            profile_content[key] = val

        # Handle the invoice partner
        if nor_on_text.lower().startswith(unicodedata.normalize("NFKC", "Tra cứu hóa đơn").lower()):

            # Find on next index too
            search_invoice_partner_block = " ".join([nor_on_text, nor_on_next_text or ""])

            # Then chain by vietnamese before go to search zone
            search_invoice_partner_block = (
                search_invoice_partner_block.lower()
                .replace("mã tra cứu", "search_keyword_id")
                .replace("mã số thuế", "tax_code")
                .replace("mst", "tax_code")
            )

            # Find
            search_keyword_id_result = re.search(
                r"(?<=search_keyword_id\:)\s?(?P<keyword_id>\w+)",
                search_invoice_partner_block,
                re.I
            )
            if search_keyword_id_result is not None:
                invoice_partner["search_keyword_id"] = search_keyword_id_result.group("keyword_id").upper()

            # Find
            endpoint_result = re.search(
                r"\bhttps?://(?:[\w\-]+\.)+[\w\-]+\b",
                search_invoice_partner_block,
                re.I
            )
            if endpoint_result is not None:
                invoice_partner["endpoint_search_invoice"] = endpoint_result.group().strip()

            # Find
            tax_code_result = re.search(
                r"(?<=tax_code\:)\s?(?P<tax_code>\b\w+)",
                search_invoice_partner_block,
                re.I
            )
            if tax_code_result is not None:
                invoice_partner["tax_code"] = tax_code_result.group("tax_code").strip()

        # Define scroll point
        # Detect block of buyer | seller (related to same attribute like name, address, account_number, ...)
        # then search words related until change scrolling point
        if "seller" in nor_on_text.lower():
            on_scrool_over_type = "seller"
        elif "buyer" in nor_on_text.lower():
            on_scrool_over_type = "buyer"

        if on_scrool_over_type == "seller":

            _, s_val = None, None
            if len(nor_on_text.split(":")) > 1:
                _, s_val = nor_on_text.split(":", maxsplit=1)
                s_val = unicodedata.normalize("NFC", s_val.strip())

            if "seller" in nor_on_text.lower():
                seller["name"] = s_val

            elif "tax code" in nor_on_text.lower():
                seller["tax_code"] = s_val

            elif "address" in nor_on_text.lower():
                seller["address"] = s_val

            elif "tel" in nor_on_text.lower(): # TODO: Multiple in 1 line
                seller["tel"] = s_val

            elif "email" in nor_on_text.lower(): # TODO: Multiple in 1 line
                seller["email"] = s_val

            elif "fax" in nor_on_text.lower(): # TODO: Multiple in 1 line
                seller["fax"] = s_val

            elif "a/c no" in nor_on_text.lower():
                seller["account_number"] = s_val

        if on_scrool_over_type == "buyer":

            _, b_val = None, None
            if len(nor_on_text.split(":")) > 1:
                _, b_val = nor_on_text.split(":", maxsplit=1)
                b_val = unicodedata.normalize("NFC", b_val.strip())

            if "buyer" in nor_on_text.lower():
                buyer["name"] = b_val

            if "company's name" in nor_on_text.lower():
                buyer["company"] = b_val

            elif "tax code" in nor_on_text.lower():
                buyer["tax_code"] = b_val

            elif "address" in nor_on_text.lower():
                buyer["address"] = b_val

            elif "tel" in nor_on_text.lower(): # TODO: Multiple in 1 line
                buyer["tel"] = b_val

            elif "email" in nor_on_text.lower(): # TODO: Multiple in 1 line
                buyer["email"] = b_val

            elif "fax" in nor_on_text.lower(): # TODO: Multiple in 1 line
                buyer["fax"] = b_val

            elif "a/c no" in nor_on_text.lower():
                buyer["account_number"] = b_val

    # TODO: Current can't not process to find the digital signature. It's likely like bounding box
    # By search like: document.pages[0].objects["image"][0]["stream"].get_rawdata()
    # attribute.digital_signature = None

    # Extract
    main_header: list[str] = []
    sub_header: list[str] = []
    total_amount_figure: list[str] = []
    total_amount_in_words: list[str] = []
    table_elements = []
    errors = []
    on_table_length: int = None
    for _, element in enumerate(document.pages, start=0):

        # Extract all
        # The package extraction process lead to the duplication of records
        # So that we using validate in the bucket output to verify out of the component
        e_tables = element.extract_tables(
            table_settings={
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines"
            },
        )

        # Loop
        for table in e_tables:
            for record in table:

                if _is_list_contain_empty(element=record):
                    continue

                # Normalization
                noralization_record = [
                    _pipeline_text_transform(string=text).replace("\n", " ")
                    if text is not None else None
                    for text in record
                ]

                # Check duplication
                if noralization_record in table_elements:
                    pass

                # For the search for (a) main header and (b) subheader
                # This only exist 1 so if they are exists, ignore the validate the next element
                if _is_main_header(element=noralization_record):
                    if len(main_header) == 0:
                        on_table_length = len(noralization_record)
                        main_header.extend(noralization_record)
                    continue

                if _is_sub_header(element=noralization_record):
                    if len(sub_header) == 0:
                        sub_header.extend(noralization_record)
                    continue

                if _is_group_total_amount_number(element=noralization_record):
                    if len(total_amount_figure) == 0:
                        total_amount_figure.extend(noralization_record)
                    continue

                if _is_group_total_amount_in_words(element=noralization_record):
                    if len(total_amount_in_words) == 0:
                        total_amount_in_words.extend(noralization_record)
                    continue

                if len(noralization_record) != on_table_length:
                    errors.append(noralization_record)
                    continue

                # Set
                table_elements.append(noralization_record)

    # Parse
    dataset = pl.DataFrame(
        table_elements,
        schema=["no", "product_description", "unit", "quantity", "unit_price", "amount"],
        orient="row",
        strict=False
    )

    # Transform
    dataset = (
        dataset
        .with_columns([
            pl.col("no").cast(pl.Int64, strict=True).name.keep(),
            pl.col("product_description").str.replace_all("\n", " ").name.keep(),
            pl.col("unit").cast(pl.String).str.to_titlecase().name.keep(),
            pl.col("quantity").cast(pl.Int64, strict=True).name.keep(),
            pl.col(["unit_price", "amount"]).str.replace_all(".", "", literal=True).cast(pl.Float64).name.keep(),
        ])
        .unique(subset="no")
        .sort(by="no", descending=False)
    )

    # Checkpoint
    _end = datetime.now(tz=timezoneUTC)

    return CommericalInvoiceResult(
        runtime_metadata={
            "source_path": pathlib.Path(path).as_posix(),
            "checksum_crc32c": file_checksum,
            "total_pages": len(document.pages),
            "file_size_mb": round(file_stat.st_size / 10**6, 2),
            "pipeline": {
                "start": _start,
                "end": _end,
                "processing_in_seconds": (_end - _start).total_seconds(),
            },
            # "container": document.to_dict(),
        },
        profile={
            "attribute": attribute,
            "seller": seller,
            "buyer": buyer,
            "invoice_partner": invoice_partner,
        },
        dataset=dataset.to_dicts()
    )
