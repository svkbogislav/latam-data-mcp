"""National tax-ID validators for 12 Latin American countries.

Pure algorithms (check-digit math), no network calls. Algorithm sources:
python-stdnum (the reference implementation used across the industry)
plus each country's tax-authority conventions.

All digit patterns are ASCII-anchored ([0-9], never \\d) so that non-ASCII
Unicode digits (full-width, Arabic-Indic, superscript) are rejected rather
than silently accepted or crashing int().
"""

from __future__ import annotations

import re
from datetime import date

# ---------------------------------------------------------------------------
# Chile — RUT
# ---------------------------------------------------------------------------

def validate_rut_cl(value: str) -> dict:
    clean = re.sub(r"[.\-\s]", "", value).upper()
    if not re.fullmatch(r"[0-9]{7,8}[0-9K]", clean):
        return {"valid": False, "reason": "RUT must be 7-8 digits plus a check digit (0-9 or K)"}
    body, dv = clean[:-1], clean[-1]
    if int(body) == 0:
        return {"valid": False, "reason": "RUT cannot be zero"}
    total, factor = 0, 2
    for digit in reversed(body):
        total += int(digit) * factor
        factor = 2 if factor == 7 else factor + 1
    remainder = 11 - (total % 11)
    expected = "0" if remainder == 11 else "K" if remainder == 10 else str(remainder)
    if dv != expected:
        return {"valid": False, "reason": f"check digit mismatch (expected {expected})"}
    formatted = f"{int(body):,}".replace(",", ".") + f"-{dv}"
    entity = "company (heuristic: RUT >= 50,000,000)" if int(body) >= 50_000_000 else "person (heuristic: RUT < 50,000,000)"
    return {"valid": True, "formatted": formatted, "type": entity}


# ---------------------------------------------------------------------------
# Argentina — CUIT / CUIL
# ---------------------------------------------------------------------------

_CUIT_KINDS = {
    "20": "male person", "23": "person (either)", "24": "person (either)",
    "27": "female person", "30": "company", "33": "company", "34": "company",
    "50": "legal entity", "51": "legal entity", "55": "legal entity",
}


def validate_cuit_ar(value: str) -> dict:
    clean = re.sub(r"[.\-\s]", "", value)
    if not re.fullmatch(r"[0-9]{11}", clean):
        return {"valid": False, "reason": "CUIT/CUIL must be 11 digits"}
    if clean[:2] not in _CUIT_KINDS:
        return {"valid": False,
                "reason": "prefix must be an AFIP-issued kind (20, 23, 24, 27, 30, 33, 34, 50, 51, 55)"}
    weights = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(clean[:10], weights))
    mod = 11 - (total % 11)
    # AFIP convention: verificador 11 -> 0; verificador 10 -> check digit 9
    # (the taxpayer's prefix is reassigned, e.g. 20 -> 23). Matches python-stdnum.
    expected = 0 if mod == 11 else 9 if mod == 10 else mod
    if int(clean[10]) != expected:
        return {"valid": False, "reason": f"check digit mismatch (expected {expected})"}
    return {"valid": True, "formatted": f"{clean[:2]}-{clean[2:10]}-{clean[10]}",
            "type": _CUIT_KINDS[clean[:2]]}


# ---------------------------------------------------------------------------
# Mexico — RFC  (format + embedded date only; see note)
# ---------------------------------------------------------------------------

def validate_rfc_mx(value: str) -> dict:
    clean = value.strip().upper().replace(" ", "")
    person = re.fullmatch(r"[A-ZÑ&]{4}[0-9]{6}[A-Z0-9]{3}", clean)
    company = re.fullmatch(r"[A-ZÑ&]{3}[0-9]{6}[A-Z0-9]{3}", clean)
    if not (person or company):
        return {"valid": False, "reason": "RFC format is 4 letters + 6 date digits + 3 chars "
                                          "(people) or 3 letters + 6 date digits + 3 chars (companies)"}
    date_part = clean[4:10] if person else clean[3:9]
    yy = int(date_part[:2])
    try:
        date(2000 + yy if yy < 30 else 1900 + yy, int(date_part[2:4]), int(date_part[4:6]))
    except ValueError:
        return {"valid": False, "reason": "embedded date is not a real date"}
    return {"valid": True, "formatted": clean, "type": "person" if person else "company",
            "check_digit_verified": False,
            "note": "format and embedded date validated; the RFC check character is not "
                    "algorithmically verifiable because SAT-issued RFCs deviate from the standard algorithm"}


