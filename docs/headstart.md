# Headstart

## **Overview**

The centralization place for developers to develop and headstart within the project

## **Development**

### **Prerequisite**

- Python version `>=3.12.x`

- `hatch` for build package

- `make` for automate command in bash

- `gh` is a GitHub CLI program to manage release documentation

### **Installation**

- Clone the package at [GitHub repository]

```bash
git clone https://github.com/thuyetbao/einvoice-lens.git einvoice-lens
```

- Create virtual environment and activate

```bash
make venv && source venv/script/active
# pre-commit installed at .git\hooks\pre-commit
```

- Install dev-mode requirement

```bash
make install
```

- Install the config of `pre-commit`

```bash
pre-commit install
# pre-commit installed at .git\hooks\pre-commit
```

### **Internal Documentation**

Serve the documentation

You can serve the documentation locally with the following command:

```bash
hatch run docs
```

The documentation will be available on port 6789 at URL [http://0.0.0.0:6789](http://0.0.0.0:6789).

### **Release**

Release is intended for maintainers.

- Validate implement progess

- Validate the sematic version layer. Bump for changes.

```bash
declare TARGETED_VERSION=x.x.x
hatch version $TARGETED_VERSION;
```

- Merge, validate, clean and updated CHANGELOG, TODO, README,...

- Using Github CLI to manage release

```bash
gh release create <TAG/>
```

#### **Development Process**

- Implement logic within the `/einvoice-lens/**` directory

- Write your test at `tests/**` and test locally

To test the package locally, execute the following command locally:

```bash
# Rull all
hatch run test

# Run specific test
hatch run test tests/endpoint/$endpoint_name/$test_file

# Run only last failed case
hatch run test --last-failed
```

- Create Pull Request PR and write your changelog
