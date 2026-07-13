"""Bank-account / interbank-code validation for Latin America.

Pure check-digit algorithms, no network calls:
- Mexico  CLABE (18 digits, weighted mod-10)
- Argentina CBU  (22 digits, two mod-10 check digits)

Bank-code lookup covers the largest institutions; unknown codes still
validate and return the numeric code.
"""

from __future__ import annotations

import re

# --- Mexico: CLABE bank codes (largest institutions; extend as needed) ------
_CLABE_BANKS = {
    "002": "Banamex", "012": "BBVA México", "014": "Santander", "019": "Banjército",
    "021": "HSBC", "030": "Banco del Bajío", "036": "Inbursa", "042": "Mifel",
    "044": "Scotiabank", "058": "Banregio", "072": "Banorte", "127": "Banco Azteca",
    "137": "BanCoppel", "166": "Banco del Bienestar", "646": "STP", "652": "Credit Suisse",
    "638": "Nu México",
}

# --- Argentina: CBU bank codes (first 3 digits; largest institutions) -------
_CBU_BANKS = {
    "007": "Banco de Galicia", "011": "Banco de la Nación Argentina",
    "015": "ICBC", "017": "BBVA Argentina", "020": "Banco de la Provincia de Buenos Aires",
    "034": "Banco Patagonia", "044": "Banco Hipotecario", "072": "Banco Santander Río",
    "150": "HSBC Bank Argentina", "191": "Banco Credicoop", "285": "Banco Macro",
    "299": "Banco Comafi",
}


def validate_clabe_mx(value: str) -> dict:
    clean = re.sub(r"[.\-\s]", "", value)
    if not re.fullmatch(r"[0-9]{18}", clean):
        return {"valid": False, "reason": "CLABE must be 18 digits"}
    weights = [3, 7, 1]
    total = sum((int(d) * weights[i % 3]) % 10 for i, d in enumerate(clean[:17]))
    expected = (10 - (total % 10)) % 10
    if int(clean[17]) != expected:
        return {"valid": False, "reason": f"check digit mismatch (expected {expected})"}
    bank_code = clean[:3]
    return {
        "valid": True,
        "formatted": clean,
        "bank_code": bank_code,
        "bank_name": _CLABE_BANKS.get(bank_code, "unknown (not in built-in catalog)"),
        "branch_code": clean[3:6],
        "account_number": clean[6:17],
        "check_digit": clean[17],
    }


def _cbu_check_digit(block: str) -> str:
    weights = (3, 1, 7, 9)
    total = sum(int(n) * weights[i % 4] for i, n in enumerate(reversed(block)))
    return str((10 - total) % 10)


def validate_cbu_ar(value: str) -> dict:
    clean = re.sub(r"[.\-\s]", "", value)
    if not re.fullmatch(r"[0-9]{22}", clean):
        return {"valid": False, "reason": "CBU must be 22 digits"}
    if _cbu_check_digit(clean[:7]) != clean[7]:
        return {"valid": False, "reason": "first block check digit mismatch (bank/branch)"}
    if _cbu_check_digit(clean[8:21]) != clean[21]:
        return {"valid": False, "reason": "second block check digit mismatch (account)"}
    bank_code = clean[:3]
    return {
        "valid": True,
        "formatted": f"{clean[:8]} {clean[8:]}",
        "bank_code": bank_code,
        "bank_name": _CBU_BANKS.get(bank_code, "unknown (not in built-in catalog)"),
        "branch_code": clean[3:7],
        "account_number": clean[8:21],
    }


BANK_VALIDATORS = {
    "MX": ("CLABE", validate_clabe_mx),
    "AR": ("CBU", validate_cbu_ar),
}
