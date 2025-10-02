# Troubleshooting

## **Overview**

The troubleshooting part for package issues

## **Issues**

### Unicode format

You're seeing this AssertionError because the two strings look identical to the human eye—Lê Hoàng Minh Phương—but are encoded differently in Unicode:

- One uses composed characters (NFC): ê, à, ơ, ư
- The other uses decomposed characters (NFD): e + ̂, a + ̀, o + ̛, u + ̛

This causes string comparison to fail even though the visual output is the same.

### Markdown images are not rendered in Pypi site

Explaination:

- PyPI is not an image host, so images are not rendered on the site.

Solution: Use the raw URL instead as a workaround.

From: <https://github.com/pypi/warehouse/issues/5246>
