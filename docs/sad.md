# SAD

## **Overview**

In Vietnam, a **sales invoice** is a formal accounting document issued by a seller to record the sale of goods or services. It is governed by strict legal and tax regulations and typically comes in the form of an **electronic invoice (hóa đơn điện tử)**.

Sales invoices are essential for:

- Tax declaration and deduction
- Legal proof of transaction
- Financial reporting and auditing

📌 Legal Basis

- **Decree 123/2020/ND-CP**: Governs the use of invoices and documents.
- **Circular 78/2021/TT-BTC**: Details the implementation of electronic invoices.
- **General Department of Taxation (GDT)**: Oversees compliance and issuance.

🧾 What’s Included in a Sales Invoice

- Seller and buyer information
- Invoice code and number
- Date of issuance
- Description of goods/services
- Quantity and unit price
- Total amount and VAT (if applicable)
- Digital signature (for electronic invoices)

scan[ocr] → parse[regex] → extract[json]

- "eInvoice": Clearly signals the domain—electronic invoices
- "Lens": Implies precision, scanning, and insight (like a camera or microscope)
- Feels like a modular engine or AI-powered tool
- Easy to remember, pronounce, and scale into a product or API

## **Implementation Logic**

Transform data into a clean format:
(a) Remove rows with all empty values
(b) Remove duplicate rows
(c) Group items by the following criteria:
(i) The first column is either "Tong tien thanh toan" or empty
(ii) The second column is either "So tien bang chu" or empty
(d) Map values to their corresponding namespace using a Language Model (LLM)
(e) Convert data types to numbers and strings
(f) Verify that the total number of rows is correct

Core Invoice Fields for Compliance

| Field Name          | Description                                                       |
| ------------------- | ----------------------------------------------------------------- |
| `document_type`     | Type of invoice (e.g., VAT, export, service)                      |
| `issue_date`        | Date of issuance (must match deadline rules per transaction type) |
| `seller_tax_code`   | Tax code of the seller                                            |
| `seller_name`       | Legal name of the seller                                          |
| `buyer_name`        | Name of the buyer (individual or organization)                    |
| `buyer_tax_code`    | Tax code of the buyer (if applicable)                             |
| `serial_number`     | Invoice serial number (e.g., AB/22E)                              |
| `invoice_number`    | Sequential invoice number                                         |
| `tax_agency_code`   | Mã cơ quan thuế (e.g., M2­25a­SIWTI­00000000009)                  |
| `goods_description` | Itemized list of goods/services                                   |
| `unit_price`        | Price per unit                                                    |
| `quantity`          | Quantity sold                                                     |
| `amount`            | Total before tax                                                  |
| `vat_rate`          | VAT percentage (e.g., 10%)                                        |
| `vat_amount`        | Calculated VAT                                                    |
| `total_amount`      | Total payable (including VAT)                                     |
| `digital_signature` | Required for e-invoice authenticity                               |
| `pos_reference`     | POS system ID or transaction reference (for real-time reporting)  |

Types of Sales Invoice Documents in Vietnam

| Type of Invoice                            | Description                                                                                       |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| **Hóa đơn giá trị gia tăng (VAT Invoice)** | Used by businesses subject to VAT to record taxable sales.                                        |
| **Hóa đơn bán hàng (Sales Invoice)**       | Used by businesses not subject to VAT or under simplified tax regimes.                            |
| **Hóa đơn xuất khẩu (Export Invoice)**     | Used for international trade transactions.                                                        |
| **Hóa đơn điện tử (Electronic Invoice)**   | Mandatory for most businesses since 2022 under Decree 123/2020/ND-CP and Circular 78/2021/TT-BTC. |

Issuance Deadlines (Mapped to Logic)

| Transaction Type | Required `issue_date` Logic                             |
| ---------------- | ------------------------------------------------------- |
| Sale of goods    | `issue_date = date_of_ownership_transfer`               |
| Services         | `issue_date = date_of_completion or payment_date`       |
| Export           | `issue_date ≤ next_working_day_after_customs_clearance` |

## **Reference**

- <https://luatvietnam.vn/thue/thong-tu-32-2025-tt-btc-huong-dan-luat-quan-ly-thue-va-nghi-dinh-ve-hoa-don-chung-tu-401781-d1.html>

- <https://www.vietnam-briefing.com/news/e-invoice-compliance-in-vietnam-regulations-requirements-and-best-practices.html>
