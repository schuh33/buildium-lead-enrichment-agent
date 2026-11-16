#!/usr/bin/env python3
"""Email replacement gate (spec C16) - syntax + MX check via DNS-over-HTTPS (dns.google).
Usage: mx_check.py <email>
outcome: PASS (syntax ok and domain has MX or A record) | FAIL (bad syntax or domain cannot receive mail)
| UNAVAILABLE (DNS check could not run -> the email is NOT staged; finding goes to Notes).
This proves the domain can receive mail, not that the mailbox exists."""
import re, sys, json
from _common import fetch, wall_from, emit

SYNTAX = re.compile(r"^[A-Za-z0-9._%+'-]{1,64}@([A-Za-z0-9-]+\.)+[A-Za-z]{2,}$")


def doh(name, rtype):
    status, _, body = fetch(f"https://dns.google/resolve?name={name}&type={rtype}", timeout=15, accept="application/dns-json")
    if status != 200:
        return None, wall_from(status, body)
    return json.loads(body), None


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    email = sys.argv[1].strip()
    if not SYNTAX.match(email) or ".." in email:
        emit({"email": email, "syntax_ok": False, "outcome": "FAIL"})
    domain = email.rsplit("@", 1)[1].lower()
    mx, err = doh(domain, "MX")
    if mx is None:
        emit({"email": email, "domain": domain, "syntax_ok": True, "outcome": "UNAVAILABLE", "reason": err})
    if mx.get("Status") == 0 and mx.get("Answer"):
        emit({"email": email, "domain": domain, "syntax_ok": True, "mx": [a.get("data") for a in mx["Answer"]], "outcome": "PASS"})
    a, err = doh(domain, "A")
    if a is None:
        emit({"email": email, "domain": domain, "syntax_ok": True, "outcome": "UNAVAILABLE", "reason": err})
    ok = a.get("Status") == 0 and bool(a.get("Answer"))
    emit({"email": email, "domain": domain, "syntax_ok": True, "mx": [], "a_record_fallback": ok, "outcome": "PASS" if ok else "FAIL"})


if __name__ == "__main__":
    main()
