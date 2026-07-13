---
title: "Construí un servidor MCP que le da a los agentes de IA datos confiables de Latinoamérica"
published: false
tags: mcp, ia, python, fintech
---

Si construiste un agente de IA que tiene que operar con Latinoamérica —validar
el RUT de un cliente, confirmar una cuenta bancaria antes de un pago, cotizar un
precio en la moneda correcta, o simplemente saber si el próximo martes es
feriado en Chile— seguramente descubriste que los datos están dispersos, sin
documentar y muchas veces solo en español. Cada país tiene su propio formato de
ID tributario, su propia matemática de dígito verificador, su tipo de cambio
oficial, su calendario de feriados.

Me cansé de re-resolver esto, así que lo convertí en un servidor MCP:
**latam-data-mcp**.

## Qué hace

17 herramientas en 15+ países de Latinoamérica. Algunas destacadas:

- **`validate_tax_id`** — validación con dígito verificador real para 15 países:
  RUT de Chile, CUIT/CUIL de Argentina, RFC de México, CPF/CNPJ de Brasil
  (incluido el nuevo CNPJ alfanumérico 2026), NIT de Colombia, RUC de Perú,
  Uruguay, Ecuador, Paraguay, Venezuela, Guatemala, República Dominicana, Panamá
  (RUC+DV), Costa Rica, Bolivia.
- **`validate_bank_account`** — CLABE de México y CBU/CVU de Argentina, con el
  dígito verificador validado y el banco/sucursal/cuenta decodificados. Atrapa
  dígitos transpuestos *antes* de que rebote una transferencia.
- **`validate_pix_key`** — valida una clave PIX brasileña de cualquier tipo (CPF,
  CNPJ, email, teléfono o UUID aleatorio).
- **Cambio e indicadores** — dólar blue vs oficial de Argentina, UF/UTM de Chile,
  SELIC/CDI/IPCA de Brasil, TRM oficial de Colombia, colón de Costa Rica, y un
  `currency_convert` entre 18 monedas latinoamericanas.
- **`business_days`** — cálculo de días hábiles con feriados por país, para SLAs,
  nóminas y fechas de liquidación.

Todas las fuentes son APIs públicas gratuitas (sin API keys) o algoritmos
locales. Los validadores tributarios y bancarios son matemática pura —sin red,
sin límites de tasa, nada que se rompa. El algoritmo del RUC de Panamá se
verificó contra 62 RUCs reales del listado oficial de la DGI.

## Pruébalo

Agrégalo a tu cliente MCP — `uvx` lo corre directo desde PyPI, sin instalar nada:

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

Después pídele a tu agente cosas como *"¿Es válida esta CLABE y de qué banco es —
646180110400000007?"* o *"Convierte 50.000 CLP a BRL"* o *"¿Cuántos días hábiles
hay entre el 2026-09-01 y el 2026-09-30 en Chile?"*.

¿Prefieres un endpoint hosteado? Hay uno en `https://latam-data.fastmcp.app/mcp`.

## Pedido honesto

Soy un fundador solo en Chile construyendo esto en abierto. Si trabajas en
agentes para fintech, e-commerce, logística o compliance en LatAm, me encantaría
tu feedback: ¿qué país o fuente de datos debería agregar? ¿Qué falta?

- Código (MIT): https://github.com/svkbogislav/latam-data-mcp
- PyPI: https://pypi.org/project/latam-data-mcp/

¡Gracias por leer! 🇨🇱
