"""Phone-number validator tests (verified vectors across the 15 countries)."""

import pytest

from latam_data.phone import COUNTRIES, validate_phone

VALID = [
    ("CL", "+56 9 6123 4567", "mobile"),
    ("CL", "9 8765 4321", "mobile"),
    ("CL", "+56 2 2123 4567", "landline"),
    ("AR", "+54 9 11 2345 6789", "mobile"),
    ("AR", "011 15-2345-6789", "mobile"),
    ("AR", "+54 11 4321 1234", "landline"),
    ("MX", "+52 1 55 1234 5678", "mobile"),
    ("MX", "+52 55 1234 5678", "unknown"),
    ("BR", "+55 11 91234-5678", "mobile"),
    ("CO", "+57 301 234 5678", "mobile"),
]

INVALID = [
    ("CL", "+56 9 123"),      # too short
    ("CL", "+54 9 11 2345 6789"),  # wrong country code for CL
    ("AR", "12345"),
    ("MX", "+52 55 1234"),
    ("BR", "+55 11 8123 4567"),    # mobile without leading 9
    ("BR", "+55 10 91234 5678"),   # invalid DDD
    ("ZZ", "12345678"),            # unsupported country
]


@pytest.mark.parametrize("country,number,line_type", VALID)
def test_valid_phones(country, number, line_type):
    r = validate_phone(country, number)
    assert r["valid"], f"{country} {number}: {r.get('reason')}"
    assert r["e164"].startswith("+")
    assert r["line_type"] == line_type


@pytest.mark.parametrize("country,number", INVALID)
def test_invalid_phones(country, number):
    assert not validate_phone(country, number)["valid"]


def test_fifteen_countries_supported():
    assert len(COUNTRIES) == 15


def test_e164_normalization():
    r = validate_phone("BR", "11 91234-5678")  # no country code
    assert r["valid"] and r["e164"] == "+5511912345678"
