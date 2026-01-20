#!/bin/python3

# Global
import os
import pathlib
from datetime import date, datetime, UTC as timezoneUTC
import re
import unicodedata
from functools import partial

# External
import pdfplumber
import strx
from viet_text_tools import normalize_diacritics

# Internal
from einvoice_lens._constant import DEFAULT_MAPPING_CHARACTERS
import einvoice_lens.model as model
from einvoice_lens._util import calculate_checksum_crc32c_on


def is_main_header(element: list[str]) -> bool:
    "Handle ['STT\n(No.)', 'Tên hàng hóa, dịch vụ\n(Description)', 'Đơn vị tính\n(Unit)', 'Số lượng\n(Quantity)', 'Đơn giá\n(Unit price)', 'Thành tiền\n(Amount)']"
    if element[0].lower().startswith("stt") or "No." in element[0]:
        return True
    return False


def is_sub_header(element: list[str]) -> bool:
    "Handle ['(1)', '(2)', '(3)', '(4)', '(5)', '(6) = (4) x (5)']"
    if element[0] == "(1)":
        if element[1] == "(2)":
            return True
    return False


def is_list_contain_empty(element: list[str]) -> bool:
    "Handle ['', '', '', '', '', '']"
    if all([x == "" for x in element]):
        return True
    return False


def is_group_total_amount_number(element: list[str]) -> bool:
    "Handle ['Tổng tiền thanh toán(Total amount): 20.752.000', None, None, None, None, None]"
    if any([x in element[0] for x in ("Tổng tiền thanh toán", "Total amount", "Cộng tiền hàng")]):
        return True
    return False


def is_group_total_amount_in_words(element: list[str]) -> bool:
    "Handle ['Số tiền viết bằng chữ(In words):Hai mươi triệu bảy trăm năm mươi hai nghìn đồng', None, None, None, None, None]"
    if element[0].startswith("Số tiền viết bằng chữ") or "In words" in element[0]:
        return True
    return False


def any_match(string: str, *args: str) -> bool:
    for arg in args:
        if string == arg:
            return True
    return False


# Mapping attributes
MAPPING_ATTRIBUTE_KEY: dict[str, dict[str, list[str]]] = {
    "TAX_AGENT_CODE": {"type": "composite", "search_by": {"english": ["Tax agent code"], "vietnamese": ["Mã CQT", "Mã cơ quan thuế", "Mã của cơ quan thuế"]}},
    "SERIAL_NO": {"type": "composite", "search_by": {"english": ["Serial No"], "vietnamese": ["Ký hiệu"]}},
    "INVOICE_NUMBER": {"type": "composite", "search_by": {"english": ["No"], "vietnamese": ["Số", "Số hiệu"]}},
    "TAX_CODE": {"type": "composite", "search_by": {"english": ["Tax code"], "vietnamese": ["Mã số thuế", "MST"]}},
    "COMPANY_NAME": {"type": "composite", "search_by": {"english": ["company's name"], "vietnamese": ["Tên đơn vị", "Tên doanh nghiệp", "Tên hộ kinh doanh"]}},
    "ADDRESS": {"type": "composite", "search_by": {"english": ["Address"], "vietnamese": ["Địa chỉ"]}},
    "PHONE": {"type": "composite", "search_by": {"english": ["Phone", "Tel"], "vietnamese": ["Điện thoại", "Số điện thoại"]}},
    "WEBSITE": {"type": "composite", "search_by": {"english": ["Website"], "vietnamese": ["Trang thông tin", "Trang web"]}},
    "EMAIL": {"type": "composite", "search_by": {"english": ["Email"], "vietnamese": ["Email"]}},
    "FAX": {"type": "composite", "search_by": {"english": ["Fax"], "vietnamese": ["Fax"]}},
    "PAYMENT_ACCOUNT": {"type": "composite", "search_by": {"english": ["Account number", "a/c no", "Account No"], "vietnamese": ["Số tài khoản", "Tài khoản thanh toán"]}}, # noqa: E501
    "PAYMENT_METHOD": {"type": "composite", "search_by": {"english": ["Payment method"], "vietnamese": ["Phương thức thanh toán", "Hình thức thanh toán"]}},
    "PAYMENT_CURRENCY": {"type": "composite", "search_by": {"english": ["Payment currency"], "vietnamese": ["Đồng tiền thanh toán", "Tiền tệ thanh toán"]}},
    "TOTAL_AMOUNT": {"type": "composite", "search_by": {"english": ["Total amount"], "vietnamese": ["Cộng tiền hàng"]}}, # NO VAT
    "TOTAL_AMOUNT_AFTER_VAT": {"type": "composite", "search_by": {"english": ["Total amount after VAT"], "vietnamese": ["Tổng tiền thanh toán", "Thành tiền (sau thuế)"]}}, # Include VAT # noqa: E501
    "TOTAL_AMOUNT_IN_WORDS": {"type": "composite", "search_by": {"english": ["Total amount in words", "In words"], "vietnamese": ["Số tiền viết bằng chữ"]}},
    "VAT_RATE": {"type": "composite", "search_by": {"english": ["VAT rate", "VAT (%)"], "vietnamese": ["Thuế suất giá trị gia tăng", "Thuế suất (%)", "Thuế suất GTGT"]}}, # noqa: E501
    "VAT_AMOUNT": {"type": "composite", "search_by": {"english": ["VAT amount", "VAT (VND)"], "vietnamese": ["Tiền thuế GTGT", "Tiền thuế VAT", "Giá trị thuế GTGT"]}}, # noqa: E501
    "SEARCH_ENDPOINT": {"type": "invoice_partner", "search_by": {"english": ["Reference at"], "vietnamese": ["Tra cứu tại website"]}},
    "SEARCH_KEYWORD_ID": {"type": "invoice_partner", "search_by": {"english": ["Reference ID"], "vietnamese": ["Mã tìm kiếm", "Mã tra cứu"]}},
    "SEARCH_PARTNER": {"type": "invoice_partner", "search_by": {"english": ["Distributed by"], "vietnamese": ["Phát hành bởi"]}},
}


