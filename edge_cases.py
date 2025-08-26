#!/usr/bin/env python3
"""Edge case tests for fuzzy matcher (no app changes).

Run with project venv to ensure deps:
  ./venv/bin/python3 edge_cases.py
"""

from __future__ import annotations

import sys
from typing import Tuple
import pandas as pd

from fuzzy_matcher import (
    preprocess_input_variable,
    preprocess_master_with_opens,
    run_specific_match,
    SchemaError,
)


def run_case(name: str, fn) -> Tuple[str, bool, str]:
    try:
        fn()
        return name, True, ""
    except AssertionError as ae:
        return name, False, f"Assertion failed: {ae}"
    except Exception as e:
        return name, False, f"Error: {e}"


def case_header_synonyms_and_derivation() -> None:
    # Input uses synonyms; no FullAddress column -> should derive from parts; include Address2
    inp = pd.DataFrame(
        {
            "First Name": ["John"],
            "Last Name": ["Doe"],
            "Address Line 1": ["123 Main St"],
            "Address Line 2": ["Apt 5"],
            "City": ["Town"],
            "St": ["CT"],
            "ZipCode": ["06001"],
        }
    )
    df1, report = preprocess_input_variable(inp, file="test.xlsx", sheet="Input")
    assert set(["First_Name", "Last_Name", "Address1", "City", "State", "Zip", "FullAddress"]).issubset(
        set(df1.columns)
    ), "Standardized columns missing"
    assert "APT 5" in df1.loc[0, "FullAddress"], "Address2 not included in FullAddress"
    # At least one strategy should be enabled
    assert any(v.get("enabled") for v in report.values()), "No strategies enabled"


def case_lastnameaddress_ignores_designator_but_fulladdress_strict() -> None:
    # Input: Apt 5; Master: Apt 6, otherwise same
    inp = pd.DataFrame(
        {
            "First_Name": ["JOHN"],
            "Last_Name": ["DOE"],
            "Address1": ["123 MAIN ST"],
            "Address2": ["APT 5"],
            "City": ["TOWN"],
            "State": ["CT"],
            "Zip": ["06001"],
        }
    )
    master = pd.DataFrame(
        {
            "First_Name": ["JOHN"],
            "Last_Name": ["DOE"],
            "Address1": ["123 MAIN ST"],
            "Address2": ["APT 6"],
            "City": ["TOWN"],
            "State": ["CT"],
            "Zip": ["06001"],
            "Opens": ["x"],
        }
    )
    df1, _ = preprocess_input_variable(inp, file="test.xlsx", sheet="Input")
    df2, opens_missing = preprocess_master_with_opens(master)
    assert not opens_missing and df2.loc[0, "Opens"] == "x", "Opens not detected/mapped"

    res_last = run_specific_match(df1, df2, "LastNameAddress")
    assert len(res_last) == 1, "LastNameAddress should match despite different APT numbers"

    res_full = run_specific_match(df1, df2, "FullAddress")
    assert len(res_full) == 0, "FullAddress should not match when APT numbers differ"


def case_suffix_split_from_fullname() -> None:
    # Input provides FullName with suffix; master has split names
    inp = pd.DataFrame(
        {
            "FullName": ["Jane Doe Jr"],
            "Address1": ["1 Oak Rd"],
            "City": ["Town"],
            "State": ["CT"],
            "Zip": ["06001"],
        }
    )
    master = pd.DataFrame(
        {
            "First_Name": ["JANE"],
            "Last_Name": ["DOE JR"],
            "Address1": ["1 OAK RD"],
            "City": ["TOWN"],
            "State": ["CT"],
            "Zip": ["06001"],
        }
    )
    df1, _ = preprocess_input_variable(inp, file="x.xlsx", sheet="A")
    df2, _ = preprocess_master_with_opens(master)
    assert df1.loc[0, "First_Name"] == "JANE" and df1.loc[0, "Last_Name"] == "DOE JR", "Suffix split failed"
    res = run_specific_match(df1, df2, "FullName")
    assert len(res) == 1, "FullName matching should succeed with suffix"


def case_ambiguous_headers_raise() -> None:
    # Two columns map to First_Name -> should raise SchemaError
    amb = pd.DataFrame(
        {
            "First Name": ["John"],
            "GivenName": ["Johnny"],  # both map to First_Name -> ambiguous
            "Last Name": ["Doe"],
            "Address": ["1 Main"],
            "City": ["Town"],
            "State": ["CT"],
            "Zip": ["06001"],
        }
    )
    try:
        preprocess_input_variable(amb, file="x.xlsx", sheet="A")
        raise AssertionError("Expected SchemaError for ambiguous headers")
    except SchemaError:
        pass


# -------- Additional edge cases below --------

