# LatAm Data MCP

<!-- mcpName: io.github.svkbogislav/latam-data-mcp -->

The Latin American data layer your AI agent is missing.

An MCP server that gives agents reliable access to LatAm data that is
otherwise scattered, undocumented, or Spanish-only: tax-ID validation
for 12 countries, live economic indicators, exchange rates (including
Argentina's blue rate and Colombia's legally binding TRM), Brazilian
company lookups, holidays, and business-day math.

## Tools (11)

### Identity & companies

| Tool | What it does |
|---|---|
| `validate_tax_id` | Validates national tax IDs with real check-digit math for **12 countries**: 🇨🇱 RUT, 🇦🇷 CUIT/CUIL, 🇲🇽 RFC, 🇧🇷 CPF/CNPJ (incl. 2026 alphanumeric CNPJs), 🇨🇴 NIT, 🇵🇪 RUC, 🇺🇾 RUT, 🇪🇨 cédula/RUC, 🇵🇾 RUC, 🇻🇪 RIF, 🇬🇹 NIT, 🇩🇴 RNC. Returns canonical formatting and person/company/public-entity detection. |
| `brazil_company_lookup` | Full federal-registry data for any Brazilian company by CNPJ: legal name, status, size, main activity, capital, address, partners. |

### Money & markets

| Tool | What it does |
|---|---|
| `chile_indicators` | UF, UTM, USD, EUR and more, in CLP. |
| `argentina_exchange_rates` | Official vs **blue** rate for USD/EUR. |
| `brazil_market_rates` | SELIC, CDI, IPCA. |
| `colombia_official_trm` | The legally binding USD/COP rate with validity dates. |
| `latam_exchange_rates` | All 18 LatAm currencies vs USD in one call. |

### Time & calendars

| Tool | What it does |
|---|---|
| `public_holidays` | Official holidays for 20 LatAm countries, any year. |
| `next_holidays` | Upcoming holidays from today. |
| `long_weekends` | Long weekends with bridge-day analysis. |
| `business_days` | Working-day count between dates, holiday-aware — for SLA, payroll, logistics, settlement math. |

## Install (free — runs on your machine)

No download or clone needed. Add this to your MCP client config — `uvx`
fetches and runs the server straight from this repo:

**Claude Desktop / Cursor / Claude Code** (`mcpServers` block):

```json
{
  "mcpServers": {
    "latam-data": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/svkbogislav/latam-data-mcp", "latam-data-mcp"]
    }
  }
}
```

Or install it as a command:

```bash
uvx --from git+https://github.com/svkbogislav/latam-data-mcp latam-data-mcp
# or:  pipx install git+https://github.com/svkbogislav/latam-data-mcp
```

Requires Python 3.10+. No API keys — every data source is free and public.

## Hosted (managed) endpoint

A always-on hosted instance is available at `https://latam-data.fastmcp.app/mcp`
(Streamable HTTP, authenticated). Use this if you'd rather not run anything
locally.

## Develop

```bash
python3.11 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python server.py     # stdio; set PORT=8000 for Streamable HTTP
```

## Tests

```bash
.venv/bin/pytest              # offline suite: validators + MCP protocol layer
.venv/bin/pytest -m live      # integration tests against the real upstream APIs
```

Validators are verified against python-stdnum's reference algorithms and
real IDs of public institutions (Banco do Brasil, SUNAT, DIAN, UTE, U. de Chile).

## Data sources

All free public APIs, no keys: gael.cloud (Chile), Bluelytics (Argentina),
BrasilAPI (Brazil), datos.gov.co (Colombia), open.er-api.com (regional FX),
Nager.Date (holidays). Tax-ID validation is pure local math — zero
dependencies, zero latency, nothing to break.

## Roadmap

- [ ] Historical series (UF, USD, TRM)
- [ ] Deploy free tier + directory listings (Smithery, PulseMCP, mcp.so)
- [ ] Monetization via MCPize (85% rev share) once free tier has weekly active users
- [ ] Electronic invoicing requirements per country (static knowledge tool)