def build_boundary_regex(keyword: str, included_colon: bool = False) -> re.Pattern:
    """Build a Unicode-safe regex pattern to match a keyword as a standalone phrase.

    The pattern matches the keyword only when it is **not part of a larger word**,
    supporting letters from any language (Unicode-aware). Multi-word keywords
    with spaces are handled, and an optional colon immediately following the
    keyword can be enforced.

    Parameters
    ----------
    keyword (str): The keyword or phrase to match.
    included_colon (bool): If True, only match the keyword when followed by a colon. Defaults to False.

    Returns
    -------
    re.Pattern: A compiled regex pattern ready for searching.

    Usage
    -----
    >>> import re
    >>> regex = build_boundary_regex("Mã cơ quan thuế", included_colon=True)
    >>> re.search(regex, "Mã cơ quan thuế: ABCDXYZGHIKLMNOPQRSTUVWXYZ")
    <re.Match object; span=(0, 15), match='Mã cơ quan thuế'>
    """

    # Escape but keep spaces literal
    kw = re.escape(keyword)

    # Negative boundary: before keyword: either start or non-word
    # After keyword: either end, non-word, or a colon if included_colon=True
    after = r"(?=\s*:)" if included_colon else r""
    pattern = rf"(?<!\w){kw}{after}(?!\w)"

    return re.compile(pattern, flags=re.IGNORECASE | re.UNICODE)


# def is_company_name(string: str) -> bool:
#     pattern = build_boundary_regex(keyword="Công ty TNHH", included_colon=False)
#     if re.search(pattern, string):
#         return True
#     return False


