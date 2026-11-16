#!/usr/bin/env python3
"""L12 - probe vendor portal hostnames directly. Usage: portal_probe.py <slug> [<slug> ...]
Reports DNS/HTTP status, final URL and page <title> for <slug>.<vendor-domain>. The agent decides what
it means: a live portal whose title/branding names THIS company is V2 evidence of use; a generic
vendor page, a redirect to the vendor's marketing site, or wildcard DNS proves nothing."""
import re, sys, socket
from _common import fetch, wall_from, emit
from crtsh_lookup import VENDORS


def main():
    slugs = sys.argv[1:]
    if not slugs:
        sys.exit(__doc__)
    try:  # control lookup: distinguishes "no such host" from "DNS unavailable in this environment"
        socket.gethostbyname("appfolio.com")
    except OSError:
        emit({"results": [], "outcome": "BLOCKED - DNS unavailable (fetch + script)"})
    results = []
    for slug in slugs:
        for vendor, dom in VENDORS.items():
            host = f"{slug}.{dom}"
            try:
                socket.gethostbyname(host)
            except OSError:
                results.append({"host": host, "vendor": vendor, "dns": "no resolve", "outcome": "NO_DATA (script)"})
                continue
            status, final, body = fetch(f"https://{host}/", timeout=12)
            title = re.search(r"<title[^>]*>(.*?)</title>", body or "", re.I | re.S)
            results.append({
                "host": host, "vendor": vendor, "dns": "resolves", "http_status": status, "final_url": final,
                "title": title.group(1).strip()[:160] if title else None,
                "outcome": "HIT (script)" if status == 200 else f"BLOCKED - {wall_from(status, body)} (fetch + script)",
            })
    emit({"results": results})


if __name__ == "__main__":
    main()
