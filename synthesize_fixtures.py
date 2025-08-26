#!/usr/bin/env python3
"""Synthesize realistic Postal/Dealer fixtures without touching the app.

Generates two CSVs under fixtures/ with anonymized, realistic patterns:
- postal_synth.csv (varied header synonyms, noise)
- dealer_synth.csv (canonical headers, includes Opens)

Run:
  ./venv/bin/python3 synthesize_fixtures.py
"""

from __future__ import annotations

import csv
import os
import random
from typing import List, Tuple

random.seed(42)

STREETS = [
    ("MAIN", ["MAIN"], ["ST", "STREET"]),
    ("OAK", ["OAK"], ["RD", "ROAD"]),
    ("MAPLE", ["MAPLE"], ["AVE", "AVENUE"]),
    ("ELM", ["ELM"], ["ST", "STREET"]),
    ("PINE", ["PINE"], ["ST", "STREET"]),
    ("RIO", ["RIO", "RÍO"], ["AVE", "AVENUE"]),
]

DESIGNATORS = [
    ("APT", ["APT", "APARTMENT", "#"]),
    ("UNIT", ["UNIT"]),
    ("STE", ["STE", "SUITE"]),
    ("BLDG", ["BLDG", "BUILDING"]),
    ("RM", ["RM", "ROOM"]),
]

FIRST_NAMES = [
    "JOHN",
    "JANE",
    "BOB",
    "JIM",
    "ANN",
    "JOSE",  # non-ASCII counterpart will be added in postal
    "PATRICK",
    "MARY",
    "ALAN",
    "Z",
    "Q",
    "A",
]

LAST_NAMES = [
    "DOE",
    "DOE JR",
    "SMITH",
    "BEAM",
    "LEE",
    "ALVAREZ",  # will appear as ÁLVAREZ in postal
    "ONEIL",     # O'NEIL in postal
    "SMITH JOHNSON",  # hyphen in postal
    "TURING",
    "Y",
    "R",
    "B",
    "T",
]

CITIES = [
    ("CITY", ["CITY", "City", "Ciudad"]),
    ("TOWN", ["TOWN", "Town"]),
    ("HAMLET", ["HAMLET", "Hamlet"]),
    ("BURG", ["BURG", "Burg"]),
]

def pick_street() -> Tuple[str, str, str]:
    base, alts, suffixes = random.choice(STREETS)
    street_name = random.choice(alts)
    suffix = random.choice(suffixes)
    return base, street_name, suffix

def synth_row(index: int, vary_designator: bool = False) -> Tuple[dict, dict]:
    # Names
    fn = FIRST_NAMES[index % len(FIRST_NAMES)]
    ln = LAST_NAMES[index % len(LAST_NAMES)]

    # Non-ASCII and punctuation for postal variants
    postal_fn = fn
    postal_ln = ln
    if ln == "ALVAREZ":
        postal_ln = "ÁLVAREZ"
    if ln == "ONEIL":
        postal_ln = "O'NEIL"
    if ln == "SMITH JOHNSON":
        postal_ln = "SMITH-JOHNSON"

    # Address
    base, street_alt, suffix = pick_street()
    num = random.randint(1, 999)
    # Dealer canonical
    dealer_addr1 = f"{num} {base} {suffix}"
    dealer_addr2 = ""
    postal_addr1 = f"{num} {street_alt} {suffix if random.random()<0.6 else suffix.replace('ROAD','RD').replace('AVENUE','AVE').replace('STREET','ST')}".strip()
    postal_addr2 = ""

    # Optionally attach a unit designator
    if random.random() < 0.4:
        des_key, variants = random.choice(DESIGNATORS)
        unit_val = str(random.randint(1, 120))
        dealer_addr2 = f"{variants[0]} {unit_val}"
        # vary synonym between postal and dealer
        if vary_designator and len(variants) > 1:
            postal_addr2 = f"{variants[1]} {unit_val}"
        else:
            postal_addr2 = dealer_addr2

    # City/State/Zip
    city_key, city_variants = random.choice(CITIES)
    dealer_city = city_key
    postal_city = random.choice(city_variants)
    dealer_state = "CT"
    postal_state = "CONNECTICUT" if random.random() < 0.15 else dealer_state
    zip5 = f"{random.randint(6001, 6999):05d}"
    dealer_zip = zip5
    postal_zip = zip5 if random.random() < 0.8 else f"{zip5}-{random.randint(1000,9999)}"

    # Dealer canonical row
    dealer = {
        "First_Name": fn,
        "Last_Name": ln,
        "Address1": dealer_addr1,
        "Address2": dealer_addr2,
        "City": dealer_city,
        "State": dealer_state,
        "Zip": dealer_zip,
        "Opens": "x" if random.random() < 0.3 else "",
    }

    # Postal row with noisy headers and variants
    postal = {
        "First Name": postal_fn if random.random()<0.7 else "",
        "Last Name": postal_ln if random.random()<0.7 else "",
        "FullName": f"{postal_fn.title()} {postal_ln.title()}" if random.random()<0.3 else "",
        "Address Line 1": postal_addr1,
        "Address Line 2": postal_addr2,
        "City": postal_city,
        "St": postal_state,
        "ZipCode": postal_zip,
    }

    return postal, dealer


def write_csv(path: str, rows: List[dict], headers: List[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main() -> None:
    postal_rows: List[dict] = []
    dealer_rows: List[dict] = []

    # Generate 40 paired rows with a mix of designator synonym differences
    for i in range(40):
        vary = (i % 5 == 0)  # every 5th row uses synonym difference for designator
        p, d = synth_row(i, vary_designator=vary)
        postal_rows.append(p)
        dealer_rows.append(d)

    # Write files
    postal_headers = [
        "First Name",
        "Last Name",
        "Address Line 1",
        "Address Line 2",
        "City",
        "St",
        "ZipCode",
        "FullName",
    ]
    dealer_headers = [
        "First_Name",
        "Last_Name",
        "Address1",
        "Address2",
        "City",
        "State",
        "Zip",
        "Opens",
    ]
    write_csv("fixtures/postal_synth.csv", postal_rows, postal_headers)
    write_csv("fixtures/dealer_synth.csv", dealer_rows, dealer_headers)
    print("Wrote fixtures: fixtures/postal_synth.csv, fixtures/dealer_synth.csv")


if __name__ == "__main__":
    main()


