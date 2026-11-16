"""Shared helpers for the headless lookup scripts (stdlib only)."""
import json, sys, urllib.request, urllib.error, socket

UA = "Mozilla/5.0 (compatible; BuildiumEnrichment/1.4)"


def fetch(url, timeout=20, accept="*/*", method="GET"):
    """Return (status, final_url, body_text). status=None on network failure."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(2_000_000).decode("utf-8", "replace") if method != "HEAD" else ""
            return r.status, r.geturl(), body
    except urllib.error.HTTPError as e:
        wall = e.headers.get("x-deny-reason") if e.headers else None
        return e.code, url, f"__HTTP_ERROR__ {wall or ''}".strip()
    except (urllib.error.URLError, socket.timeout, TimeoutError, OSError) as e:
        return None, url, f"__NETWORK_ERROR__ {e}"


def wall_from(status, body):
    """Classify a failed fetch into a named wall for Source_Ladder_Log."""
    if status is None:
        return "network/timeout"
    if status == 403 and "host_not_allowed" in (body or ""):
        return "host not on environment allowlist"
    if status in (401, 403):
        return f"{status} blocked"
    if status == 429:
        return "rate limit"
    if status >= 500:
        return f"{status} server error"
    return f"http {status}"


def emit(obj):
    print(json.dumps(obj, indent=2, default=str))
    sys.exit(0)
