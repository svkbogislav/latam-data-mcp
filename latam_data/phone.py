"""
latam_phone.py — Verified phone-number validator for 15 Latin American countries.

Part of latam-data-mcp. Pure Python standard library (only `re`). No external
dependencies (no phonenumbers/libphonenumber) so `uvx latam-data-mcp` stays light.

Public API
----------
    validate_phone(country, number) -> dict

Returns a dict with:
    valid      : bool
    reason     : str | None   (why it is invalid; None when valid)
    e164       : str | None   (canonical +CC... form)
    national   : str | None   (human-readable national grouping)
    line_type  : 'mobile' | 'landline' | 'unknown'
    country    : str          (ISO 3166-1 alpha-2, upper-cased)

Design notes on the "notorious" cases:
  * Brazil (BR): 2-digit DDD (area code) + 9-digit mobile subscriber (leading 9,
    the "nono dígito") -> 11-digit NSN; landlines are 10-digit NSN whose
    subscriber starts 2-5. DDD is validated against the official set.
  * Mexico (MX): flat 10-digit NSN since 2019. A legacy leading "1" after the
    country code (+521...) is accepted and stripped; when present it flags the
    number as mobile. Otherwise mobile/landline are indistinguishable -> 'unknown'.
  * Argentina (AR): mobiles carry a leading "9" in international form
    (+54 9 <10-digit geo>). Domestic mobiles use "15" after the area code
    (0 <area> 15 <subscriber>); that form is detected and normalised to the
    international "9" form. Bare 10-digit numbers are treated as landline.
  * Chile (CL): 9-digit NSN; mobiles start with 9, landlines start 2-7.

Input accepted with or without country code, with spaces, dashes, dots,
parentheses, a leading +, and/or a "00" international exit prefix.
"""

import re

# --------------------------------------------------------------------------- #
# Reference data
# --------------------------------------------------------------------------- #

# Official Brazilian DDDs (area codes).
_BR_DDD = {
    11, 12, 13, 14, 15, 16, 17, 18, 19,
    21, 22, 24, 27, 28,
    31, 32, 33, 34, 35, 37, 38,
    41, 42, 43, 44, 45, 46, 47, 48, 49,
    51, 53, 54, 55,
    61, 62, 63, 64, 65, 66, 67, 68, 69,
    71, 73, 74, 75, 77, 79,
    81, 82, 83, 84, 85, 86, 87, 88, 89,
    91, 92, 93, 94, 95, 96, 97, 98, 99,
}

# Venezuelan mobile area codes (all others starting with 2 are landline).
_VE_MOBILE = {"412", "414", "416", "424", "426"}

# Dominican Republic NANP area codes.
_DO_AREA = {"809", "829", "849"}


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #

def _grp(s, sizes):
    """Group a digit string into space-separated chunks of the given sizes;
    any remainder is appended as a final chunk."""
    out, i = [], 0
    for sz in sizes:
        if i >= len(s):
            break
        out.append(s[i:i + sz])
        i += sz
    if i < len(s):
        out.append(s[i:])
    return " ".join(p for p in out if p)


# --------------------------------------------------------------------------- #
# Per-country classifiers.
# Each takes the national significant number (digits only) and returns
#   (line_type, e164_nsn, national_str)  on success, or None on failure.
# e164_nsn is the digit string that follows the country code in E.164 form.
# --------------------------------------------------------------------------- #

def _cl(n):  # Chile +56 — 9-digit NSN
    if len(n) != 9:
        return None
    if n[0] == "9":
        return ("mobile", n, "9 " + n[1:5] + " " + n[5:])
    if n[0] in "234567":
        return ("landline", n, _grp(n, [1, 4, 4]))
    return None


def _ar_geo_ok(geo):
    return len(geo) == 10 and geo[0] in "123456789"


def _ar(n):  # Argentina +54
    # International mobile: leading 9 + 10-digit geographic number.
    if len(n) == 11 and n[0] == "9":
        geo = n[1:]
        if _ar_geo_ok(geo):
            return ("mobile", "9" + geo, "9 " + _grp(geo, [2, 4, 4]))
        return None
    # Domestic mobile with "15" inserted after the area code -> 12 digits.
    if len(n) == 12:
        for split in (2, 3, 4):
            if n[split:split + 2] == "15":
                geo = n[:split] + n[split + 2:]
                if _ar_geo_ok(geo):
                    return ("mobile", "9" + geo, "9 " + _grp(geo, [2, 4, 4]))
    # Bare 10-digit geographic number -> landline (mobiles carry the 9).
    if len(n) == 10 and _ar_geo_ok(n):
        return ("landline", n, _grp(n, [2, 4, 4]))
    return None


