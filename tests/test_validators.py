"""Check-digit validator tests: real-world IDs, synthetic vectors, and rejections."""

import pytest

from latam_data.validators import VALIDATORS


def check(country: str, tax_id: str) -> dict:
    return VALIDATORS[country][1](tax_id)


# Real IDs of well-known institutions + vectors from python-stdnum docs.
VALID = [
    ("CL", "12.345.678-5"),        # synthetic, verified check digit
    ("CL", "60.910.000-1"),        # Universidad de Chile
    ("CL", "10.000.013-K"),        # K check digit
    ("CL", "10000013k"),           # lowercase, unformatted
    ("AR", "20-12345678-6"),       # synthetic person
    ("AR", "30-50001091-2"),       # Banco de la Nación Argentina
    ("MX", "GODE561231GR8"),       # SAT documentation example (person)
    ("MX", "ABC680524P76"),        # company format
    ("CO", "900373115-3"),
    ("CO", "800.197.268-4"),       # DIAN
    ("PE", "20100047218"),         # Banco de Crédito del Perú
    ("PE", "20131312955"),         # SUNAT
    ("BR", "111.444.777-35"),      # classic CPF vector
    ("BR", "00.000.000/0001-91"),  # Banco do Brasil CNPJ
    ("BR", "12ABC345010A55"),      # alphanumeric CNPJ (2026 format)
    ("UY", "21-100342-001-7"),     # stdnum vector (UTE)
    ("UY", "211406340011"),
    ("EC", "1714307103"),          # cédula
    ("EC", "1792060346001"),       # private company RUC
    ("PY", "80028061-0"),
    ("PY", "2660-3"),
    ("VE", "V-11470283-4"),
    ("GT", "576937-K"),
    ("GT", "7108-0"),
    ("DO", "1-01-85004-3"),
]

INVALID = [
    ("CL", "12.345.678-9", "check digit"),
    ("CL", "123-4", "7-8 digits"),
    ("AR", "20-12345678-7", "check digit"),
    ("AR", "2012345678", "11 digits"),
    ("MX", "GODE561331GR8", "not a real date"),
    ("MX", "G1DE561231GR8", "format"),
    ("CO", "900373115-9", "check digit"),
    ("PE", "20100047219", "check digit"),
    ("PE", "30100047218", "start with"),
    ("BR", "111.444.777-36", "check digits"),
    ("BR", "111.111.111-11", "all digits equal"),
    ("BR", "00.000.000/0000-00", "root cannot be all zeros"),
    ("BR", "123456", "expected a CPF"),
    ("UY", "21-100342-001-8", "check digit"),
    ("UY", "23-100342-001-7", "prefix"),
    ("UY", "21-100342-002-7", "must be '001'"),
    ("EC", "1714307104", "check digit"),
    ("EC", "2592060346001", "province"),
    ("EC", "1792060346000", "suffix"),
    ("PY", "800532492", "check digit"),
    ("PY", "8012345678", "2 to 9 digits"),
    ("VE", "V-11470283-5", "check digit"),
    ("VE", "X-11470283-4", "V/E/J/P/G"),
    ("GT", "8977112-0", "check digit"),
    ("DO", "101850042", "check digit"),
    ("DO", "10185004", "9 digits"),
]


@pytest.mark.parametrize("country,tax_id", VALID)
def test_valid_ids(country, tax_id):
    result = check(country, tax_id)
    assert result["valid"], f"{country} {tax_id}: {result.get('reason')}"
    assert result.get("formatted")


@pytest.mark.parametrize("country,tax_id,reason_hint", INVALID)
def test_invalid_ids(country, tax_id, reason_hint):
    result = check(country, tax_id)
    assert not result["valid"], f"{country} {tax_id} should be invalid"
    assert reason_hint.lower() in result["reason"].lower(), (
        f"{country} {tax_id}: expected reason mentioning '{reason_hint}', got: {result['reason']}")


def test_entity_type_detection():
    assert "company" in check("CL", "60.910.000-1")["type"]
    assert check("AR", "30-50001091-2")["type"] == "company"
    assert check("BR", "111.444.777-35")["type"] == "person"
    assert check("BR", "00.000.000/0001-91")["type"] == "company"
    assert check("EC", "1792060346001")["type"] == "private company"
    assert check("VE", "V-11470283-4")["type"] == "Venezuelan person"
    assert check("PE", "20131312955")["type"] == "company"


def test_alphanumeric_cnpj_flagged():
    result = check("BR", "12ABC345010A55")
    assert result["valid"] and result["alphanumeric_format"] is True
    classic = check("BR", "00.000.000/0001-91")
    assert classic["valid"] and classic["alphanumeric_format"] is False


def test_formatting_is_canonical():
    assert check("CL", "123456785")["formatted"] == "12.345.678-5"
    assert check("BR", "11144477735")["formatted"] == "111.444.777-35"
    assert check("BR", "00000000000191")["formatted"] == "00.000.000/0001-91"
    assert check("UY", "211003420017")["formatted"] == "21-100342-001-7"
    assert check("VE", "V114702834")["formatted"] == "V-11470283-4"
    assert check("DO", "101850043")["formatted"] == "1-01-85004-3"
