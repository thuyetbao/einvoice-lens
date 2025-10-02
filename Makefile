#!/bin/bash

# Settings
SHELL := /bin/bash
.DEFAULT_GOAL := info
PACKAGE_FOLDER := einvoice-lens

# Avoid
.PHONY: venv build tests docs

venv:
	@uv venv --allow-existing --color "auto" --python 3.12.8 --seed venv

install-build-backend:
	@uv pip install "wheel>=0.45.1,<0.50.0" "hatch>=1.12.1,<1.15.0" "setuptools<80.0.0" --no-cache

install-dev:
	@uv pip install -r requirements-dev.txt --no-cache

install-package:
	@uv pip install $$(hatch dep show requirements);

install-docs:
	@uv pip install -r requirements-docs.txt --no-cache

install: install-build-backend install-dev install-docs install-package

enforce-install:
	@pre-commit install

ruff:
	@hatch run ruff check ${PACKAGE_FOLDER};

pack-env:
	hatch env create

pack-deps:
	@hatch dep show requirements;

pack-build:
	@hatch build;

pack-test:
	@hatch run test;

docs:
	@hatch run docs;

docs-build:
	mkdocs build

docs-serve:
	mkdocs serve --dev-addr "0.0.0.0:6789" --watch mkdocs.yaml  --watch docs/ --watch README.md --watch CHANGELOG.md --watch TODO.md

# Alias
docs-up: docs-serve

info:
	@echo -e "==============================================================================="
	@echo -e "Package:\t\t\e[34mEinvoice Lens\e[0m"
	@echo -e "On version:\t\t\e[34m$$(hatch version)\e[0m"
	@echo -e "==============================================================================="
	@echo -e ""
	@echo -e "> Supported target ============================================================"
	@echo -e "make info: \t\tGet info of the package"
	@echo -e "make install-dev: \tInstall development dependencies"
	@echo -e "make ruff: \t\tLint"
	@echo -e "make docs: \t\tServing local development documentation"
	@echo -e "make test: \t\tTest services"
	@echo -e "make clean: \t\tCleaning bytes codes, cached folder and self generated output"
	@echo -e ""

info-release:
	@gh release list --exclude-drafts --exclude-pre-releases --repo "thuyetbao/einvoice-lens"

info-release-latest:
	@gh release list --exclude-drafts --exclude-pre-releases --repo "thuyetbao/einvoice-lens" --limit 1

release:
	gh release create "v$$(hatch version)";

clean:
	@echo "";
	@echo -e "\e[34m[A] Removed self-generated folder by dependencies or package itself\e[0m";
	@echo -e "\t[+] Remove folders: \`dist\`, \`build\`, \`logs\`";
	@if [ -d dist ] ; then rm -r dist; fi;
	@if [ -d build ] ; then rm -r build; fi;
	@if [ -d logs ] ; then rm -r logs; fi;
	@echo -e "\t[+] Remove egg-info";
	@find ./ -type f -name '*.egg-info' -delete;
	@echo "";
	@echo -e "\e[34m[B] Removing packages folders\e[0m";
	@echo -e "\e[34m[1] Cleaning bytecode in current directory tree...\e[0m";
	@pyclean -v .;
	@echo -e "\t[+] Remove cache from \`pytest\` module";
	@find ./ -maxdepth 1 -type d -name '.pytest_cache' | xargs --no-run-if-empty rm -rf;
	@echo -e "\t[+] Remove cache from \`ruff\` module";
	@find ./ -maxdepth 1 -type d -name '.ruff_cache' | xargs --no-run-if-empty rm -rf;
	@echo -e "\t[+] Remove coverage test";
	@find ./ -type f -name '*.coverage' -delete;
	@echo "";
	@echo -e "\e[32m[Status] Cleared successfully\e[0m";