def _mx(n):  # Mexico +52 — 10-digit NSN, optional legacy leading 1
    line = "unknown"
    if len(n) == 11 and n[0] == "1":
        n = n[1:]
        line = "mobile"  # legacy +521... marked mobiles
    if len(n) == 10 and n[0] in "23456789":
        return (line, n, _grp(n, [2, 4, 4]))
    return None


def _br(n):  # Brazil +55 — 2-digit DDD + subscriber
    if len(n) not in (10, 11):
        return None
    if int(n[:2]) not in _BR_DDD:
        return None
    ddd, sub = n[:2], n[2:]
    if len(n) == 11:  # mobile: 9-digit subscriber, leading 9
        if sub[0] != "9":
            return None
        return ("mobile", n, "(%s) %s %s-%s" % (ddd, sub[0], sub[1:5], sub[5:]))
    # landline: 8-digit subscriber, leading 2-5
    if sub[0] not in "2345":
        return None
    return ("landline", n, "(%s) %s-%s" % (ddd, sub[:4], sub[4:]))


def _co(n):  # Colombia +57 — 10-digit NSN
    if len(n) != 10:
        return None
    if n[0] == "3":
        return ("mobile", n, _grp(n, [3, 3, 4]))
    if n[:2] == "60":  # 10-digit fixed-line plan (since 2022)
        return ("landline", n, _grp(n, [3, 3, 4]))
    return None


def _pe(n):  # Peru +51
    if len(n) == 9 and n[0] == "9":
        return ("mobile", n, _grp(n, [3, 3, 3]))
    if len(n) == 8 and n[0] in "12345678":
        fmt = _grp(n, [1, 3, 4]) if n[0] == "1" else _grp(n, [2, 3, 3])
        return ("landline", n, fmt)
    return None


def _uy(n):  # Uruguay +598 — 8-digit NSN
    if len(n) != 8:
        return None
    if n[0] == "9":
        return ("mobile", n, _grp(n, [2, 3, 3]))
    if n[0] in "24":
        return ("landline", n, _grp(n, [4, 4]))
    return None


def _ec(n):  # Ecuador +593
    if len(n) == 9 and n[0] == "9":
        return ("mobile", n, _grp(n, [2, 3, 4]))
    if len(n) == 8 and n[0] in "234567":
        return ("landline", n, _grp(n, [1, 3, 4]))
    return None


def _py(n):  # Paraguay +595
    if len(n) == 9 and n[0] == "9":
        return ("mobile", n, _grp(n, [3, 3, 3]))
    if 7 <= len(n) <= 9 and n[0] in "2345678":
        return ("landline", n, _grp(n, [2, 3, 4]))
    return None


def _ve(n):  # Venezuela +58 — 10-digit NSN
    if len(n) != 10:
        return None
    if n[:3] in _VE_MOBILE:
        return ("mobile", n, _grp(n, [3, 3, 4]))
    if n[0] == "2":
        return ("landline", n, _grp(n, [3, 3, 4]))
    return None


def _gt(n):  # Guatemala +502 — 8-digit NSN
    if len(n) != 8:
        return None
    if n[0] in "345":
        return ("mobile", n, _grp(n, [4, 4]))
    if n[0] in "267":
        return ("landline", n, _grp(n, [4, 4]))
    return None


def _do(n):  # Dominican Republic +1 (NANP)
    if len(n) != 10:
        return None
    if n[:3] in _DO_AREA:
        return ("unknown", n, "(%s) %s-%s" % (n[:3], n[3:6], n[6:]))
    return None


def _pa(n):  # Panama +507
    if len(n) == 8 and n[0] == "6":
        return ("mobile", n, _grp(n, [4, 4]))
    if len(n) == 7 and n[0] in "23456789":
        return ("landline", n, _grp(n, [3, 4]))
    return None


def _cr(n):  # Costa Rica +506 — 8-digit NSN
    if len(n) != 8:
        return None
    if n[0] in "678":
        return ("mobile", n, _grp(n, [4, 4]))
    if n[0] in "24":
        return ("landline", n, _grp(n, [4, 4]))
    return None


def _bo(n):  # Bolivia +591 — 8-digit NSN
    if len(n) != 8:
        return None
    if n[0] in "67":
        return ("mobile", n, _grp(n, [4, 4]))
    if n[0] in "234":
        return ("landline", n, _grp(n, [1, 3, 4]))
    return None


# --------------------------------------------------------------------------- #
# Country table:  ISO -> (calling_code, display_name, classifier)
# --------------------------------------------------------------------------- #