# ---------------------------------------------------------------------------
# Colombia — NIT
# ---------------------------------------------------------------------------

def validate_nit_co(value: str) -> dict:
    clean = re.sub(r"[.\-\s]", "", value)
    if not re.fullmatch(r"[0-9]{8,16}", clean):
        return {"valid": False, "reason": "NIT must be 8-16 digits (including the check digit)"}
    if int(clean) == 0:
        return {"valid": False, "reason": "NIT cannot be zero"}
    body, dv = clean[:-1], int(clean[-1])
    weights = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
    total = sum(int(d) * w for d, w in zip(reversed(body), weights))
    mod = total % 11
    expected = mod if mod < 2 else 11 - mod
    if dv != expected:
        return {"valid": False, "reason": f"check digit mismatch (expected {expected})"}
    return {"valid": True, "formatted": f"{body}-{dv}"}


# ---------------------------------------------------------------------------
# Peru — RUC
# ---------------------------------------------------------------------------

def validate_ruc_pe(value: str) -> dict:
    clean = re.sub(r"[.\-\s]", "", value)
    if not re.fullmatch(r"[0-9]{11}", clean):
        return {"valid": False, "reason": "RUC must be 11 digits"}
    if clean[:2] not in {"10", "15", "17", "20"}:
        return {"valid": False, "reason": "RUC must start with 10, 15, 17 or 20"}
    weights = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(clean[:10], weights))
    expected = (11 - (total % 11)) % 10
    if int(clean[10]) != expected:
        return {"valid": False, "reason": f"check digit mismatch (expected {expected})"}
    return {"valid": True, "formatted": clean,
            "type": "person" if clean[:2] in {"10", "15", "17"} else "company"}


# ---------------------------------------------------------------------------
# Brazil — CPF (people) and CNPJ (companies, incl. 2026 alphanumeric format)
# ---------------------------------------------------------------------------

def _validate_cpf_br(clean: str) -> dict:
    if not re.fullmatch(r"[0-9]{11}", clean):
        return {"valid": False, "reason": "CPF must be 11 digits"}
    if int(clean) == 0 or clean == clean[0] * 11:
        return {"valid": False, "reason": "CPF with all digits equal is not issued"}
    d1 = sum((10 - i) * int(clean[i]) for i in range(9))
    d1 = (11 - d1) % 11 % 10
    d2 = sum((11 - i) * int(clean[i]) for i in range(9)) + 2 * d1
    d2 = (11 - d2) % 11 % 10
    if clean[9:] != f"{d1}{d2}":
        return {"valid": False, "reason": f"check digits mismatch (expected {d1}{d2})"}
    formatted = f"{clean[:3]}.{clean[3:6]}.{clean[6:9]}-{clean[9:]}"
    return {"valid": True, "formatted": formatted, "type": "person", "id_type": "CPF"}


def _validate_cnpj_br(clean: str) -> dict:
    if not re.fullmatch(r"[0-9A-Z]{12}[0-9]{2}", clean):
        return {"valid": False, "reason": "CNPJ must be 12 alphanumeric characters plus 2 numeric check digits"}
    if clean[:12] == "0" * 12:
        return {"valid": False, "reason": "CNPJ root cannot be all zeros"}
    values = [ord(c) - 48 for c in clean[:12]]
    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    d1 = (11 - sum(w * v for w, v in zip(w1, values))) % 11 % 10
    w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    d2 = (11 - sum(w * v for w, v in zip(w2, values + [d1]))) % 11 % 10
    if clean[12:] != f"{d1}{d2}":
        return {"valid": False, "reason": f"check digits mismatch (expected {d1}{d2})"}
    formatted = f"{clean[:2]}.{clean[2:5]}.{clean[5:8]}/{clean[8:12]}-{clean[12:]}"
    alphanumeric = not clean[:12].isdigit()
    return {"valid": True, "formatted": formatted, "type": "company", "id_type": "CNPJ",
            "alphanumeric_format": alphanumeric}