class SearchAttribute:
    def __init__(self, *, key: str, mapping_english: list[str], mapping_vietnamese: list[str]):
        """Search attribute with declarative mapping

        Args
        ----
        key: str: Key of the attribute
        mapping_english: list[str]: List of English keywords to search for
        mapping_vietnamese: list[str]: List of Vietnamese keywords to search for

        Usage
        -----
        >>> s_attr = SearchAttribute(key="SERIAL_NO", mapping_english=["Serial No"], mapping_vietnamese=["Ký hiệu"])
        >>> s_attr.mask_attribute("Ký hiệu:1C25TKT", with_prefix_stop="STOP")
        '[STOP][SERIAL_NO]:1C25TKT'
        >>> s_attr.mask_attribute("Ký hiệu:1C25TKT[STOP]", with_prefix_stop="STOP")
        '[STOP][SERIAL_NO]:1C25TKT'
        """
        self.key = key
        # Build mapping list
        # Combine from (a) English and (b) Vietnamese and (c) Product between them
        component = mapping_english + mapping_vietnamese
        for k_en, k_vi in zip(mapping_english, mapping_vietnamese):
            combined = [f"{k_en} ({k_vi})", f"{k_vi} ({k_en})"]
            component.extend(combined)
        self.mapping = sorted(component, key=len, reverse=True)

    def mask_attribute(self, string: str, with_prefix_stop: str | None = None, included_colon_seperated: bool = True) -> str:
        replacement = f"[{self.key.upper()}]" if with_prefix_stop is None else f"[{with_prefix_stop.upper()}][{self.key.upper()}]"
        reform_string = unicodedata.normalize("NFC", string)
        for keyword in self.mapping:
            on_search_keyword = unicodedata.normalize("NFKC", keyword)
            regex = build_boundary_regex(keyword=on_search_keyword, included_colon=included_colon_seperated)
            ater_replace_string = regex.sub(replacement, reform_string)
            if ater_replace_string != reform_string:
                return ater_replace_string
        return string


def pipe_content_transform(*, string: str | None = None, mapping: dict[str, str] | None = None) -> str:
    """Internal pipeline that handle the transformation on document (Pre-built pipeline)

    Included following steps:
    - Apply mapping with str.translate
    - Collapse multi-spaces
    - Strip weird line breaks
    - Remove leftover control characters
    """
    if not string:
        return ""

    # Translate
    if isinstance(mapping, dict):
        string = string.translate(str.maketrans(mapping))

    # Remove control characters except tab/newline
    string = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", string)

    # Collapse weird linebreak sequences
    string = re.sub(r"\s{2,}\n", "\n", string).rstrip()

    # Collapse multiple spaces
    string = re.sub(r"\s{2,}", " ", string)

    # Others
    string = string.replace("\xad", "")

    return string