COUNTRIES = {
    "CL": ("56", "Chile", _cl),
    "AR": ("54", "Argentina", _ar),
    "MX": ("52", "Mexico", _mx),
    "BR": ("55", "Brazil", _br),
    "CO": ("57", "Colombia", _co),
    "PE": ("51", "Peru", _pe),
    "UY": ("598", "Uruguay", _uy),
    "EC": ("593", "Ecuador", _ec),
    "PY": ("595", "Paraguay", _py),
    "VE": ("58", "Venezuela", _ve),
    "GT": ("502", "Guatemala", _gt),
    "DO": ("1", "Dominican Republic", _do),
    "PA": ("507", "Panama", _pa),
    "CR": ("506", "Costa Rica", _cr),
    "BO": ("591", "Bolivia", _bo),
}

# Accept a few common aliases / names in addition to ISO codes.
_ALIASES = {
    "CHILE": "CL", "ARGENTINA": "AR", "MEXICO": "MX", "MÉXICO": "MX",
    "BRAZIL": "BR", "BRASIL": "BR", "COLOMBIA": "CO", "PERU": "PE",
    "PERÚ": "PE", "URUGUAY": "UY", "ECUADOR": "EC", "PARAGUAY": "PY",
    "VENEZUELA": "VE", "GUATEMALA": "GT", "DOMINICAN REPUBLIC": "DO",
    "PANAMA": "PA", "PANAMÁ": "PA", "COSTA RICA": "CR", "BOLIVIA": "BO",
}


# --------------------------------------------------------------------------- #
# Candidate national-significant-number extraction
# --------------------------------------------------------------------------- #

def _candidates(digits, had_intl, cc, trunk="0"):
    """Return an ordered, de-duplicated list of plausible NSNs to try."""
    ordered = []

    def add(x):
        if x and x not in ordered:
            ordered.append(x)

    d = digits

    if had_intl:
        # Explicit international form: the country code must be present.
        if d.startswith(cc):
            nsn = d[len(cc):]
            add(nsn)
            if trunk and nsn.startswith(trunk):
                add(nsn[len(trunk):])
        else:
            add(d)  # will almost certainly fail -> caller reports mismatch
        return ordered

    # No explicit international marker: try, in priority order, the number as
    # given, then trunk-stripped, then country-code-stripped variants. Trying
    # "as given" first avoids mis-stripping numbers whose area code coincides
    # with the country code (e.g. Peru's Puno area code 51).
    add(d)
    if trunk and d.startswith(trunk):
        add(d[len(trunk):])
    if d.startswith(cc):
        nsn = d[len(cc):]
        add(nsn)
        if trunk and nsn.startswith(trunk):
            add(nsn[len(trunk):])
    return ordered


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def validate_phone(country, number):
    """Validate and normalise a phone `number` for the given `country`.

    `country` is an ISO 3166-1 alpha-2 code (case-insensitive); a few English/
    Spanish country names are also accepted.
    """
    iso = (country or "").strip().upper()
    iso = _ALIASES.get(iso, iso)

    if iso not in COUNTRIES:
        return {
            "valid": False,
            "reason": "unsupported country: %r" % (country,),
            "e164": None,
            "national": None,
            "line_type": "unknown",
            "country": iso,
        }

    cc, name, classify = COUNTRIES[iso]

    raw = "" if number is None else str(number)
    stripped = raw.strip()
    had_intl = stripped.startswith("+")

    digits = re.sub(r"\D", "", stripped)

    # International access prefix ("00" is the ITU exit code used across the
    # region). Note: we deliberately do NOT strip "011" here — for the +1 zone
    # the DR national/trunk prefix is "1" (handled by country-code stripping),
    # and stripping "011" would corrupt Argentina's domestic "011 <area> 15..."
    # mobile form.
    if digits.startswith("00"):
        digits, had_intl = digits[2:], True

    if not digits:
        return {
            "valid": False,
            "reason": "no digits found in input",
            "e164": None,
            "national": None,
            "line_type": "unknown",
            "country": iso,
        }

    if had_intl and not digits.startswith(cc):
        return {
            "valid": False,
            "reason": "number does not match +%s (%s)" % (cc, name),
            "e164": None,
            "national": None,
            "line_type": "unknown",
            "country": iso,
        }

    for nsn in _candidates(digits, had_intl, cc):
        result = classify(nsn)
        if result:
            line_type, e164_nsn, national = result
            return {
                "valid": True,
                "reason": None,
                "e164": "+" + cc + e164_nsn,
                "national": national,
                "line_type": line_type,
                "country": iso,
            }

    return {
        "valid": False,
        "reason": "not a valid %s phone number" % (name,),
        "e164": None,
        "national": None,
        "line_type": "unknown",
        "country": iso,
    }


if __name__ == "__main__":
    import json
    for c, num in [("CL", "+56 9 6123 4567"), ("BR", "+55 11 91234-5678"),
                   ("AR", "011 15-2345-6789"), ("MX", "+52 1 55 1234 5678")]:
        print(c, num, "->", json.dumps(validate_phone(c, num), ensure_ascii=False))
