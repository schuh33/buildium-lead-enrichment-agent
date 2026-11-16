#!/usr/bin/env python3
"""L11 - Wayback Machine archived team/staff/about/contact pages.
Usage: wayback_cdx.py <domain> [--fetch N]
Lists up to 20 archived pages; --fetch N also returns text of the first N snapshots (truncated).
Old data supports only - it never overrides a current source."""
import re, sys, json, urllib.parse
from _common import fetch, wall_from, emit


def text_of(html):
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", html)).strip()


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    domain = args[0].lower().removeprefix("www.")
    n = int(args[args.index("--fetch") + 1]) if "--fetch" in args else 0
    q = urllib.parse.urlencode({
        "url": f"{domain}/*", "filter": "original:.*(team|staff|about|contact).*",
        "collapse": "urlkey", "limit": "20", "output": "json"})
    url = f"https://web.archive.org/cdx/search/cdx?{q}"
    status, _, body = fetch(url, timeout=30)
    if status != 200:
        emit({"domain": domain, "source_url": url, "outcome": f"BLOCKED - {wall_from(status, body)} (fetch + script)"})
    rows = json.loads(body) if body.strip() else []
    snaps = [{"timestamp": r[1], "original": r[2], "snapshot_url": f"https://web.archive.org/web/{r[1]}/{r[2]}"} for r in rows[1:]]
    for s in snaps[:n]:
        st, _, html = fetch(s["snapshot_url"], timeout=30)
        s["text"] = text_of(html)[:4000] if st == 200 else f"fetch failed: {wall_from(st, html)}"
    emit({"domain": domain, "source_url": url, "snapshots": snaps,
          "outcome": "HIT (script)" if snaps else "NO_DATA (script)"})


if __name__ == "__main__":
    main()
