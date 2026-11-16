# MARKETO FIELD MAP, NOTES FORMAT & WRITE-BACK PROCEDURE (v1.4)

*v1.3: NO APPROVAL STEP — `WRITEBACK sheet=<url>` writes every staged `FILL`, `FLAG`, `APPEND_NOTE` row not on `hold`; `current_software` and `Technologies__c` became empty-only write targets (free text, not picklists — `current_software` string 255, `Technologies__c` textarea 5,000, per Marketo field metadata 2026-10-09).*
*v1.4 (2026-11-16): **NIGHTLY auto write-back** with safeguards (§6); **`REPLACE`** action for fields Marketo has flagged invalid — including `email` (C16) — with duplicate-email and MX checks; Notes lines `Previous <field> (flagged invalid)`; invalid-value flags are config-driven.*

Field names below were checked against the live Marketo lead schema and the Buildium Salesforce org on 2026-10-01. If a field write errors, stop and report it — never substitute a "similar" field.

## 1. Notes fields (verified)

| SFDC record type (`sfdcType`) | Marketo API name | SFDC field | SFDC label | Type / limit |
|---|---|---|---|---|
| Lead | `Notes__c` (the "Notes (L)" field) | Lead.`Notes__c` | Marketing Notes | Long Text Area, 32,000 chars |
| Contact | `Marketing_Notes__c` | Contact.`Marketing_Notes__c` | Marketing Notes | Long Text Area, 32,768 chars |
| blank / not synced | `Notes__c` + flag `unsynced` in Lead_Summary | — | — | — |
| anything else (e.g., person account) | none — `notes_target_field = REVIEW_TARGET`; stage the block with `field_api = REVIEW_TARGET`; never written | — | — | — |

Routing keys read at intake: `sfdcType`, `sfdcLeadId`, `sfdcContactId`.

## 2. Intake field set (pass as `fields` to `get_list_members`)

```
id,email,firstName,lastName,title,company,phone,mobilePhone,mainPhone,website,address,city,state,postalCode,country,
sfdcType,sfdcLeadId,sfdcContactId,leadStatus,Role__c,Property_Types_Managed__c,Professional_Membership__c,
Number_of_Units__c,Units_under_management__c,unitRange,numberOfEmployees,Notes__c,Marketing_Notes__c,
linkedInProfileURL,current_software,Technologies__c,No_Longer_at_Company__c,No_Longer_in_Business__c,
Current_Buildium_Customer__c,buildiumManagedDomain,BVEmailStatus,DBA__c,Legal_Entity_Name__c,zqu__County__c
```

Plus any field named in `INVALID_PHONE_FIELDS` / `INVALID_PHONE_CRITERIA` in `config/nightly_config.md`. If Marketo rejects a field, drop it, retry, and list it in `Run_Summary.dropped_intake_fields`. Read-only context fields (`Units_under_management__c`, `unitRange`, `BVEmailStatus`, `Current_Buildium_Customer__c`, `buildiumManagedDomain`, `DBA__c`, `Legal_Entity_Name__c`, `zqu__County__c`) are never written by this agent.

## 3. Write-target fields (the ONLY fields that may appear in `Field_Changes`)

**Empty-only rule (v1.2).** Every row is written only when the field is **empty** — action `FILL`. If it already has a value, nothing is written: the finding goes into the Notes block and a `NOTE_ONLY` row is logged. **Exception (v1.4, C16):** `email` and the configured phone field(s) may be `REPLACE`d when Marketo has flagged the current value invalid. Other write actions: `FLAG` (checkbox to true when not already true) and `APPEND_NOTE`.