def validate_br(value: str) -> dict:
    clean = re.sub(r"[.\-/\s]", "", value).upper()
    if len(clean) == 11 and re.fullmatch(r"[0-9]{11}", clean):
        return _validate_cpf_br(clean)
    if len(clean) == 14:
        return _validate_cnpj_br(clean)
    return {"valid": False,
            "reason": "expected a CPF (11 digits) or a CNPJ (14 characters)"}


# ---------------------------------------------------------------------------
# Uruguay — RUT (DGI)
# ---------------------------------------------------------------------------

def validate_rut_uy(value: str) -> dict:
    clean = re.sub(r"[.\-\s]", "", value.upper().replace("UY", ""))
    if not re.fullmatch(r"[0-9]{12}", clean):
        return {"valid": False, "reason": "Uruguayan RUT must be 12 digits"}
    if not "01" <= clean[:2] <= "22":
        return {"valid": False, "reason": "registration office prefix must be between 01 and 22"}
    if clean[2:8] == "000000":
        return {"valid": False, "reason": "registration number cannot be all zeros"}
    if clean[8:11] != "001":
        return {"valid": False, "reason": "digits 9-11 must be '001'"}
    weights = (4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
    total = sum(int(n) * w for w, n in zip(weights, clean))
    expected = -total % 11
    if expected == 10:
        return {"valid": False, "reason": "number cannot have a valid check digit"}
    if int(clean[11]) != expected:
        return {"valid": False, "reason": f"check digit mismatch (expected {expected})"}
    formatted = f"{clean[:2]}-{clean[2:8]}-{clean[8:11]}-{clean[11]}"
    return {"valid": True, "formatted": formatted, "type": "registered taxpayer (DGI)"}


# ---------------------------------------------------------------------------
# Ecuador — Cédula (10 digits) and RUC (13 digits)
# ---------------------------------------------------------------------------

def _ec_province_ok(clean: str) -> bool:
    return "01" <= clean[:2] <= "24" or clean[:2] in {"30", "50"}


def _validate_cedula_ec(clean: str) -> dict:
    if not _ec_province_ok(clean):
        return {"valid": False, "reason": "province code must be 01-24, 30 or 50"}
    if clean[2] > "6":
        return {"valid": False, "reason": "third digit must be 0-6 for a cédula"}
    fold = lambda x: x - 9 if x > 9 else x
    if sum(fold((2, 1)[i % 2] * int(n)) for i, n in enumerate(clean)) % 10 != 0:
        return {"valid": False, "reason": "check digit mismatch"}
    return {"valid": True, "formatted": clean, "type": "person", "id_type": "cédula"}


def _ec_checksum_ok(clean: str, weights: list[int]) -> bool:
    return sum(w * int(n) for w, n in zip(weights, clean)) % 11 == 0


def _validate_ruc_ec(clean: str) -> dict:
    if not _ec_province_ok(clean):
        return {"valid": False, "reason": "province code must be 01-24, 30 or 50"}
    third = clean[2]

    def natural_person() -> dict | None:
        core = _validate_cedula_ec(clean[:10])
        if core["valid"] and clean[10:] != "000":
            return {"valid": True, "formatted": clean, "type": "natural person", "id_type": "RUC"}
        return None

    if third in "012345":
        person = natural_person()
        if person:
            return person
        return {"valid": False, "reason": "check digit mismatch or invalid establishment suffix"}
    if third == "6":
        # Public entity, or a natural person whose cédula legitimately has third digit 6.
        if _ec_checksum_ok(clean, [3, 2, 7, 6, 5, 4, 3, 2, 1]) and clean[9:] != "0000":
            return {"valid": True, "formatted": clean, "type": "public entity", "id_type": "RUC"}
        person = natural_person()
        if person:
            return person
        return {"valid": False, "reason": "check digit mismatch (neither public-entity nor natural-person rule holds)"}
    if third == "9":
        if _ec_checksum_ok(clean, [4, 3, 2, 7, 6, 5, 4, 3, 2, 1]) and clean[10:] != "000":
            return {"valid": True, "formatted": clean, "type": "private company", "id_type": "RUC"}
        return {"valid": False, "reason": "check digit mismatch or invalid establishment suffix"}
    return {"valid": False, "reason": "third digit must be 0-6 or 9"}


def validate_ec(value: str) -> dict:
    clean = re.sub(r"[.\-\s]", "", value)
    if re.fullmatch(r"[0-9]{10}", clean):
        return _validate_cedula_ec(clean)
    if re.fullmatch(r"[0-9]{13}", clean):
        return _validate_ruc_ec(clean)
    return {"valid": False, "reason": "expected a cédula (10 digits) or a RUC (13 digits)"}


# ---------------------------------------------------------------------------
# Paraguay — RUC
# ---------------------------------------------------------------------------

def validate_ruc_py(value: str) -> dict:
    clean = re.sub(r"[.\-\s]", "", value)
    if not re.fullmatch(r"[0-9]{2,9}", clean):
        return {"valid": False, "reason": "RUC must be 2 to 9 digits (including the check digit)"}
    if int(clean) == 0:
        return {"valid": False, "reason": "RUC cannot be zero"}
    body, dv = clean[:-1], clean[-1]
    total = sum((i + 2) * int(n) for i, n in enumerate(reversed(body)))
    expected = str((-total % 11) % 10)
    if dv != expected:
        return {"valid": False, "reason": f"check digit mismatch (expected {expected})"}
    entity = ("company (heuristic: 8-digit RUC starting with 80)"
              if len(clean) == 9 and clean.startswith("80") else "person or entity")
    return {"valid": True, "formatted": f"{body}-{dv}", "type": entity}


# ---------------------------------------------------------------------------
# Venezuela — RIF
# ---------------------------------------------------------------------------

_RIF_PREFIX = {"V": 4, "E": 8, "J": 12, "P": 16, "G": 20}
_RIF_KIND = {"V": "Venezuelan person", "E": "foreign person", "J": "company",
             "P": "passport holder", "G": "government entity"}


def validate_rif_ve(value: str) -> dict:
    clean = re.sub(r"[.\-\s]", "", value).upper()
    if not re.fullmatch(r"[VEJPG][0-9]{9}", clean):
        return {"valid": False, "reason": "RIF must be a letter (V/E/J/P/G) followed by 9 digits"}
    if clean[1:9] == "00000000":
        return {"valid": False, "reason": "RIF body cannot be all zeros"}
    weights = (3, 2, 7, 6, 5, 4, 3, 2)
    c = _RIF_PREFIX[clean[0]]
    c += sum(w * int(n) for w, n in zip(weights, clean[1:9]))
    expected = "00987654321"[c % 11]
    if clean[9] != expected:
        return {"valid": False, "reason": f"check digit mismatch (expected {expected})"}
    return {"valid": True, "formatted": f"{clean[0]}-{clean[1:9]}-{clean[9]}",
            "type": _RIF_KIND[clean[0]]}


# ---------------------------------------------------------------------------
# Guatemala — NIT
# ---------------------------------------------------------------------------

def validate_nit_gt(value: str) -> dict:
    clean = re.sub(r"[.\-\s]", "", value).upper()
    if not re.fullmatch(r"[0-9]{1,11}[0-9K]", clean) or len(clean) < 2:
        return {"valid": False, "reason": "NIT must be 2-12 characters: digits plus a check digit (0-9 or K)"}
    body, dv = clean[:-1], clean[-1]
    if int(body) == 0:
        return {"valid": False, "reason": "NIT cannot be zero"}
    c = -sum(i * int(n) for i, n in enumerate(reversed(body), 2)) % 11
    expected = "K" if c == 10 else str(c)
    if dv != expected:
        return {"valid": False, "reason": f"check digit mismatch (expected {expected})"}
    return {"valid": True, "formatted": f"{body}-{dv}"}


# ---------------------------------------------------------------------------
# Dominican Republic — RNC
# ---------------------------------------------------------------------------

def validate_rnc_do(value: str) -> dict:
    clean = re.sub(r"[.\-\s]", "", value)
    if not re.fullmatch(r"[0-9]{9}", clean):
        return {"valid": False, "reason": "RNC must be 9 digits"}
    if int(clean[:8]) == 0:
        return {"valid": False, "reason": "RNC cannot be zero"}
    weights = (7, 9, 8, 6, 5, 4, 3, 2)
    check = sum(w * int(n) for w, n in zip(weights, clean)) % 11
    expected = str((10 - check) % 9 + 1)
    if clean[8] != expected:
        return {"valid": False,
                "reason": f"check digit mismatch (expected {expected}); note a handful of "
                          "legacy RNCs registered with anomalous check digits exist"}
    return {"valid": True, "formatted": f"{clean[0]}-{clean[1:3]}-{clean[3:8]}-{clean[8]}",
            "type": "registered taxpayer (DGII)"}


# ---------------------------------------------------------------------------
# Panama — RUC (+ two-digit DV check). Algorithm verified against 62 real RUCs
# from the official DGI "Grandes Compradores" list.
# ---------------------------------------------------------------------------

_PA_ARRVAL = {
    '00': '00', '10': '01', '11': '02', '12': '03', '13': '04', '14': '05',
    '15': '06', '16': '07', '17': '08', '18': '09', '19': '01', '20': '02',
    '21': '03', '22': '04', '23': '07', '24': '08', '25': '09', '26': '02',
    '27': '03', '28': '04', '29': '05', '30': '06', '31': '07', '32': '08',
    '33': '09', '34': '01', '35': '02', '36': '03', '37': '04', '38': '05',
    '39': '06', '40': '07', '41': '08', '42': '09', '43': '01', '44': '02',
    '45': '03', '46': '04', '47': '05', '48': '06', '49': '07',
}


def _pa_digit(sw: bool, ructb: str) -> int:
    """One modulo-11 pass with ascending weights from the right."""
    j, total = 2, 0
    for c in reversed(ructb):
        if sw and j == 12:
            sw = False
            j -= 1
        total += j * (ord(c) - ord('0'))
        j += 1
    r = total % 11
    return 11 - r if r > 1 else 0


def _pa_calculate_dv(ruc: str) -> str:
    """Return the 2-char DV for a dashed RUC, or '' if the RUC is malformed."""
    rs = ruc.split('-')
    if (len(rs) == 4 and rs[1] != 'NT') or len(rs) < 3 or len(rs) > 5:
        return ''
    sw = False
    try:
        if ruc[0] == 'E':
            ructb = '0' * (4 - len(rs[1])) + '0000005' + '00' + '50' + '0' * (3 - len(rs[1])) + rs[1] + '0' * (5 - len(rs[2])) + rs[2]
        elif rs[1] == 'NT':
            ructb = '0' * (4 - len(rs[1])) + '0000005' + '00' * (2 - len(rs[0][:-2])) + rs[0][:-2] + '43' + '0' * (3 - len(rs[2])) + rs[2] + '0' * (5 - len(rs[3])) + rs[3]
        elif rs[0][-2:] == 'AV':
            ructb = '0' * (4 - len(rs[1])) + '0000005' + '00' * (2 - len(rs[0][:-2])) + rs[0][:-2] + '15' + '0' * (3 - len(rs[1])) + rs[1] + '0' * (5 - len(rs[2])) + rs[2]
        elif rs[0][-2:] == 'PI':
            ructb = '0' * (4 - len(rs[1])) + '0000005' + '00' * (2 - len(rs[0][:-2])) + rs[0][:-2] + '79' + '0' * (3 - len(rs[1])) + rs[1] + '0' * (5 - len(rs[2])) + rs[2]
        elif rs[0] == 'PE':
            ructb = '0' * (4 - len(rs[1])) + '0000005' + '00' + '75' + '0' * (3 - len(rs[1])) + rs[1] + '0' * (5 - len(rs[2])) + rs[2]
        elif ruc[0] == 'N':
            ructb = '0' * (4 - len(rs[1])) + '0000005' + '00' + '40' + '0' * (3 - len(rs[1])) + rs[1] + '0' * (5 - len(rs[2])) + rs[2]
        elif 0 < len(rs[0]) <= 2:
            ructb = '0' * (4 - len(rs[1])) + '0000005' + '0' * (2 - len(rs[0])) + rs[0] + '00' + '0' * (3 - len(rs[1])) + rs[1] + '0' * (5 - len(rs[2])) + rs[2]
        else:
            ructb = '0' * (10 - len(rs[0])) + rs[0] + '0' * (4 - len(rs[1])) + rs[1] + '0' * (6 - len(rs[2])) + rs[2]
            sw = ructb[3] == '0' and ructb[4] == '0' and ructb[5] < '5'
    except IndexError:
        return ''
    if not re.fullmatch(r"[0-9]+", ructb):
        return ''
    if sw:
        ructb = ructb[:5] + _PA_ARRVAL.get(ructb[5:7], ructb[5:7]) + ructb[7:]
    dv1 = _pa_digit(sw, ructb)
    dv2 = _pa_digit(sw, ructb + chr(48 + dv1))
    return '%d%d' % (dv1, dv2)


def validate_ruc_pa(value: str) -> dict:
    """Panama RUC. Accepts the RUC with its DV separated by whitespace or a
    'DV' label, e.g. '155628291-2-2016 DV 32', '8-174-586 47', or the bare RUC.
    The RUC keeps its internal dashes (they carry structural meaning)."""
    up = value.strip().upper()
    up = re.sub(r"^RUC[:\s]+", "", up)
    dv_given = None
    m = re.search(r"[\s-]*D\.?\s*V\.?\s*[:\-]?\s*([0-9]{1,2})\s*$", up)
    if m:
        dv_given = m.group(1)
        up = up[:m.start()].strip()
    else:
        toks = up.split()
        if len(toks) == 2 and re.fullmatch(r"[0-9]{1,2}", toks[1]):
            dv_given, up = toks[1], toks[0]
    ruc = up.replace(" ", "")
    if not re.fullmatch(r"[0-9A-Z]+(?:-[0-9A-Z]+){2,4}", ruc):
        return {"valid": False,
                "reason": "RUC must be 3-5 dash-separated groups (e.g. 8-174-586 "
                          "for a person or 155628291-2-2016 for a company)"}
    dv = _pa_calculate_dv(ruc)
    if not dv:
        return {"valid": False, "reason": "unrecognized RUC structure"}
    first = ruc.split('-')[0]
    person = first[:1] in "EN" or first == "PE" or re.fullmatch(r"[0-9]{1,2}", first) is not None
    entity = "person (natural)" if person else "company (juridical)"
    formatted = f"{ruc} DV {dv}"
    if dv_given is not None:
        if int(dv_given) != int(dv):
            return {"valid": False, "reason": f"DV check digit mismatch (expected {dv})"}
        return {"valid": True, "formatted": formatted, "type": entity}
    return {"valid": True, "formatted": formatted, "type": entity,
            "dv": dv, "dv_verified": False,
            "note": "no DV supplied to verify; the computed DV is shown in 'dv'"}


# ---------------------------------------------------------------------------
# Costa Rica — cédula (física / jurídica / DIMEX). No check digit; structure only.
# ---------------------------------------------------------------------------

_CR_CLASS3 = ('002', '003', '004', '005', '006', '007', '008', '009', '010',
              '011', '012', '013', '014', '101', '102', '103', '104', '105',
              '106', '107', '108', '109', '110')


def validate_cedula_cr(value: str) -> dict:
    clean = re.sub(r"[.\-\s]", "", value)
    if not re.fullmatch(r"[0-9]+", clean):
        return {"valid": False, "reason": "Costa Rica cédula must contain only digits"}
    n = len(clean)
    if n == 9:
        if clean[0] == "0":
            return {"valid": False, "reason": "9-digit cédula física cannot start with 0"}
        return {"valid": True, "formatted": f"{clean[0]}-{clean[1:5]}-{clean[5:9]}",
                "type": "person (cédula física)", "id_type": "cédula física",
                "check_digit_verified": False,
                "note": "Costa Rica cédula física has no check digit; length and "
                        "structure validated only"}
    if n == 10:
        if clean[0] in "2345":
            if clean[0] == "2" and clean[1:4] not in ("100", "200", "300", "400"):
                return {"valid": False, "reason": "invalid jurídica class-2 subtype"}
            if clean[0] == "3" and clean[1:4] not in _CR_CLASS3:
                return {"valid": False, "reason": "invalid jurídica class-3 subtype"}
            if clean[0] == "4" and clean[1:4] != "000":
                return {"valid": False, "reason": "invalid jurídica class-4 subtype"}
            if clean[0] == "5" and clean[1:4] != "001":
                return {"valid": False, "reason": "invalid jurídica class-5 subtype"}
            return {"valid": True, "formatted": f"{clean[0]}-{clean[1:4]}-{clean[4:]}",
                    "type": "company (cédula jurídica)", "id_type": "cédula jurídica",
                    "check_digit_verified": False,
                    "note": "structure validated per Registro Nacional class rules; "
                            "cédula jurídica has no check digit"}
        if clean[0] == "0":
            return {"valid": True, "formatted": f"{clean[:2]}-{clean[2:6]}-{clean[6:]}",
                    "type": "person (cédula física, 10-digit tax form)",
                    "id_type": "cédula física", "check_digit_verified": False,
                    "note": "10-digit DGT tax representation of a física cédula; no check digit"}
        return {"valid": False,
                "reason": "10-digit id must start with 0 (física tax form) or 2-5 (jurídica)"}
    if n in (11, 12):
        if int(clean) == 0:
            return {"valid": False, "reason": "DIMEX cannot be all zeros"}
        return {"valid": True, "formatted": clean,
                "type": "foreign resident (DIMEX)", "id_type": "DIMEX",
                "check_digit_verified": False,
                "note": "DIMEX (foreigner residency id) is 11-12 digits with no check digit; "
                        "length/format validated only"}
    return {"valid": False,
            "reason": "expected 9 digits (cédula física), 10 (cédula jurídica) "
                      "or 11-12 (DIMEX)"}


# ---------------------------------------------------------------------------
# Bolivia — NIT. No public check-digit algorithm; format/length only.
# ---------------------------------------------------------------------------

def validate_nit_bo(value: str) -> dict:
    clean = re.sub(r"[.\-\s]", "", value)
    if not re.fullmatch(r"[0-9]{7,12}", clean):
        return {"valid": False, "reason": "Bolivia NIT must be 7-12 digits"}
    if int(clean) == 0:
        return {"valid": False, "reason": "NIT cannot be zero"}
    return {"valid": True, "formatted": clean, "type": "registered taxpayer (SIN)",
            "check_digit_verified": False,
            "note": "Bolivia NIT has no public check-digit algorithm (the trailing "
                    "digit is randomly assigned); length/format validated only"}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

VALIDATORS = {
    "CL": ("RUT", validate_rut_cl),
    "AR": ("CUIT/CUIL", validate_cuit_ar),
    "MX": ("RFC", validate_rfc_mx),
    "CO": ("NIT", validate_nit_co),
    "PE": ("RUC", validate_ruc_pe),
    "BR": ("CPF/CNPJ", validate_br),
    "UY": ("RUT", validate_rut_uy),
    "EC": ("Cédula/RUC", validate_ec),
    "PY": ("RUC", validate_ruc_py),
    "VE": ("RIF", validate_rif_ve),
    "GT": ("NIT", validate_nit_gt),
    "DO": ("RNC", validate_rnc_do),
    "PA": ("RUC", validate_ruc_pa),
    "CR": ("Cédula", validate_cedula_cr),
    "BO": ("NIT", validate_nit_bo),
}
