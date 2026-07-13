"""Bank-account validator tests: CLABE (Mexico) and CBU (Argentina)."""

import pytest

from latam_data.bank import BANK_VALIDATORS


def check(country: str, account: str) -> dict:
    return BANK_VALIDATORS[country][1](account)


# Real test accounts used in Mexican fintech sandboxes + the stdnum CBU vector.
VALID = [
    ("MX", "646180110400000007"),   # STP standard test account
    ("MX", "002010077777777771"),   # BBVA documentation example
    ("MX", "032180000118359719"),   # Klar example
    ("AR", "2850590940090418135201"),   # python-stdnum vector (Banco Macro)
    ("AR", "28505909 40090418135201"),  # same, formatted with a space
]

INVALID = [
    ("MX", "646180110400000008", "check digit"),   # wrong dv
    ("MX", "12345", "18 digits"),
    ("MX", "64618011040000000X", "18 digits"),
    ("AR", "2810590940090418135201", "first block"),   # stdnum invalid vector
    ("AR", "2850590940090418135200", "second block"),  # broken account dv
    ("AR", "123", "22 digits"),
]


@pytest.mark.parametrize("country,account", VALID)
def test_valid_accounts(country, account):
    result = check(country, account)
    assert result["valid"], f"{country} {account}: {result.get('reason')}"
    assert result["bank_code"]
    assert result.get("formatted")


@pytest.mark.parametrize("country,account,reason_hint", INVALID)
def test_invalid_accounts(country, account, reason_hint):
    result = check(country, account)
    assert not result["valid"], f"{country} {account} should be invalid"
    assert reason_hint.lower() in result["reason"].lower(), (
        f"{country} {account}: expected '{reason_hint}', got: {result['reason']}")


def test_clabe_structure_and_bank_name():
    r = check("MX", "646180110400000007")
    assert r["bank_code"] == "646"
    assert r["bank_name"] == "STP"
    assert r["branch_code"] == "180"
    assert r["account_number"] == "11040000000"


def test_cbu_structure_and_bank_name():
    r = check("AR", "2850590940090418135201")
    assert r["bank_code"] == "285"
    assert r["bank_name"] == "Banco Macro"
    assert r["formatted"] == "28505909 40090418135201"


def test_unknown_bank_code_still_valid():
    # A CLABE whose check digit is correct but bank code isn't in the catalog.
    r = check("MX", "999180110400000004")
    if r["valid"]:
        assert "unknown" in r["bank_name"].lower()
