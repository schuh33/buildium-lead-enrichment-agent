# NIGHTLY CONFIG (read at the start of every run)

Values in `<TBD>` are not set yet. Behavior that depends on an optional `<TBD>` value is **disabled** (fail-safe).
The three REQUIRED values must be set: if `QUEUE_LIST` or `SHEET` is `<TBD>` the run stops and posts a Slack alert;
if `SLACK_CHANNEL_ID` is `<TBD>` the run stops without an alert (there is nowhere to post), so set it first.

```
# REQUIRED
QUEUE_LIST        = 31546      # Marketo static list ST31546, "01. Leads to Enrich - Claude Agent" (API list ID is the number)
                               # May hold both new and already-finished leads: the sheet ledger decides what is new (spec Step 1N).
SHEET             = https://docs.google.com/spreadsheets/d/1AU3BapMbdo2b0hlpkVEoGJnzO1Fba2P4GwITMNtow-Q/edit   # rolling sheet "Buildium MQL Contact Repair (Rolling)"
SLACK_CHANNEL_ID  = C0CJBLWSNSY   # #claude-run-log (private channel); run summaries and alerts post here
MARKETO_REST_BASE = https://546-NBY-032.mktorest.com   # Marketo instance (Munchkin 546-NBY-032); all Marketo calls go through
                                                       # the Zapier Marketo tools with full URLs on this base (CLAUDE.md rule 13)

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
# The hard stop is pausing the scheduled task itself in claude.ai.

# INVALID-VALUE FLAGS (spec C16) - confirmed by operator 2026-11-16
INVALID_EMAIL_FIELD    = BVEmailStatus            # Marketo API name; display name "BV Email Status"
INVALID_EMAIL_VALUES   = invalid                  # other statuses (e.g. "risky") are NOT invalid and are never replaced
INVALID_PHONE_FIELDS   = phone                    # the field a phone REPLACE may change (mobilePhone is NOT covered)
INVALID_PHONE_FLAG_FIELD = BVPhoneStatus          # Marketo API name; display name "BV Phone Status" (confirmed by operator)
INVALID_PHONE_VALUES   = invalid
# Both field names verified readable in Marketo on 2026-11-16 (list 31546 returned BVEmailStatus and BVPhoneStatus,
# both through the Marketo MCP and through the Zapier REST path).
# If either BV status can't be read for a lead, no REPLACE of that kind for that lead.

# CLOUD ENVIRONMENT (set in the claude.ai environment dialog, listed here for reference)
# Network access: Custom (+ default list) or Full - decide after the host test. Hosts the scripts need:
#   crt.sh, web.archive.org, archive.org, rdap.verisign.com, rdap.org, data.iana.org, dns.google
# plus any state open-data portals added later. No secrets in environment variables.
# Marketo, Google Sheets, Slack and GitHub calls go through connectors and need no allowlist entries.
```
