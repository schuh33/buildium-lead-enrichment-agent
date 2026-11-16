# NIGHTLY CONFIG (read at the start of every run)

Values in `<TBD>` are not set yet. Behavior that depends on an optional `<TBD>` value is **disabled** (fail-safe).
The three REQUIRED values must be set: if `QUEUE_LIST` or `SHEET` is `<TBD>` the run stops and posts a Slack alert;
if `SLACK_CHANNEL_ID` is `<TBD>` the run stops without an alert (there is nowhere to post), so set it first.

```
# REQUIRED
QUEUE_LIST        = <TBD>      # Marketo static list name or ID, e.g. "Enrichment Queue"
SHEET             = <TBD>      # URL of the rolling Google Sheet (created once from the doc 02 template)
SLACK_CHANNEL_ID  = <TBD>      # channel (or your user ID for a DM) for run summaries and alerts

# RUN SIZE
BATCH_SIZE        = 25         # leads per session
MAX_RUNS_PER_NIGHT = 5         # informational; the task schedule controls this (hourly, ~1am-5am Mountain)
LOCK_STALE_HOURS  = 3          # a run lock older than this is considered dead and may be taken over

# WRITE-BACK SAFETY
AUTO_WRITEBACK    = false      # false = stage only (a person types WRITEBACK). Flip to true only after the first
                               # week or two of reviewed runs.
WRITE_CAP_PER_RUN = 100        # max Field_Changes rows written in one run
ERROR_HALT        = 3          # stop writing after this many ERROR rows in one run (or >20% of attempted)
# Kill switch: Run_Summary key `kill_switch` in the sheet. Any non-blank value = no writes this run (staging continues).

# INVALID-VALUE FLAGS (spec C16)
INVALID_EMAIL_FIELD  = BVEmailStatus
INVALID_EMAIL_VALUES = invalid           # confirm against live data before enabling AUTO_WRITEBACK
INVALID_PHONE_FIELDS = <TBD>             # which Marketo phone field(s) the invalid flag applies to
INVALID_PHONE_CRITERIA = <TBD>           # how Marketo marks a phone invalid (field + values)

# CLOUD ENVIRONMENT (set in the claude.ai environment dialog, listed here for reference)
# Network access: Custom (+ default list) or Full - decide after the host test. Hosts the scripts need:
#   crt.sh, web.archive.org, archive.org, rdap.verisign.com, rdap.org, data.iana.org, dns.google
# plus any state open-data portals added later. No secrets in environment variables.
```
