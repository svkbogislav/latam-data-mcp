---
title: "I built an MCP server that gives AI agents reliable Latin America data"
published: false
tags: mcp, ai, python, fintech
---

If you've built an AI agent that has to touch Latin America — validate a
customer's tax ID, confirm a bank account before a payout, quote a price in
the right currency, or just know whether next Tuesday is a holiday in Chile —
you've probably discovered the data is scattered, undocumented, and often
Spanish-only. Every country has its own tax-ID format, its own check-digit
math, its own official exchange rate, its own holiday calendar.

I kept re-solving this, so I turned it into an MCP server: **latam-data-mcp**.

## What it does

17 tools across 15+ Latin American countries. A few highlights:

- **`validate_tax_id`** — real check-digit validation for 15 countries: Chile
  RUT, Argentina CUIT/CUIL, Mexico RFC, Brazil CPF/CNPJ (including the new 2026
  alphanumeric CNPJ), Colombia NIT, Peru RUC, Uruguay, Ecuador, Paraguay,
  Venezuela, Guatemala, Dominican Republic, Panama (RUC+DV), Costa Rica, Bolivia.
- **`validate_bank_account`** — Mexico CLABE and Argentina CBU/CVU, with the
  check digit verified and the bank/branch/account decoded. Catches transposed
  digits *before* a transfer bounces.
- **`validate_pix_key`** — validate a Brazilian PIX key of any type (CPF, CNPJ,
  e-mail, phone, or random UUID).
- **FX & indicators** — Argentina's blue vs official rate, Chile's UF/UTM,
  Brazil's SELIC/CDI/IPCA, Colombia's official TRM, Costa Rica's colón rate, and
  a `currency_convert` helper across 18 LatAm currencies.
- **`business_days`** — holiday-aware working-day math per country, for SLAs,
  payroll and settlement dates.

Every data source is a free public API (no keys) or a pure local algorithm.
The tax-ID and bank validators are pure math — no network, no rate limits,
nothing to break. The Panama RUC check-digit algorithm was verified against 62
real RUCs from the official tax-authority list.

## Try it

Add it to your MCP client — `uvx` runs it straight from PyPI, no install step:

```json
{
  "mcpServers": {
    "latam-data": {
      "command": "uvx",
      "args": ["latam-data-mcp"]
    }
  }
}
```

Then just ask your agent things like *"Is this CLABE valid and which bank is
it — 646180110400000007?"* or *"Convert 50,000 CLP to BRL"* or *"How many
business days between 2026-09-01 and 2026-09-30 in Chile?"*.

Prefer a hosted endpoint? There's one at `https://latam-data.fastmcp.app/mcp`.

## Honest ask

I'm a solo founder in Chile building this in the open. If you're working on
agents for LatAm fintech, e-commerce, logistics or compliance, I'd genuinely
value your feedback — what country or data source should I add next? What's
missing?

- Code (MIT): https://github.com/svkbogislav/latam-data-mcp
- PyPI: https://pypi.org/project/latam-data-mcp/

Thanks for reading. 🇨🇱
