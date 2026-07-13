# Distribution checklist — latam-data-mcp

Everything is prepared. The items below need **your** accounts (I can't post as
you), but each is copy-paste ready. Do them when you have a few minutes.

## Status

| Channel | Status |
|---|---|
| PyPI (`uvx latam-data-mcp`) | ✅ live |
| Official MCP registry | ✅ listed (active) |
| GitHub repo (public, MIT) | ✅ live |
| punkpeye/awesome-mcp-servers | ✅ PR open (#10033) — also feeds Glama |
| appcypher/awesome-mcp-servers | ❌ contributions disabled by owner — skip |
| wong2/awesome-mcp-servers | ❌ does not accept PRs — skip |
| Glama (glama.ai) | ⏳ auto-crawls public GitHub MCP repos — should index automatically |

## Your to-do list (copy-paste ready — see sections below once filled in)

1. [ ] PulseMCP — submit via their web form
2. [ ] mcp.so — submit via their web form
3. [ ] Post to r/mcp (Reddit)
4. [ ] (optional) Show HN on Hacker News
5. [ ] (optional) Publish the dev.to article (`docs/launch-article.md`)
6. [ ] (optional) LinkedIn + X posts

<!-- The exact per-channel URLs, form fields and ready-to-paste text are
appended below automatically once the research finishes. -->


---

# Ready-to-paste content (per channel)

## PulseMCP submit

**URL:** https://www.pulsemcp.com/submit

**Campos:** PulseMCP does NOT have a multi-field form. The page has a single URL field and states they ingest entries from the Official MCP Registry daily and process them weekly. Since latam-data-mcp is already published to the official registry as io.github.svkbogislav/latam-data-mcp, it should appear automatically within about a week. To speed it up or fix anything: (1) paste the GitHub repo URL into the URL field on /submit, and (2) if it hasn't shown up in a week, email hello@pulsemcp.com with the repo URL and a one-line description. After it appears, claim ownership on the listing so you can edit it. Field 1 (URL) = the GitHub repo URL below. Optional email body = the paste text below.

**Para pegar:**

```
URL field:
https://github.com/svkbogislav/latam-data-mcp

(Optional) follow-up email to hello@pulsemcp.com if it isn't listed within a week:
Subject: Server submission — LatAm Data MCP (already on the official registry)

Hi PulseMCP team,

I published a server to the official MCP Registry as io.github.svkbogislav/latam-data-mcp and wanted to make sure it gets indexed. Repo: https://github.com/svkbogislav/latam-data-mcp — PyPI: latam-data-mcp.

One line: 19 tools giving AI agents reliable access to Latin American data — tax-ID validation for 15 countries (RUT, CUIT, RFC, CPF/CNPJ, NIT, RUC, etc.), bank-account validation (Mexican CLABE, Argentine CBU/CVU), Brazilian PIX-key validation, plus company lookups, exchange rates, and holiday/business-day math. MIT, Python 3.10+, no API keys. I'd like to claim the listing once it appears.

Thanks,
Sebastián
```

_Nota: PulseMCP is primarily a registry-ingesting directory, not a manual form — the biggest win is that you're already on the official registry, so listing is largely automatic. The action here is mostly (a) drop the repo URL in the /submit field and (b) claim ownership once it appears so you control the description._

## mcp.so submit

**URL:** https://mcp.so/submit

**Campos:** mcp.so accepts public GitHub MCP servers. Paste the GitHub repo URL; it generates a draft you then edit and save (saving auto-publishes). Fill the draft as follows — Name: LatAm Data MCP; GitHub/Repo URL: the repo below; Short description / tagline: the one-liner below; Long description: the body below; Category/Tags: pick Finance/Fintech plus add tags 'latam', 'fintech', 'validation', 'tax-id', 'exchange-rates', 'brazil', 'mexico', 'argentina', 'colombia', 'chile'. For non-GitHub or client submissions they ask you to open a ticket, but a GitHub repo is exactly what this form wants.

**Para pegar:**

```
Repo URL:
https://github.com/svkbogislav/latam-data-mcp

Name:
LatAm Data MCP

Tagline:
The Latin American data layer your AI agent is missing — tax-ID, bank-account & PIX validation, FX rates, company lookups, and holidays across 20 LatAm countries.

Description:
LatAm Data MCP gives AI agents reliable access to Latin American data that is otherwise scattered, undocumented, or Spanish-only. 19 tools, MIT-licensed, Python 3.10+, no API keys — every source is free and public, or a pure local algorithm.

Built for fintech, e-commerce, logistics and compliance agents:
• validate_tax_id — real check-digit math for 15 countries: Chile RUT, Argentina CUIT/CUIL, Mexico RFC, Brazil CPF/CNPJ (incl. the 2026 alphanumeric CNPJ), Colombia NIT, Peru RUC, Uruguay RUT, Ecuador cédula/RUC, Paraguay RUC, Venezuela RIF, Guatemala NIT, Dominican Rep. RNC, Panama RUC+DV, Costa Rica cédula, Bolivia NIT. Returns canonical formatting and person/company/public-entity detection.
• validate_bank_account — check-digit validation for Mexican CLABE (18-digit) and Argentine CBU/CVU (22-digit, incl. Mercado Pago virtual accounts); decodes bank/branch/account so an agent can verify a payout destination before sending money.
• validate_pix_key — validates Brazilian PIX keys (CPF, CNPJ, email, +55 phone, or random UUID) and detects the type.
• Company lookups: full Brazilian federal registry by CNPJ; Costa Rica taxpayer + compliance status (moroso/omiso) for KYC/AML.
• Money & markets: Chile indicators (UF/UTM), Argentina official vs blue rate, Brazil SELIC/CDI/IPCA (+ historical series), Colombia's legally binding TRM (+ history), Costa Rica colón rate, currency conversion, and all 18 LatAm currencies vs USD in one call.
• Time: official holidays for 20 LatAm countries, next holidays, long weekends, and holiday-aware business-day math for SLAs/payroll/settlement.

Install (free, runs locally):
uvx latam-data-mcp

GitHub: https://github.com/svkbogislav/latam-data-mcp
PyPI: https://pypi.org/project/latam-data-mcp/
Official MCP Registry: io.github.svkbogislav/latam-data-mcp
```

_Nota: Lead the draft with the fintech tools — that's the differentiator vs generic FX/holiday servers. Keep the install line as `uvx latam-data-mcp` since it's on PyPI._

## r/mcp Reddit post

**URL:** https://www.reddit.com/r/mcp/submit?type=text

**Campos:** Choose a TEXT post (not link). Title = below (leads with the problem, not the product). Body = Reddit markdown below. Post type: text/self post. Flair: use 'Server' or 'Showcase'/'Self-promotion' flair if the subreddit requires one. Keep it a discussion, not an ad: it leads with the pain, states plainly that you built it, that it's free and open source, and ends asking for feedback. Reply to comments.

**Para pegar:**

```
TITLE:
Making an agent validate a Mexican CLABE or a Brazilian CNPJ is surprisingly painful — so I built an MCP server for LatAm data

BODY (markdown):
If you've built an AI agent that touches Latin America — fintech, e-commerce, logistics, compliance — you've probably hit this: the reference data you need is scattered across a dozen government sites, poorly documented, and usually Spanish-only. Validating a Mexican CLABE, an Argentine CBU, or a Brazilian CNPJ means digging up the check-digit algorithm yourself. Getting Colombia's *legally binding* USD/COP rate (the TRM) or Argentina's blue-market rate means scraping.

I got tired of re-solving this, so I packaged it as an MCP server. It's free, open source (MIT), and needs no API keys — every source is either a free public API or a pure local algorithm.

**The fintech/compliance tools (the ones I couldn't find elsewhere):**

- `validate_tax_id` — real check-digit math for **15 countries**: 🇨🇱 RUT, 🇦🇷 CUIT/CUIL, 🇲🇽 RFC, 🇧🇷 CPF/CNPJ (including the new 2026 alphanumeric CNPJ), 🇨🇴 NIT, 🇵🇪 RUC, 🇺🇾 RUT, 🇪🇨 cédula/RUC, 🇵🇾 RUC, 🇻🇪 RIF, 🇬🇹 NIT, 🇩🇴 RNC, 🇵🇦 RUC+DV, 🇨🇷 cédula, 🇧🇴 NIT. Returns canonical formatting + person/company/public-entity detection.
- `validate_bank_account` — check-digit validation for 🇲🇽 CLABE (18-digit) and 🇦🇷 CBU/CVU (22-digit, incl. Mercado Pago virtual accounts). Decodes bank/branch/account so an agent can sanity-check a payout destination before money moves.
- `validate_pix_key` — validates a 🇧🇷 PIX key (CPF, CNPJ, email, +55 phone, or random UUID) and detects its type.

**Plus the boring-but-useful stuff:** Brazilian company lookup by CNPJ (full federal registry), Costa Rica taxpayer + compliance status (moroso/omiso) for KYC, Chile indicators (UF/UTM), Argentina official vs blue rate, Brazil SELIC/CDI/IPCA + historical series, Colombia TRM + history, currency conversion, all 18 LatAm currencies in one call, and holiday-aware business-day math for 20 countries.

**19 tools total.** The validators have 300+ tests and I checked the algorithms against real published accounts (e.g. bank CLABEs) and against python-stdnum where they overlap (0 disagreements across the countries both cover).

Install is one line:
```
uvx latam-data-mcp
```
Or in your client config:
```json
{
  "mcpServers": {
    "latam-data": { "command": "uvx", "args": ["latam-data-mcp"] }
  }
}
```

Repo: https://github.com/svkbogislav/latam-data-mcp

Full disclosure: I'm the solo dev, based in Chile, and I built this partly as a product I'd like to eventually monetize (a hosted tier). But the whole thing runs locally for free and always will. I'd genuinely like feedback — especially: which country/data gaps hurt you most, and whether the tool outputs are shaped the way an agent actually wants to consume them. What would you add?
```

_Nota: Reddit's self-promo culture is allergic to hype — this version leads with the problem, discloses you're the dev and that a paid tier exists, and ends with a real question. Don't cross-post the identical text to 10 subs the same day; that reads as spam._

## Hacker News — Show HN

**URL:** https://news.ycombinator.com/submit

**Campos:** Two fields: Title and URL (leave the text field blank when you provide a URL). Title MUST start with 'Show HN:' and stay concrete (HN dislikes marketing adjectives). URL = the GitHub repo. Then immediately post the 'first comment' below as a reply to your own submission — this is the HN convention and where you give context. Post during US morning hours (roughly 8–10am ET, weekday) for best odds. Do not ask for upvotes anywhere.

**Para pegar:**

```
TITLE:
Show HN: LatAm Data MCP – tax-ID, bank-account and PIX validation for AI agents

URL:
https://github.com/svkbogislav/latam-data-mcp

FIRST COMMENT (post as a reply to your own submission):
Hi HN. I'm a solo dev in Chile. I kept hitting the same wall building agents that touch Latin America: the reference data you need — tax-ID check digits, interbank account formats, the legally-binding exchange rates — is scattered across government sites, badly documented, and mostly Spanish-only. So I packaged it as an MCP server.

It's 19 tools, MIT-licensed, Python 3.10+, and needs no API keys — every source is either a free public API (BrasilAPI, Banco Central do Brasil, datos.gov.co, Costa Rica's Hacienda, Nager.Date, etc.) or a pure local algorithm.

The parts I couldn't find anywhere else:

- validate_tax_id: real check-digit validation for 15 countries (Chile RUT, Argentina CUIT, Mexico RFC, Brazil CPF/CNPJ incl. the 2026 alphanumeric CNPJ, Colombia NIT, Peru RUC, and more), with canonical formatting and person/company detection.
- validate_bank_account: check-digit validation for Mexican CLABE (18-digit) and Argentine CBU/CVU (22-digit, incl. Mercado Pago virtual accounts), decoding bank/branch/account — so an agent can verify a payout destination before money moves.
- validate_pix_key: validates Brazilian PIX keys (CPF/CNPJ/email/phone/random UUID) and detects the type.

The rest is company lookups (Brazilian CNPJ registry; Costa Rica taxpayer + moroso/omiso compliance status), FX (Argentina official vs blue, Colombia's TRM, Chile UF/UTM, Brazil SELIC/CDI/IPCA + historical series, conversion), and holiday-aware business-day math for 20 countries.

On correctness: the validators have 300+ tests. I verified algorithms against real published accounts and ran a differential against python-stdnum where they overlap — 0 disagreements across the countries both cover (Ecuador is intentionally stricter, following SRI rules rather than stdnum).

Honest about the business: I want this to eventually earn some passive income via an optional hosted endpoint, but the server runs locally for free under MIT and that won't change.

Install: `uvx latam-data-mcp`. Feedback very welcome — especially on which country/data gaps matter most and whether the outputs are shaped the way agents actually want to consume them.
```

_Nota: HN rewards specificity and candor and punishes hype — this leans on concrete algorithms, named data sources, the stdnum differential, and an upfront note about monetization. Title is 74 chars, safely under HN's 80-char limit._

## LinkedIn post (founder voice, Spanish)

**URL:** https://www.linkedin.com/feed/ (usa 'Crear publicación' / Start a post)

**Campos:** Publicación de texto en el feed personal. Tono de fundador, en primera persona, español neutro/chileno. Ángulo: fintech LatAm y agentes de IA. Incluye 1 enlace (el repo) — en LinkedIn conviene poner el enlace al final o en el primer comentario para no penalizar el alcance. Agrega 3–5 hashtags al final. Sin promesas exageradas.

**Para pegar:**

```
Construí algo que me hubiera ahorrado semanas de trabajo, y lo dejé gratis y open source.

Si has desarrollado un agente de IA que opera en Latinoamérica —fintech, e-commerce, logística, compliance— probablemente conoces el dolor: los datos que necesitas están dispersos en sitios de gobierno, mal documentados y casi siempre solo en español. Validar una CLABE mexicana, un CBU argentino o un CNPJ brasileño significa buscar tú mismo el algoritmo del dígito verificador. Obtener la TRM oficial de Colombia o el dólar blue de Argentina significa scrapear.

Empaqueté todo eso como un servidor MCP: LatAm Data MCP. 19 herramientas, licencia MIT, sin API keys —cada fuente es una API pública gratuita o un algoritmo local.

Lo que más me importa (lo difícil de encontrar):

→ validate_tax_id: validación real con dígito verificador para 15 países (RUT chileno, CUIT argentino, RFC mexicano, CPF/CNPJ brasileño —incluyendo el nuevo CNPJ alfanumérico 2026—, NIT, RUC y más). Detecta si es persona, empresa o entidad pública.

→ validate_bank_account: validación de CLABE (México, 18 dígitos) y CBU/CVU (Argentina, 22 dígitos, incluye cuentas virtuales tipo Mercado Pago). Decodifica banco, sucursal y cuenta —para verificar un destino de pago antes de mover dinero.

→ validate_pix_key: valida llaves PIX de Brasil (CPF, CNPJ, email, teléfono +55 o UUID) y detecta el tipo.

Además: consulta de empresas por CNPJ, estado de cumplimiento tributario en Costa Rica (moroso/omiso) para KYC, indicadores de Chile (UF/UTM), tasas de cambio, series históricas y cálculo de días hábiles con feriados de 20 países.

Soy fundador solo, desde Chile. Se instala en una línea (uvx latam-data-mcp) y corre en tu máquina, gratis. Me encantaría feedback de quienes construyen sobre datos de la región: ¿qué país o dato les falta más?

Repo en el primer comentario 👇

#MCP #IA #FintechLatAm #DesarrolloDeSoftware #OpenSource
```

_Nota: Primer comentario para poner el enlace (mejora el alcance): 'Repo y detalle técnico: https://github.com/svkbogislav/latam-data-mcp — instalación: uvx latam-data-mcp'. Mantén el enlace fuera del cuerpo del post._

## X/Twitter thread (4 tweets)

**URL:** https://x.com/compose/post

**Campos:** Hilo de 4 tweets. Tweet 1 = gancho con el problema (evita hype). Tweet 2 = las 3 herramientas fintech diferenciadoras. Tweet 3 = qué más trae + prueba de correctitud. Tweet 4 = instalación + repo + CTA de feedback. Cada tweet <280 caracteres. Puede ir en inglés (audiencia dev de MCP mayormente en inglés) — abajo va en inglés con hashtags #MCP.

**Para pegar:**

```
1/
Building an AI agent that touches Latin America? The data you need — tax-ID check digits, bank account formats, the legally-binding FX rates — is scattered across gov sites, undocumented, and Spanish-only.

I packaged it as an MCP server. Free, open source, no API keys. 🧵

2/
The fintech tools I couldn't find anywhere else:

• validate_tax_id — real check-digit math for 15 countries (RUT, CUIT, RFC, CPF/CNPJ incl. 2026 alphanumeric CNPJ…)
• validate_bank_account — MX CLABE + AR CBU/CVU (incl. Mercado Pago)
• validate_pix_key — Brazilian PIX keys

3/
Plus: Brazilian company lookup by CNPJ, Costa Rica compliance status (moroso/omiso) for KYC, Argentina official vs blue rate, Colombia's TRM, Chile UF/UTM, currency conversion, and holiday-aware business-day math for 20 countries. 19 tools total.

Validators: 300+ tests, checked vs real accounts.

4/
Runs locally, one line:

uvx latam-data-mcp

MIT, Python 3.10+. I'm a solo dev in Chile — feedback very welcome, especially on which country/data gaps hurt you most.

https://github.com/svkbogislav/latam-data-mcp

#MCP #AIagentsX #FintechLatAm
```

_Nota: Keep the repo link in the last tweet (links in the first tweet can suppress reach). Honest, concrete, no 'revolutionary/game-changer' language. If you prefer Spanish for a LatAm-dev audience, the same 4-tweet structure translates directly._
