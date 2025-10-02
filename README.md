<div align="center">
  <a href="https://github.com/thuyetbao/einvoice-lens.git">
    <img src="docs/assets/images/banner.png" alt="Package Banner" height="200" width="100%">
  </a>
</div>

<div align="center">
  <h3>Einvoice Lens</h3>
  <p><b>Scan Vietnam's electronic invoices into structured data</b></p>
</div>

<div align="center">
  <a href="https://github.com/thuyetbao/einvoice-lens.git" target="_blank">
    <img src="https://img.shields.io/pypi/v/einvoice-lens.svg?logo=pypi" alt="Package Version">
  </a>
</div>

<div align="center">
  <a href="https://www.python.org/" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/einvoice-lens.svg?logo=python" alt="Supported Python Version">
  </a>
  <br>
  <a href="https://pre-commit.com/" target="_blank">
    <img src="https://img.shields.io/badge/pre--commit-enabled-teal?logo=pre-commit" alt="pre-commit enabled">
  </a>
  <a href="https://pre-commit.com/" target="_blank">
    <img src="https://img.shields.io/badge/pep8-enabled-teal?logo=python" alt="pep8 enabled">
  </a>
  <a href="https://github.com/features/actions" target="_blank">
    <img src="https://img.shields.io/badge/cicd-github--action-teal?logo=github-actions" alt="Github Action">
  </a>
</div>

---

**einvoice-lens** is a package that uses OCR and rule-based parsing to transform Vietnam's electronic invoices into structured data.

**Features**:

- Extracts structured output of sale invoice

- Command-line interface to integrate with shell scripts and automation workflows

## **Usage**

Install package from PyPI distribution [`einvoice-lens`](https://pypi.org/project/einvoice-lens/)

```bash
pip install einvoice-lens
```

```py
from  einvoice_lens import parse_commerical_invoice

output = parse_commerical_invoice(path="path/to/document.pdf")
```

or, using cli by

```bash
python -m einvoice_lens.cli --path path/to/document.pdf
```

**Documentation**:

Documentation document at folder [docs/](/docs/)

**Code Storage**:

Repository: [GitHub > Repository:`einvoice-lens`](https://github.com/thuyetbao/einvoice-lens)

**Releases**:

Releases: [GitHub > Repository:`einvoice-lens` > Releases](https://github.com/thuyetbao/einvoice-lens/releases)