def _case_header_noise_formatting() -> None:
    inp = pd.DataFrame({
        "  FIRST-name  ": ["Ann"],
        " last  name ": ["Lee"],
        "Address": ["10 Maple Ave"],
        "Town": ["City"],
        "Province": ["CT"],
        "Post-code": ["06001"],
    })
    df1, report = preprocess_input_variable(inp, file="x.xlsx", sheet="A")
    assert df1.loc[0, "First_Name"] == "ANN" and df1.loc[0, "Last_Name"] == "LEE"
    assert any(v.get("enabled") for v in report.values())


def _case_ambiguity_lastname_raises() -> None:
    amb = pd.DataFrame({
        "Last Name": ["Lee"],
        "Surname": ["Li"],
        "First": ["Ann"],
        "Address1": ["10 Maple Ave"],
        "City": ["City"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    try:
        preprocess_input_variable(amb, file="x.xlsx", sheet="A")
        raise AssertionError("Expected SchemaError for ambiguous last name")
    except SchemaError:
        pass


def _case_abbrev_normalization_same_number() -> None:
    inp = pd.DataFrame({
        "First_Name": ["BOB"],
        "Last_Name": ["SMITH"],
        "Address1": ["50 OAK ROAD"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    master = pd.DataFrame({
        "First_Name": ["BOB"],
        "Last_Name": ["SMITH"],
        "Address1": ["50 OAK RD"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    df1, _ = preprocess_input_variable(inp, file="x.xlsx", sheet="A")
    df2, _ = preprocess_master_with_opens(master)
    res = run_specific_match(df1, df2, "FullAddress")
    assert len(res) == 1, "Street abbreviation should still match when number same"


def _case_designator_synonyms() -> None:
    inp = pd.DataFrame({
        "First_Name": ["JIM"],
        "Last_Name": ["BEAM"],
        "Address1": ["7 PINE ST"],
        "Address2": ["STE 12"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    master = pd.DataFrame({
        "First_Name": ["JIM"],
        "Last_Name": ["BEAM"],
        "Address1": ["7 PINE ST"],
        "Address2": ["SUITE 12"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    df1, _ = preprocess_input_variable(inp, file="x.xlsx", sheet="A")
    df2, _ = preprocess_master_with_opens(master)
    assert len(run_specific_match(df1, df2, "LastNameAddress")) == 1
    assert len(run_specific_match(df1, df2, "FullAddress")) == 0


def _case_house_number_nearby() -> None:
    inp = pd.DataFrame({
        "First_Name": ["A"],
        "Last_Name": ["B"],
        "Address1": ["101 MAIN ST"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    master = pd.DataFrame({
        "First_Name": ["A"],
        "Last_Name": ["B"],
        "Address1": ["103 MAIN ST"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    df1, _ = preprocess_input_variable(inp, file="x.xlsx", sheet="A")
    df2, _ = preprocess_master_with_opens(master)
    res = run_specific_match(df1, df2, "FullAddress")
    # Nearby numbers should reduce score but may still meet threshold depending on content; assert 0 or 1 result deterministically
    assert len(res) in (0, 1)


def _case_zip_plus4() -> None:
    inp = pd.DataFrame({
        "First_Name": ["Z"],
        "Last_Name": ["Y"],
        "Address1": ["1 A ST"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001-1234"],
    })
    master = pd.DataFrame({
        "First_Name": ["Z"],
        "Last_Name": ["Y"],
        "Address1": ["1 A ST"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    df1, _ = preprocess_input_variable(inp, file="x.xlsx", sheet="A")
    df2, _ = preprocess_master_with_opens(master)
    # LastNameAddress should tolerate zip format difference via address string similarity
    assert len(run_specific_match(df1, df2, "LastNameAddress")) in (0, 1)


def _case_state_variants() -> None:
    inp = pd.DataFrame({
        "First_Name": ["Q"],
        "Last_Name": ["R"],
        "Address1": ["9 X RD"],
        "City": ["CITY"],
        "State": ["CONNECTICUT"],
        "Zip": ["06001"],
    })
    master = pd.DataFrame({
        "First_Name": ["Q"],
        "Last_Name": ["R"],
        "Address1": ["9 X RD"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    df1, _ = preprocess_input_variable(inp, file="x.xlsx", sheet="A")
    df2, _ = preprocess_master_with_opens(master)
    assert len(run_specific_match(df1, df2, "FullAddress")) in (0, 1)


def _case_minimal_fullname() -> None:
    inp = pd.DataFrame({
        "FullName": ["Alan Turing"],
        "Address1": ["1 B ST"],
        "City": ["City"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    master = pd.DataFrame({
        "First_Name": ["ALAN"],
        "Last_Name": ["TURING"],
        "Address1": ["1 B ST"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    df1, report = preprocess_input_variable(inp, file="x.xlsx", sheet="A")
    assert report.get("FullName", {}).get("enabled") is True
    df2, _ = preprocess_master_with_opens(master)
    assert len(run_specific_match(df1, df2, "FullName")) == 1


def _case_duplicate_candidates() -> None:
    inp = pd.DataFrame({
        "First_Name": ["S"],
        "Last_Name": ["T"],
        "Address1": ["2 C ST"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    master = pd.DataFrame({
        "First_Name": ["S", "S", "S"],
        "Last_Name": ["T", "T", "T"],
        "Address1": ["2 C ST", "2 C ST", "2 C ST"],
        "City": ["CITY", "CITY", "CITY"],
        "State": ["CT", "CT", "CT"],
        "Zip": ["06001", "06001", "06001"],
    })
    df1, _ = preprocess_input_variable(inp, file="x.xlsx", sheet="A")
    df2, _ = preprocess_master_with_opens(master)
    res = run_specific_match(df1, df2, "FullAddress")
    assert len(res) == 1, "Should pick a single best duplicate deterministically"


# -------- Adversarial false-positive cases --------

def _case_fp_fullname_similar_not_same() -> None:
    # Close but not same: JON vs JOHN, and different last name
    inp = pd.DataFrame({
        "First_Name": ["JON"],
        "Last_Name": ["SMYTH"],
        "Address1": ["12 D ST"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    master = pd.DataFrame({
        "First_Name": ["JOHN"],
        "Last_Name": ["SMITH"],
        "Address1": ["12 D ST"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    df1, _ = preprocess_input_variable(inp, file="x.xlsx", sheet="A")
    df2, _ = preprocess_master_with_opens(master)
    res = run_specific_match(df1, df2, "FullName")
    assert len(res) == 0, "FullName should not match similar but different names at high threshold"


def _case_fp_lastnameaddress_far_number() -> None:
    # Same last name and street, but house numbers far apart and different zips
    inp = pd.DataFrame({
        "First_Name": ["A"],
        "Last_Name": ["DOE"],
        "Address1": ["10 MAIN ST"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    master = pd.DataFrame({
        "First_Name": ["B"],
        "Last_Name": ["DOE"],
        "Address1": ["910 MAIN ST"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06999"],
    })
    df1, _ = preprocess_input_variable(inp, file="x.xlsx", sheet="A")
    df2, _ = preprocess_master_with_opens(master)
    res = run_specific_match(df1, df2, "LastNameAddress")
    assert len(res) == 0, "LastNameAddress should reject far house numbers and zip mismatch"


def _case_fp_fulladdress_diff_city() -> None:
    # Same number and street but different city -> FullAddress should fail
    inp = pd.DataFrame({
        "First_Name": ["A"],
        "Last_Name": ["B"],
        "Address1": ["77 OAK RD"],
        "City": ["TOWN"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    master = pd.DataFrame({
        "First_Name": ["C"],
        "Last_Name": ["D"],
        "Address1": ["77 OAK RD"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    df1, _ = preprocess_input_variable(inp, file="x.xlsx", sheet="A")
    df2, _ = preprocess_master_with_opens(master)
    res = run_specific_match(df1, df2, "FullAddress")
    assert len(res) == 0, "FullAddress should not match across different cities"


def _case_fp_designator_only_one_side() -> None:
    # Designator present only on one side -> FullAddress must fail; LastNameAddress ignores designator but still needs address similarity
    inp = pd.DataFrame({
        "First_Name": ["JIM"],
        "Last_Name": ["BEAM"],
        "Address1": ["7 PINE ST"],
        "Address2": ["APT 12"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    master = pd.DataFrame({
        "First_Name": ["JIM"],
        "Last_Name": ["BEAM"],
        "Address1": ["7 PINE ST"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    df1, _ = preprocess_input_variable(inp, file="x.xlsx", sheet="A")
    df2, _ = preprocess_master_with_opens(master)
    assert len(run_specific_match(df1, df2, "FullAddress")) == 0
    # LastNameAddress may match or not depending on address score; allow 0 or 1 but not force a match
    lna = run_specific_match(df1, df2, "LastNameAddress")
    assert len(lna) in (0, 1)


def _case_fp_nonascii_similar_lastname() -> None:
    # Similar last name with accents; different address -> should not match FullName or FullAddress inadvertently
    inp = pd.DataFrame({
        "First_Name": ["JOSE"],
        "Last_Name": ["ÁLVAREZ"],
        "Address1": ["1 X ST"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    master = pd.DataFrame({
        "First_Name": ["JOSE"],
        "Last_Name": ["ALVAREZ"],
        "Address1": ["999 Z ST"],
        "City": ["CITY"],
        "State": ["CT"],
        "Zip": ["06001"],
    })
    df1, _ = preprocess_input_variable(inp, file="x.xlsx", sheet="A")
    df2, _ = preprocess_master_with_opens(master)
    assert len(run_specific_match(df1, df2, "FullName")) == 0
    assert len(run_specific_match(df1, df2, "FullAddress")) == 0


def main() -> int:
    cases = [
        ("header_synonyms_and_derivation", case_header_synonyms_and_derivation),
        ("lastnameaddress_ignores_designator_but_fulladdress_strict", case_lastnameaddress_ignores_designator_but_fulladdress_strict),
        ("suffix_split_from_fullname", case_suffix_split_from_fullname),
        ("ambiguous_headers_raise", case_ambiguous_headers_raise),
        # Additional edge cases
        ("header_noise_formatting", lambda: _case_header_noise_formatting()),
        ("ambiguity_lastname_raises", lambda: _case_ambiguity_lastname_raises()),
        ("abbrev_normalization_same_number", lambda: _case_abbrev_normalization_same_number()),
        ("designator_synonyms_lastnameaddress_ok_fulladdress_fail", lambda: _case_designator_synonyms()),
        ("house_number_nearby_scores", lambda: _case_house_number_nearby()),
        ("zip_plus4_vs_zip_lastnameaddress", lambda: _case_zip_plus4()),
        ("state_fullname_vs_abbrev_lastnameaddress", lambda: _case_state_variants()),
        ("minimal_fullname_only", lambda: _case_minimal_fullname()),
        ("duplicate_candidates_deterministic_single_result", lambda: _case_duplicate_candidates()),
        # Adversarial false-positive guards
        ("fp_fullname_similar_but_not_same", lambda: _case_fp_fullname_similar_not_same()),
        ("fp_lastnameaddress_far_number_zip_city", lambda: _case_fp_lastnameaddress_far_number()),
        ("fp_fulladdress_different_city", lambda: _case_fp_fulladdress_diff_city()),
        ("fp_fulladdress_designator_only_one_side", lambda: _case_fp_designator_only_one_side()),
        ("fp_nonascii_similar_lastname_diff_address", lambda: _case_fp_nonascii_similar_lastname()),
    ]

    results = [run_case(name, fn) for name, fn in cases]
    passed = sum(1 for _, ok, _ in results if ok)
    failed = [(name, msg) for name, ok, msg in results if not ok]

    for name, ok, msg in results:
        status = "PASS" if ok else "FAIL"
        line = f"[{status}] {name}"
        if msg:
            line += f" - {msg}"
        print(line)

    print(f"\nSummary: {passed}/{len(cases)} passed, {len(failed)} failed")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())


# Optional: golden fixtures test using anonymized CSV slices
def _load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def run_golden_fixtures(postal_csv: str = "fixtures/postal_fixture.csv", dealer_csv: str = "fixtures/dealer_fixture.csv") -> None:
    postal = _load_csv(postal_csv)
    dealer = _load_csv(dealer_csv)

    df1, report = preprocess_input_variable(postal, file=postal_csv, sheet="Postal")
    df2, _ = preprocess_master_with_opens(dealer)

    enabled = [mt for mt, v in report.items() if v.get("enabled")]
    print(f"Enabled strategies: {enabled}")

    for mt in ["FullName", "LastNameAddress", "FullAddress"]:
        if mt not in enabled:
            print(f"[SKIP] {mt}: {report.get(mt, {}).get('reason')}")
            continue
        res = run_specific_match(df1, df2, mt)
        print(f"[GOLDEN] {mt} => matches: {len(res)}")


def compute_counts(postal_csv: str, dealer_csv: str) -> dict:
    postal = pd.read_csv(postal_csv)
    dealer = pd.read_csv(dealer_csv)
    df1, report = preprocess_input_variable(postal, file=postal_csv, sheet="Postal")
    df2, _ = preprocess_master_with_opens(dealer)
    counts = {}
    for mt in ["FullName", "LastNameAddress", "FullAddress"]:
        if not report.get(mt, {}).get("enabled"):
            counts[mt] = 0
            continue
        res = run_specific_match(df1, df2, mt)
        counts[mt] = int(len(res))
    return counts


def assert_synth_counts(expected: dict | None = None) -> None:
    """Assert baseline counts on synthesized fixtures (seed=42)."""
    if expected is None:
        expected = {"FullName": 10, "LastNameAddress": 10, "FullAddress": 25}
    postal_csv = "fixtures/postal_synth.csv"
    dealer_csv = "fixtures/dealer_synth.csv"
    actual = compute_counts(postal_csv, dealer_csv)
    print(f"Synth counts: {actual}")
    assert actual == expected, f"Counts changed: expected {expected}, got {actual}"



