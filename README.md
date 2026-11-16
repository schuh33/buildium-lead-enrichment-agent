# Buildium Lead Enrichment Agent

Enriches existing Buildium MQL records that have an invalid phone or email, using public web sources, and
stages every finding in a Google Sheet. Runs unattended every night as a Claude Code cloud scheduled task.

**Spec version: v1.4** (2026-11-16)

## How a night works

1. A Marketo smart campaign adds each MQL with an invalid phone/email to the static list **Enrichment Queue**.
2. The scheduled task (hourly, overnight window) starts a cloud session that clones this repo, reads `CLAUDE.md`,
   `config/nightly_config.md` and `spec/`, then runs `MODE = NIGHTLY`.
3. It takes the next batch of queued leads not yet in the sheet ledger, runs the Enrichment Ladder, and appends
   rows to the rolling Google Sheet.
4. If `AUTO_WRITEBACK = true` it writes the staged rows to Marketo (empty-only, plus replacement of values
   Marketo has flagged invalid); otherwise rows wait for a typed `WRITEBACK` command.
5. It posts a summary (or an alert on any stop) to Slack.

## Layout

| Path | Purpose |
|---|---|
| `CLAUDE.md` | Rules every cloud session follows |
| `config/nightly_config.md` | Queue list, sheet, Slack channel, batch size, write caps, invalid-value flags |
| `spec/01_Enrichment_Runtime_Spec.md` | Constraints, procedure, ladder, self-check |
| `spec/02_Output_Contract_Google_Sheet.md` | Exact sheet tabs and columns |
| `spec/03_Marketo_Field_Map_and_WriteBack.md` | Writable fields, Notes format, write-back procedure |
| `scripts/` | Headless lookups that replace the browser rungs (RDAP, crt.sh, portal probe, Wayback, MX check) |
| `prompts/nightly_task_prompt.md` | Text pasted into the scheduled task; keep it short, the spec lives here |

## Setup checklist

- [ ] Admin: cloud sessions and scheduled tasks enabled; GitHub connection covers this repo
- [ ] Cloud environment created (see `config/nightly_config.md` for the allowlist) and attached to the task
- [ ] Rolling Google Sheet created once from the template in spec doc 02 (the nightly run never creates tabs)
- [ ] Marketo: `Enrichment Queue` static list + smart campaign
- [ ] Fill every `<TBD>` in `config/nightly_config.md`
- [ ] Test: manual session in the environment (host reachability), then "Run now" on 3–5 seeded leads
- [ ] First week or two: `AUTO_WRITEBACK = false`, review the sheet, type `WRITEBACK` each morning

## Open items (not yet proven)

- Phone-invalid indicator field/values in Marketo (phone replacement stays off until set)
- Confirm `BVEmailStatus` value(s) that mean invalid
- Sheets write path from a cloud session (Zapier Google Sheets actions vs. skill) must be proven in the first test
- Whether web search/fetch from a cloud session works under a Custom allowlist, or needs Full
- Scripts in `scripts/` compile and fail safely offline but have **not** been run against live hosts
- Auto-mode classifier must allow the Zapier Marketo write calls without a prompt

The agent never commits to this repo.