def normalize_vi_keep_accents(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = normalize_diacritics(text)
    return text


def parse_commerical_invoice(path: str) -> model.CommericalInvoiceResult:
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
        raise ValueError(f"Invaid extension of pdf. Got {path.split('.')[-1]} file type")

    # Checkpoint
    _start = datetime.now(tz=timezoneUTC)

    # Component
    attribute = model.DocumentAttribute(
        document_type=None,
        tax_agent_code=None,
        digital_signature=None,
        serial_no=None,
        invoice_number=None,
        issue_date=None
    )
    seller = model.SellerInformation(
        name=None,
        tax_code=None,
        address=None,
        tel=None,
        email=None,
        fax=None,
        account_number=None
    )
    buyer = model.BuyerInformation(
        name=None,
        company=None,
        tax_code=None,
        tel=None
    )
    invoice_partner = model.InvoicePartnerInformation(
        endpoint_search_invoice=None,
        tax_code=None
    )

    # Build
    _pipe_content_transform = partial(pipe_content_transform, mapping=DEFAULT_MAPPING_CHARACTERS)
    pattern_issue_date = re.compile(r"Ngày\s?(\(date\))?\s?(?P<date>\d{1,2})\s?tháng\s?(\(month\))?\s?(?P<month>\d{1,2})\s?năm(\(year\))?\s?(?P<year>\d{4})")

    # Get
    file_checksum = calculate_checksum_crc32c_on(path)
    file_stat = os.stat(path)
    document = pdfplumber.open(path, unicode_norm="NFKC")
    all_content = normalize_vi_keep_accents(_pipe_content_transform(string=" | ".join([page.extract_text() for page in document.pages])))
    first_page_content = normalize_vi_keep_accents(_pipe_content_transform(string=document.pages[0].extract_text()))
    last_page_content = None if len(document.pages) == 1 else normalize_vi_keep_accents(_pipe_content_transform(string=document.pages[-1].extract_text()))
    composite_features: dict[str, dict[str, list[str]]] = {
        key: val["search_by"]
        for key, val in MAPPING_ATTRIBUTE_KEY.items()
        if val["type"] == "composite"
    }
    invoice_partner_features: dict[str, dict[str, list[str]]] = {
        key: val["search_by"]
        for key, val in MAPPING_ATTRIBUTE_KEY.items()
        if val["type"] == "invoice_partner"
    }
    attrs_general = {}
    attrs_seller = {}
    attrs_buyer = {}
    _ = first_page_content
    _ = last_page_content
    _ = invoice_partner_features

    # Search: format type
    if any([unicodedata.normalize("NFKC", x) in all_content.lower() for x in ("electronic invoice display",)]):
        attribute["display_format"] = "ELECTRONIC_INVOICE_DISPLAY"

    # Search: document type
    if any([unicodedata.normalize("NFKC", x) in all_content.lower() for x in ("sales invoice", "hóa đơn bán hàng", "đơn bán hàng")]):
        attribute["document_type"] = "SALES_INVOICE"

    elif any([unicodedata.normalize("NFKC", x) in all_content.lower() for x in ("hóa đơn giá trị gia tăng",)]):
        attribute["document_type"] = "VALUE_ADDED_TAX_INVOICE"

    # Search issue date
    # # Detect issue date. Example: Ngày (date) 25 tháng (month) 09 năm (year) 2025
    search_result_issue_date = pattern_issue_date.search(all_content)
    if search_result_issue_date is not None:
        try:
            component_search_issue_date = search_result_issue_date.groupdict()
            component_search_issue_date = {x: y.strip() for x, y in component_search_issue_date.items()}
            attribute["issue_date"] = date(
                year=int(component_search_issue_date["year"]),
                month=int(component_search_issue_date["month"]),
                day=int(component_search_issue_date["date"])
            )
        except ValueError:
            pass

    # Handle
    all_content_masked_stop = all_content.replace("\n", "[STOP]")
    for key, value in composite_features.items():
        on_search_attribute = SearchAttribute(
            key=key,
            mapping_english=value["english"],
            mapping_vietnamese=value["vietnamese"]
        )
        all_content_masked_stop = on_search_attribute.mask_attribute(
            string=all_content_masked_stop,
            with_prefix_stop="STOP",
            included_colon_seperated=True
        )

    # If
    if re.search(r"^(Công ty TNHH)|(Hộ kinh doanh)", all_content_masked_stop, re.I) is not None:
        all_content_masked_stop = "[COMPANY_NAME]:" + all_content_masked_stop

    # Replace duplicate
    checkpoint_partner = "seller"
    all_content_masked_stop = all_content_masked_stop.replace("[STOP][STOP]", "[STOP]")
    for _, line_content in enumerate(all_content_masked_stop.split("[STOP]")):

        # Found metadata
        attr_search_result = re.search(r"(?P<key>\[[\w|\_]+\])(?=\:)(?P<content>.*)", line_content, re.I)
        if attr_search_result is not None:
            attr_key = attr_search_result.group("key").removeprefix("[").removesuffix("]").strip()
            attr_value = attr_search_result.group("content").removeprefix(":").removesuffix(".").strip()

            if attr_key in attrs_seller or "buyer" in attr_key.lower():
                checkpoint_partner = "buyer"

            if attr_key in ("COMPANY_NAME", "TAX_CODE", "ADDRESS", "PHONE", "EMAIL", "PAYMENT_ACCOUNT", "PAYMENT_METHOD", "PAYMENT_CURRENCY"):
                if checkpoint_partner == "seller":
                    attrs_seller[attr_key] = attr_value
                elif checkpoint_partner == "buyer":
                    attrs_buyer[attr_key] = attr_value
            else:
                attrs_general[attr_key] = attr_value

    # For last page extraction
    # for on_ind, on_line in enumerate(last_page_content.split("\n"), start=0):

    #     if any([
    #         on_line.lower().startswith("Tra cứu hóa đơn".lower()),
    #         on_line.lower().startswith("Tra cứu tại website".lower()),
    #     ]):

    #         # Find on next index too
    #         search_invoice_partner_block = " ".join([on_line, on_next_line or ""])

    #         # Then chain by vietnamese before go to search zone
    #         search_invoice_partner_block = (
    #             search_invoice_partner_block.lower()
    #             .replace("mã tra cứu", "search_keyword_id")
    #             .replace("mã số thuế", "tax_code")
    #             .replace("mst", "tax_code")
    #         )

    #         # Find
    #         search_keyword_id_result = re.search(
    #             r"(?<=search_keyword_id\:)\s?(?P<keyword_id>\w+)",
    #             search_invoice_partner_block,
    #             re.I
    #         )
    #         if search_keyword_id_result is not None:
    #             invoice_partner["search_keyword_id"] = search_keyword_id_result.group("keyword_id").upper()

    #         # Find
    #         endpoint_result = re.search(
    #             r"\bhttps?://(?:[\w\-]+\.)+[\w\-]+\b",
    #             search_invoice_partner_block,
    #             re.I
    #         )
    #         if endpoint_result is not None:
    #             invoice_partner["endpoint_search_invoice"] = endpoint_result.group().strip()

    #         # Find
    #         tax_code_result = re.search(
    #             r"(?<=tax_code\:)\s?(?P<tax_code>\b\w+)",
    #             search_invoice_partner_block,
    #             re.I
    #         )
    #         if tax_code_result is not None:
    #             invoice_partner["tax_code"] = tax_code_result.group("tax_code").strip()

    # Checkpoint mapping
    field_attributes = list(attrs_general)
    field_sellers = list(attrs_seller)
    field_buyers = list(attrs_buyer)
    if len(attrs_general) != 0:
        for k, v in attrs_general.items():
            if k.lower() in field_attributes:
                attribute[k.lower()] = v

    if len(attrs_seller) != 0:
        for k, v in attrs_seller.items():
            if k.lower() in field_sellers:
                seller[k.lower()] = v

    if len(attrs_buyer) != 0:
        for k, v in attrs_buyer.items():
            if k.lower() in field_buyers:
                buyer[k] = v

    # TODO: Current can't not process to find the digital signature. It's likely like bounding box
    # By search like: document.pages[0].objects["image"][0]["stream"].get_rawdata()
    # attribute.digital_signature = None

    # Extract
    main_header: list[str] = []
    sub_header: list[str] = []
    total_amount_figure: list[str] = []
    total_amount_in_words: list[str] = []
    table_elements: list[dict] = []
    _tray_first_element = []
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

            # Loop
            for record in table:

                # Empty record
                if is_list_contain_empty(element=record):
                    continue

                # Build
                noralization_record = [
                    pipe_content_transform(string=on_component).replace("\n", " ")
                    if on_component is not None else None
                    for on_component in record
                ]

                # For the search for (a) main header and (b) subheader
                # This only exist 1 so if they are exists, ignore the validate the next element
                if is_main_header(element=noralization_record):
                    if len(main_header) == 0:
                        on_table_length = len(noralization_record)
                        main_header.extend(noralization_record)
                    continue

                if is_sub_header(element=noralization_record):
                    if len(sub_header) == 0:
                        sub_header.extend(noralization_record)
                    continue

                if is_group_total_amount_number(element=noralization_record):
                    if len(total_amount_figure) == 0:
                        total_amount_figure.extend(noralization_record)
                    continue

                if is_group_total_amount_in_words(element=noralization_record):
                    if len(total_amount_in_words) == 0:
                        total_amount_in_words.extend(noralization_record)
                    continue

                if len(noralization_record) != on_table_length:
                    errors.append(noralization_record)
                    continue

                # Ignore case not start with ordered number
                if not str(noralization_record[0]).isdigit():
                    continue

                # Check duplicate on first element (first element is tray number on no. column)
                if record[0] in _tray_first_element:
                    continue
                else:
                    _tray_first_element.append(record[0])

                # Build
                noralization_record = {
                    "no": int(noralization_record[0]),
                    "product_description": (
                        unicodedata.normalize("NFKD", str(noralization_record[1])).replace("\n", " ")
                        if noralization_record[1] is not None
                        else None
                    ),
                    "unit": unicodedata.normalize("NFKD", noralization_record[2]).lower(),
                    "quantity": int(strx.str_to_number(string=noralization_record[3], radix=",", delimiter=".")),
                    "unit_price": float(strx.str_to_number(string=noralization_record[4], radix=",", delimiter=".")),
                    "amount": float(strx.str_to_number(string=noralization_record[5], radix=",", delimiter=".")),
                }
                table_elements.append(noralization_record)

    # Last sort
    _ = table_elements.sort(key=lambda x: x["no"])

    # Checkpoint
    _end = datetime.now(tz=timezoneUTC)

    return model.CommericalInvoiceResult(
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
        },
        profile={
            "attribute": attribute,
            "seller": seller,
            "buyer": buyer,
            "invoice_partner": invoice_partner,
        },
        dataset=table_elements
    )
