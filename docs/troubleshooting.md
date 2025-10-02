# Troubleshooting

## **Overview**

The troubleshooting part for package issues

## **Issues**

You're seeing this AssertionError because the two strings look identical to the human eye—Lê Hoàng Minh Phương—but are encoded differently in Unicode:

- One uses composed characters (NFC): ê, à, ơ, ư
- The other uses decomposed characters (NFD): e + ̂, a + ̀, o + ̛, u + ̛

This causes string comparison to fail even though the visual output is the same.
