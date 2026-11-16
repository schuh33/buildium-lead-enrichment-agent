# OUTPUT CONTRACT — ENRICHMENT REVIEW GOOGLE SHEET (v1.4)

*v1.3: no approval step; `Field_Changes.approve` replaced by optional `hold` (`Y` = do not write; blank = write); `SKIPPED_HOLD`; `Final_Contacts` drops rows with `hold = Y`; software fields are write targets.*
*v1.4 (2026-11-16): **rolling sheet for NIGHTLY mode** (one standing sheet, ledger-driven, created once from this template — the nightly run never creates sheets or tabs); new action `REPLACE`; new tab `Run_Log`; `run_id` columns; `run_lock` and `kill_switch` keys; outcome enums use `(script)` instead of `(browser)`.*

**Sheet modes**
- **Interactive (ENRICH):** one sheet per Marketo list run. Name: `Buildium Lead Enrichment — <list name> — <YYYY-MM-DD>`.
- **NIGHTLY:** one **rolling** sheet named `Buildium MQL Contact Repair — Rolling`, URL in `config/nightly_config.md`. Create it **once**, interactively, with every tab below, headers verbatim, and the `Final_Contacts` formulas set up to cover appended rows (ARRAYFORMULA/QUERY-style so new rows flow through). When `Lead_Summary` passes ~5,000 rows, start a new rolling sheet (quarterly is typical) and update the config.

