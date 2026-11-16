#!/usr/bin/env python3
"""L10 - domain registration data via RDAP. Usage: rdap_lookup.py <domain>
.com/.net -> Verisign RDAP directly; other TLDs -> IANA bootstrap, then the registry's RDAP server.
Domain age goes to Notes only (never as founded year). Privacy-masked registrant = NO_DATA for that part."""
import json, sys
from _common import fetch, wall_from, emit

VERISIGN = {"com": "https://rdap.verisign.com/com/v1/", "net": "https://rdap.verisign.com/net/v1/"}


def base_for(tld):
    if tld in VERISIGN:
        return VERISIGN[tld], None
    status, _, body = fetch("https://data.iana.org/rdap/dns.json", accept="application/json")
    if status != 200:
        return None, wall_from(status, body)
    for svc in json.loads(body).get("services", []):
        if tld in svc[0]:
            return svc[1][0], None
    return None, "no RDAP service for TLD"


def vcard(entity, key):
    for item in (entity.get("vcardArray") or [None, []])[1]:
        if item[0] == key:
            return item[3]
    return None


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    domain = sys.argv[1].lower().strip().removeprefix("www.")
    tld = domain.rsplit(".", 1)[-1]
    base, err = base_for(tld)
    if not base:
        emit({"domain": domain, "outcome": f"BLOCKED - {err} (fetch + script)"})
    url = base.rstrip("/") + "/domain/" + domain
    status, _, body = fetch(url, accept="application/rdap+json")
    if status != 200:
        out = "NO_DATA (script)" if status == 404 else f"BLOCKED - {wall_from(status, body)} (fetch + script)"
        emit({"domain": domain, "source_url": url, "outcome": out})
    d = json.loads(body)
    events = {e.get("eventAction"): e.get("eventDate") for e in d.get("events", [])}
    registrant = next((e for e in d.get("entities", []) if "registrant" in e.get("roles", [])), {})
    registrar = next((e for e in d.get("entities", []) if "registrar" in e.get("roles", [])), {})
    org, email = vcard(registrant, "org") or vcard(registrant, "fn"), vcard(registrant, "email")
    masked = (not org and not email) or any("redact" in str(x).lower() or "privacy" in str(x).lower() for x in (org, email))
    emit({
        "domain": domain, "source_url": url,
        "registration_date": events.get("registration"), "last_changed": events.get("last changed"),
        "registrar": vcard(registrar, "fn"),
        "registrant_org": None if masked else org, "registrant_email": None if masked else email,
        "privacy_masked": masked,
        "outcome": "HIT (script)" if events.get("registration") else "NO_DATA (script)",
    })


if __name__ == "__main__":
    main()
