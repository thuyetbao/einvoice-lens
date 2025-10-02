# **TODO**

- [ ] Add grouth truth for define the dataset is satified (total rows, total amount)

- [ ] Added metadata for Total Amount and In Words

- [ ] Issue trouble on encoded

- [ ] CLI params

- [ ] Suppress warning

```bash
tests/test_extract_document.py::test_extract_document_base_case
  thuyetbao\REPOSITORY\einvoice-lens\einvoice_lens\engine.py:446: PolarsInefficientMapWarning:
  Expr.map_elements is significantly slower than the native expressions API.
  Only use if you absolutely CANNOT implement your logic otherwise.
  Replace this expression...
    - pl.col("unit").map_elements(lambda s: ...)
  with this one instead:
    + pl.col("unit").cast(pl.String).str.to_titlecase()

    pl.col("unit").str.to_lowercase().map_elements(lambda s: str(s).title(), return_dtype=pl.String).name.keep(),

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
========================================================================================== 1 passed, 1 warning in 0.42s ==========================================================================================
```

- [ ] Add support for `Python 3.14`. See: <https://github.com/thuyetbao/einvoice-lens/actions/runs/18183864131/job/51764582139>

```bash
Installed versions
  Version 3.14 was not found in the local cache
  Error: The version '3.14' with architecture 'x64' was not found for Ubuntu 22.04.
  The list of all available versions can be found here: https://raw.githubusercontent.com/actions/python-versions/main/versions-manifest.json
```
