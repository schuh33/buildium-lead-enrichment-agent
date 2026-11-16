#!/usr/bin/env python3
"""L12 - certificate-transparency lookup. Usage: crtsh_lookup.py <slug> [<slug> ...]
For each slug, checks <slug>.<vendor-domain> for the PMS portal domains. A certificate record is a
SUPPORTING signal only: login-link evidence on the company site outranks it, and a record alone never
proves current use. crt.sh is often slow/flaky: one attempt per host, failures are logged as walls."""
import json, sys
from _common import fetch, wall_from, emit

VENDORS = {
    "AppFolio": "appfolio.com", "Buildium": "managebuilding.com", "Yardi/RentCafe": "rentcafe.com",
    "Propertyware": "propertyware.com", "Rent Manager": "rentmanager.com", "Rentvine": "rentvine.com",
}


def main():
    slugs = sys.argv[1:]
    if not slugs:
        sys.exit(__doc__)
    results = []
    for slug in slugs:
        for vendor, dom in VENDORS.items():
            host = f"{slug}.{dom}"
            url = f"https://crt.sh/?q={host}&output=json"
            status, _, body = fetch(url, timeout=30, accept="application/json")
            if status != 200:
                results.append({"host": host, "vendor": vendor, "outcome": f"BLOCKED - {wall_from(status, body)} (fetch + script)"})
                continue
            try:
                rows = json.loads(body) if body.strip() else []
            except json.JSONDecodeError:
                results.append({"host": host, "vendor": vendor, "outcome": "BLOCKED - unparseable response (fetch + script)"})
                continue
            exact = [r for r in rows if host in (r.get("name_value") or "").split("\n")]
            results.append({
                "host": host, "vendor": vendor, "source_url": url, "cert_records": len(exact),
                "first_seen": min((r.get("not_before") for r in exact), default=None),
                "outcome": "HIT (script)" if exact else "NO_DATA (script)",
            })
    emit({"results": results})


if __name__ == "__main__":
    main()
