"""
Manual utility: checks a set of source config YAML files for
duplicate indicator_code values within their column_mapping. Real
risk source: truncated codes (e.g. long ONS column names cut to 60
characters) can silently collide, causing two genuinely different
indicators to overwrite each other's data under one key.

Usage:
    python -m framework.tests.manual_check_duplicate_indicator_codes ons_m2 ons_m3 ons_m4 ons_m5 ons_m6 ons_m7
"""

import sys
import yaml


def check(config_names: list[str]):
    for name in config_names:
        path = f"framework/config/sources/{name}.yaml"
        with open(path) as f:
            config = yaml.safe_load(f)

        codes = [entry["indicator_code"] for entry in config["column_mapping"]]
        duplicates = set(c for c in codes if codes.count(c) > 1)

        status = "DUPLICATES FOUND" if duplicates else "OK"
        print(f"{name}: {len(codes)} codes, {len(set(codes))} unique -- {status}")
        if duplicates:
            print(f"   {duplicates}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m framework.tests.manual_check_duplicate_indicator_codes <config1> [config2] ...")
        sys.exit(1)

    check(sys.argv[1:])