| Marketo API | Label | What qualifies (V1/V2 only) | Allowed actions |
|---|---|---|---|
| `email` | Email Address | **Only** when flagged invalid (`INVALID_EMAIL_FIELD` ∈ `INVALID_EMAIL_VALUES`): the lead's own **V1 person-specific** address, identity CONFIRMED, `mx_check` PASS, no other Marketo lead holds it (C16). Never filled/changed otherwise; role aliases go to Notes | REPLACE |
| `title` | Job Title | Lead's current title **at the record's company** (C13) | FILL |
| `phone` | Phone Number | Lead's direct business phone; if none, company main line (`role_based = Y`) | FILL; REPLACE only if flagged invalid per config |
| `mainPhone` | Main Phone | Company main line | FILL |
| `mobilePhone` | Mobile Phone | Only a cell the lead publishes as a business contact (C1) | FILL; REPLACE only if flagged invalid per config |
| `company` | Company Name | Blank → FILL. Any existing value, including junk → Notes only | FILL |
| `website` | Website | Canonical company domain (https://…) | FILL |
| `address`, `city`, `state`, `postalCode` | Address block | Office/HQ address from one source. Fill a blank field only when every populated field in the block agrees; otherwise Notes | FILL |
| `country` | Country | `United States` only when blank and a US address is proposed | FILL |
| `Role__c` | Role (picklist) | Mapped from a verified title at the record's company (§3a) | FILL |
| `Property_Types_Managed__c` | Property Types Managed (multi-select) | Values in §3b only. Written only when empty | FILL (only when empty) |
| `Professional_Membership__c` | Professional Membership (multi-select) | `NARPM`, `IREM`, `CAI`, `NAA` only; directory = V1, logo on company site = V2. Written only when empty | FILL (only when empty) |
| `Number_of_Units__c` | Number of Units (number) | A **published** number: "450 doors" → `450`. Ranges/"300+" and listing-count estimates → Notes only | FILL |
| `current_software` | Current Software (text, 255) | **Every** V1/V2-detected property-management tool per §3c. Plain vendor names, comma-separated | FILL |
| `Technologies__c` | Technologies (long text, 5,000) | Every V1/V2-detected tool (superset of `current_software`), PM software first | FILL |
| `No_Longer_at_Company__c` | No Longer at Company (checkbox) | `true` only with V1 evidence | FLAG |
| `No_Longer_in_Business__c` | No Longer in Business (checkbox) | `true` only if SOS status dissolved/inactive AND site is dead or shows a closure notice | FLAG |
| `Notes__c` / `Marketing_Notes__c` | Notes | Notes block (§5) | APPEND_NOTE |

**Never write:** `firstName`, `lastName`, lead status/score/source fields, owner fields, any read-only context field from §2, and `email` outside a C16 `REPLACE`. LinkedIn URL, legal entity/DBA, license #, county, founded year, ownership, employee count, extra contacts, estimates → **Notes only**.

### 3a. `Role__c` mapping (allowed values, verified)
| Title contains | Value |
|---|---|
| Owner, Broker, Principal, President, CEO, Founder, Managing Member, Partner | `Broker/Owner` |
| Property Manager, Portfolio Manager, Community Manager, Association Manager, Director of Property Management | `Property Manager` |
| Leasing | `Leasing` |
| Maintenance, Facilities | `Maintenance` |
| Bookkeeper, Accountant, Controller, Accounting | `Bookkeeper/Accountant` |
| Office Manager, Operations Manager, Administrator, COO | `Business/Office Manager` |
| Consultant | `Consultant` |
| Individual self-managing owner of rentals (no PM company) | `Landlord` |
| HOA board member/officer | `HOA Board Member` |
| Verified title fits none of the above | `Other` |

### 3b. `Property_Types_Managed__c` allowed values (verified)
`Single Family` · `Multi Family` · `Association` · `Commercial` · `Affordable Housing` · `Student Housing` · `Vacation/Short Term` · `Mobile Homes` · `Storage`
Written as one semicolon-separated string: `Single Family;Multi Family`. A found type not in this list goes to Notes.

### 3c. `current_software` and `Technologies__c` — value rules

- **No picklist.** Use the vendor's plain product name with consistent spelling: `AppFolio`, `Rentec Direct`, `Rentvine`, `RentRedi`, `Hemlane`, `DoorLoop`, `Yardi`, `Propertyware`, `Rent Manager`, `Datex`, `CaliberWeb`, `Track Hospitality Software`, etc. One name per product — no URLs, evidence text or "(probable)" qualifiers. Separator `, `. Same vendor never twice.
- **`current_software`** = every detected tool that is property-management software: a property/PM system of any kind (HOA, vacation-rental and commercial platforms included) or any of its modules; tenant/owner/resident portal platforms; leasing, rental-application, screening or lease-document tools; rental-listing or MLS/search-portal tools and investor/owner reporting portals; property accounting software (when listed as its bookkeeping tool); property inspection or building-access technology. **Not** in `current_software` (→ `Technologies__c` only): payroll/HR, chat/collaboration, design, email-marketing, payment processors, recruiting portals, website builders/hosts, forms, loan-servicing or student/school portals, social/listing profiles for sales.
- **The two fields must agree.** Every PM tool in `Technologies__c` also appears in `current_software`.
- **`Technologies__c`** = `current_software` items first, then other V1/V2 tools in `Tech_Stack` order.
- **Exclude from both:** registrar/DNS-only entries, offline sites, "none found", anything not a named product. Vendor partner-network listings, job-post mentions, archived-page-only evidence, and CRM notes are **not** evidence of use → Notes only.
- **Identity.** Stage only for leads whose identity is CONFIRMED or PROBABLE, using `Company_Cache` / `Tech_Stack`. A platform seen at one office of a multi-office brokerage, where the lead's office is not established → Notes only.
- **Empty-only, per field.** Judged independently. Populated → Notes (`NOTE_ONLY`).
- **Staging.** One `FILL` row per lead per field; `tier` = weakest tier combined; `source_url`, `evidence`, `rung` list every contributing source.

## 4. Discrepancy rules
- Compare after normalizing (phones to digits, URLs to root domain, case/whitespace, address abbreviations). Equal → `CONFIRMED`.
- Field empty → `FILL`. Field flagged invalid and C16 satisfied → `REPLACE`. Field has a value that differs (not flagged, or C16 not satisfied) → **do not change it**; `NOTE_ONLY` and the finding goes in Notes (`Differs from record: …`).
- Two V1/V2 sources disagree → stage a value (into an empty or flagged-invalid field) only if one is clearly more authoritative AND current; otherwise list both in Notes and stage nothing.
- Otherwise the agent never overwrites. Changing an unflagged existing value is a manual decision in Marketo/SFDC.

## 5. Notes block format

For sales reps: plain text, short lines, newest block on top, ≤2,000 characters. Every V1/V2 finding goes in. No V3, no X values, no consumer data. **No bracketed tags** — tiers and source URLs live only in the sheet. Estimates and company claims are labeled in plain words.

```
--- Claude Lead Enrichment | <YYYY-MM-DD> ---
Identity: CONFIRMED (email domain matches website; same city)
Company: <canonical name> (legal: <entity>, active in <state> since <year>) | <domain> | <main phone>
Office: <street, city, state zip> (<county> County)
Lead: <name>, <title> - still listed on team page as of <YYYY-MM-DD>; RE license <#> active
Also: <title> at <other company>
Other decision-makers: <name>, <title>, <email>
Portfolio: company says <N> doors (<year>); types: SFR, small MF; HOA: no; ~<N> active listings (estimate)
Software: <platform> (<plain evidence>) -> switcher target | Buildium portal: none found
Memberships: NARPM
Ownership: no change found | acquired by <X> in <YYYY>
Replaced: email <new> found on company team page (not deliverability-tested)
Previous email (flagged invalid): <old email>
Previous phone (flagged invalid): <old phone>
Not replaced: possible email <addr> from <source> - held back (<reason: mx check failed | address already on lead <id> | role alias | not person-specific>)
Differs from record: phone on record <x>, website lists <y>; title on record <x>, LinkedIn shows <y>
Not found: <fields>
Sources: <url1>; <url2>; <url3>
```
UNRESOLVED leads get a 2–3 line block: identity unresolved, what was searched, no data proposed.

## 6. WRITEBACK procedure

**Triggers.** (a) Interactive: the operator types `WRITEBACK sheet=<url>` — typing it is the go-ahead; no approval column, no confirmation prompt. (b) NIGHTLY: the end of a run, only when config `AUTO_WRITEBACK = true`. Nothing else starts a write.

1. **Select rows.** Rows with blank `writeback_status`, `hold` not `Y`, action `FILL`, `REPLACE`, `FLAG` or `APPEND_NOTE`. Ignore `CONFIRMED`, `NOTE_ONLY` and legacy `CONFLICT` / `ADD_VALUES`. `hold = Y` → `SKIPPED_HOLD`. NIGHTLY: only rows whose `run_id` is the current run (earlier unwritten rows are written only by an interactive WRITEBACK).
2. **NIGHTLY gates (check in order; any failure = no writes, staging stays, Slack says why):**
   - `AUTO_WRITEBACK = true`.
   - `Run_Summary.kill_switch` blank (else rows → `SKIPPED_KILL_SWITCH`). Re-read it before every batch of writes.
   - **Write cap:** at most `WRITE_CAP_PER_RUN` rows; the rest → `SKIPPED_CAP` (picked up by a later run only if re-staged; report the count).
   - **Error halt:** stop writing after `ERROR_HALT` ERROR rows in the run, or when errors exceed 20% of attempted writes.
3. **Announce, don't ask.** Interactive: one line in chat naming leads, rows by action and fields touched, then continue. NIGHTLY: the same line goes to Slack. Never wait for a reply.
4. **Automatic pilot** (first write-back ever, or `Run_Summary.writeback_validated_spec` ≠ current spec version): run steps 5–7 on **one** lead first and re-read it from Marketo. If every written field matches, set `writeback_validated_spec` and continue. If any field is missing, different, or errored → **stop** and report (Slack in NIGHTLY); write nothing further. No human confirmation is requested when the pilot passes.
5. **Re-read live values** per lead (`get_leads_by_filter`, filterType `id`, same fields):
   - FILL → live value no longer empty → `SKIPPED_CHANGED_SINCE_REVIEW`.
   - **REPLACE → live value must still equal `current_value` AND the invalid flag must still be true; otherwise `SKIPPED_CHANGED_SINCE_REVIEW`. For `email`, re-run the duplicate check (`get_leads_by_filter`, filterType `email`, the new address): if any other lead holds it → `SKIPPED_CHANGED_SINCE_REVIEW` with the lead ID in `writeback_message`.**
   - FLAG → live checkbox already true → `SKIPPED_CHANGED_SINCE_REVIEW`.
   - APPEND_NOTE → new value = `<block>` + blank line + `<live existing notes>` (existing text preserved verbatim). If over the field limit (§1), do not truncate existing notes → `ERROR – notes overflow`.
6. **Write** via `zapier.marketo_make_api_mutating_request`: `POST` to `/rest/v1/leads.json`, body `{"action":"updateOnly","lookupField":"id","input":[{"id":<marketo_lead_id>,"<field_api>":"<value>",…}]}` — ≤100 leads per call, only staged fields. If the relative URL is rejected, discover the accepted form with `zapier.marketo_make_api_get_request` (`GET /rest/v1/leads.json?filterType=id&filterValues=<id>`) and reuse it. Read each record's `status`/`reasons`. Write an `email` `REPLACE` in its own request so a rejection cannot block the lead's other fields.
7. **Verify:** re-read written fields; set `writeback_status = WRITTEN` + `writeback_timestamp` (ISO 8601) or `ERROR` + `writeback_message`.
8. **Report:** update `Run_Summary.writeback_status`; interactive: tell the operator written / skipped / error counts with reasons; NIGHTLY: Slack summary and `Run_Log`. Note that smart campaigns triggered by *Data Value Changes* on email, title, Role, phone, Number of Units, Current Software, Technologies or Notes will fire for written leads, that SFDC sync follows email changes, and that a replaced email's validity status is stale until Marketo re-verifies it.

**Fallback** if the API path fails: build a CSV (header = Marketo API names, `id` first, staged values only, notes already merged) and tell the operator exactly which file to import with "update existing". Never in NIGHTLY — NIGHTLY just stops and alerts.