Location: `DRIVE_FOLDER_ID` if set in Project Instructions, else My Drive root. Headers in row 1 **verbatim** (snake_case), header row frozen, filter on, a `Y` dropdown on `Field_Changes.hold`. Append rows after every lead (C12) — never rewrite whole tabs mid-run. Use whichever Sheets write path the session proves at precheck (the google-workspace skill where available; otherwise the connector's Sheets actions); if none works, STOP.

---

## Tab 1 — `Run_Summary` (key | value)

`Title` · `run_id` (latest) · `mode_history` · `marketo_list` (name + ID) · `spec_version` (Enrichment Runtime Spec v1.4) · `leads_in_list` · `complete` · `complete_no_new_data` · `unresolved` · `in_progress` · `pending` · `fill_rows_proposed` · `replace_rows_proposed` · `note_only_rows` · `flags` (counts: buildium_portal / ownership_change / icp_mismatch / out_of_business / no_longer_at_company) · `most_missed_fields` · `dropped_intake_fields` · `stop_reason` · `resume_command` · `writeback_status` (NOT STARTED / PARTIAL / COMPLETE + date) · `writeback_validated_spec` (spec version for which the automatic one-lead pilot last passed) · `run_lock` (`<RUN_ID> <ISO timestamp>`, blank when no run is active) · `kill_switch` (any non-blank value = no Marketo writes; staging continues) · `rules` (No system writes except per C6; empty fields only — existing values are never overwritten, findings go to Notes — except values Marketo flagged invalid, which may be replaced (C16); V1/V2 only; no aggregator values; no fabrication)

## Tab 2 — `Lead_Summary` (the ledger; one row per Marketo lead)

```
marketo_lead_id | email | first_name | last_name | company | state | sfdc_type | sfdc_id | company_key |
email_invalid | phone_invalid | identity_status | identity_evidence | enrichment_status | fill_count | replace_count | conflict_count |
buildium_portal_detected | ownership_change_flag | icp_mismatch | possible_out_of_business | no_longer_at_company |
current_pms | rungs_logged | notes_target_field | run_id | last_verified | reviewer_notes
```

`conflict_count` = number of `NOTE_ONLY` discrepancies. `run_id` = the run that last touched the lead. NIGHTLY skips leads whose `enrichment_status` is COMPLETE, COMPLETE_NO_NEW_DATA or UNRESOLVED.

Enums: `identity_status` ∈ {CONFIRMED, PROBABLE, UNRESOLVED} · `enrichment_status` ∈ {PENDING, IN_PROGRESS, COMPLETE, COMPLETE_NO_NEW_DATA, UNRESOLVED} · flags and `email_invalid` / `phone_invalid` ∈ {yes, no} · `rungs_logged` like `15/15 + S1,S5` · `notes_target_field` ∈ {Notes__c, Marketing_Notes__c, Notes__c (unsynced), REVIEW_TARGET} · `sfdc_id` = sfdcLeadId or sfdcContactId.

## Tab 3 — `Field_Changes` (the write-back tab; one row per staged action)

```
change_id | run_id | marketo_lead_id | email | company | field_api | field_label | current_value | proposed_value |
action | tier | role_based | source_url | evidence | rung | hold | reviewer | writeback_status |
writeback_timestamp | writeback_message
```

- `change_id` = `<marketo_lead_id>-<field_api>` (unique; a later run's row for the same lead+field replaces a still-unwritten earlier row).
- `action` ∈
  - `FILL` — field is **empty**, V1/V2 value found → written by WRITEBACK unless `hold = Y`.
  - `REPLACE` — field is **flagged invalid in Marketo** and a qualifying replacement exists (C16). `current_value` = the invalid value, `proposed_value` = the replacement. Written unless `hold = Y`. Only fields `email` and the configured phone field(s) may carry `REPLACE`.
  - `NOTE_ONLY` — field already has a value that differs (or a multi-select has values and more were found; or a C16 condition failed) → **never written**; carried in the Notes block.
  - `FLAG` — checkbox set to true when not already true → written unless `hold = Y`.
  - `APPEND_NOTE` — the Notes block (`proposed_value` = full block text) → prepended to the notes field unless `hold = Y`.
  - `CONFIRMED` — found value equals current value → informational, never written.
  - (Retired in v1.2: `CONFLICT`, `ADD_VALUES`; WRITEBACK treats them as `NOTE_ONLY`.)
- `tier` ∈ {V1, V2}. `role_based` ∈ {Y, N}. `hold` ∈ {Y, blank} — a person sets `Y` to pull one row out of write-back. `reviewer` = optional free text, never read by the agent.
- `writeback_status` ∈ {blank, WRITTEN, SKIPPED_CHANGED_SINCE_REVIEW, SKIPPED_HOLD, SKIPPED_CAP, SKIPPED_KILL_SWITCH, ERROR}. Filled only by WRITEBACK / the NIGHTLY write step.
- Software fields: one row per lead per field built from `Tech_Stack` (doc 03 §3c); `tier` = weakest tier among combined platforms.
- Email `REPLACE` rows put the `mx_check` result in `evidence` and the duplicate-check result (`no other lead holds this address`) alongside it.
- Sort: by `marketo_lead_id`, then FILL, REPLACE, FLAG, APPEND_NOTE, NOTE_ONLY, CONFIRMED.

## Tab 4 — `Current_Values` (snapshot at intake; one row per lead)

`marketo_lead_id` followed by one column per intake field from doc 03 §2, using the Marketo API name as the header. Written once when the lead is first added; never edited. WRITEBACK compares against live Marketo values, not this tab.

## Tab 5 — `Additional_Contacts` (other decision-makers found; staged only, never written to Marketo)

```
marketo_lead_id | company | full_name | title | role_category | business_email | email_tier |
business_phone | phone_tier | profile_url | source_url | decision_maker_fit | in_marketo | notes
```

Enums: `role_category` ∈ {owner, broker, principal, GM, ops_lead, other} · tiers ∈ {V1, V2, V3} (V3 only for L16 inferred emails, labeled) · `decision_maker_fit` ∈ {high, med, low} · `in_marketo` ∈ {yes, no, not_checked}.

## Tab 6 — `Tech_Stack`

```
company_key | company | detected_platform | signal_type | evidence | source_url | rung
```

`signal_type` ∈ {Buildium portal (possible customer), Competitor PMS (switcher), Other tool}. Source for the `current_software` and `Technologies__c` rows.

## Tab 7 — `Source_Ladder_Log` (proof that every rung ran for every lead)

```
run_id | marketo_lead_id | company_key | rung | source | query_or_url | outcome | fields_fed | cached_from
```

- `rung` ∈ {L1 … L16, S1 … S5}. Every lead has L1–L15 rows plus a row for each triggered conditional rung.
- `outcome` ∈ {HIT, HIT (script), HIT (browser), NO_DATA, NO_DATA (script), NO_DATA (browser), BLOCKED – <wall> (fetch + script), BLOCKED – <wall> (fetch + browser), N/A – <reason>}. (`(browser)` appears only in interactive runs.)
- `cached_from` = marketo_lead_id whose company pass was reused (blank if run fresh).

## Tab 8 — `Company_Cache` (reuse across leads, sessions and nights)

```
company_key | canonical_company | domain | identity_status | company_rungs_complete | findings_json | last_verified
```

`findings_json` = compact JSON of company-level findings with tiers + source URLs. NIGHTLY and RESUME read this before re-researching a company; findings older than 180 days are re-verified.

## Tab 9 — `Final_Contacts` (the projected final list; placed second in the workbook)

One row per lead, **all and only the Marketo/SFDC fields** from the intake set in doc 03 §2 (same columns as `Current_Values`, with `marketo_lead_id` shown as `id`). No status, hold or helper columns. Every cell is a live formula: the lead's current value, except that (a) an **empty** field takes the staged `FILL` / `FLAG` value (including `current_software` and `Technologies__c`), (b) a field **flagged invalid** takes the staged `REPLACE` value, and (c) the notes field (`Marketing_Notes__c` for Contacts, `Notes__c` for Leads) is the staged `APPEND_NOTE` block followed by a blank line and the existing notes. Rows with `hold = Y` drop out; rows already `WRITTEN` show the written value. Existing non-flagged values are never replaced (C7). Cells that differ from `Current_Values` are highlighted green. This tab is the list that WRITEBACK produces once the staged rows are written.

## Tab 10 — `Run_Log` (NIGHTLY; one row per run)

```
run_id | started_utc | finished_utc | mode | leads_processed | complete | complete_no_new_data | unresolved | in_progress |
fill_rows | replace_rows | note_only_rows | writes_written | writes_skipped | writes_error | auto_writeback | kill_switch_seen | stop_reason | slack_posted
```

`Run_Summary` also carries a `retired_actions` row on sheets converted from v1.1 (CONFLICT / ADD_VALUES → NOTE_ONLY).
