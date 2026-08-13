# Captain Compliance - Consent Cutover container

A single Google Tag Manager container-import file that is the **clean cutover** recipe
for Captain Compliance customers. It replaces a pile of site-specific banner-loader tags
with **one** tag that loads the Captain Compliance banner and drives Google Consent Mode v2,
while preserving the canonical superset of `Captain*` gating variables that downstream
tags read.

## Files

| File | What it is |
| --- | --- |
| `captain-consent-cutover.container.json` | The GTM import file. Import this. |
| `build-cutover.py` | Deterministic build script that produced the JSON by selecting real objects out of four production containers. Re-runnable. |
| `README.md` | This file. |

## What is in the container

**One inlined custom template** (`Captain Compliance CMP`, type `cvt_00000000_1`) - our local
`../template.tpl`, embedded verbatim as `templateData`. It has no `galleryReference` because it
is a locally-authored template until published to the GTM gallery.

**Two tags**

1. `Captain Compliance CMP - Banner + Consent Mode` - an instance of the inlined template.
   Fires on **Consent Initialization - All Pages**. It loads the banner
   (`<bannerBaseUrl>/banner/script?accessToken=...`) and runs Consent Mode v2
   (`setDefaultConsentState` on load, `updateConsentState` on choice). Set its **`accessToken`**
   field to your property token; every other field is left at the template default.
2. `Captain Compliance CMP - Consent Normalization` - carried verbatim from the TDZK
   production container (Custom HTML). It dedupes the raw banner events and pushes one
   canonical `captainComplianceConsentNormalized` event. Fires on the
   `captainComplianceConsent` and `captainComplianceConsentUpdated` custom-event triggers.

**Four triggers**: `Consent Initialization - All Pages` (CONSENT_INIT),
`captainComplianceConsent`, `captainComplianceConsentUpdated`, and
`captainComplianceConsentNormalized` (all CUSTOM_EVENT).
**Point your downstream marketing/analytics tags at `captainComplianceConsentNormalized`** -
it is the single deduped signal.

**One built-in variable**: `Event` (so `{{Event}}` in the normalization tag resolves).

Everything site-specific was dropped: all `... Base Tag - <domain>` loaders, every
`Captain Compliance CMP (<domain>)` loader, `Cookie Preferences - Stamp CC Settings ID`,
`Net Adds - MCC level`, `eFax Protect Direct Sale`, and all non-Captain third-party
pixels / custom templates.

## The 13 canonical gating variables

Each variable body is **byte-identical to production** - selected from the source container
named in brackets, then normalized (placeholder account/container ids, sequential ids,
stripped folders/fingerprints). `{{variable}}` references are kept by name, so no id rewiring
was needed inside bodies.

| # | Variable | Source | Notes |
| --- | --- | --- | --- |
| 1 | `CaptainCookie` | 5CKCCV | 1st-party cookie `cc_consent_preference` |
| 2 | `CaptainCookieParsed` | 5CKCCV | `JSON.parse` of the cookie |
| 3 | `CaptainConsentStatus` | 5CKCCV | Cookie-based jsm form (`return parsed.status`). Self-contained, no dataLayer-timing dependency. |
| 4 | `CaptainPerformance` | 5CKCCV | DLV `...selectedCookies.PERFORMANCE_COOKIES` |
| 5 | `CaptainTargeting` | 5CKCCV | DLV `...TARGETING_COOKIES` |
| 6 | `CaptainFunctionality` | 5CKCCV | DLV `...FUNCTIONALITY_COOKIES` |
| 7 | `CaptainPerformancePassive` | KFGX26 | Reads `parsed.selectedCookies`, honors GPC, falls back to `optInRegion===false && status===undefined` |
| 8 | `CaptainTargetingPassive` | KFGX26 | Same passive form |
| 9 | `CaptainFunctionalityPassive` | KFGX26 | Same passive form |
| 10 | `CaptainGPCSignalDetected` | KFGX26 | `navigator.globalPrivacyControl === true` |
| 11 | `CaptainConsentExistedAtPageLoad` | KFGX26 | Memoized page-load snapshot |
| 12 | `CaptainTargeting (Active Accept)` | TDZK | Advanced / edge-case sessionStorage flag |
| 13 | `CaptainOptInRegion` | **NEW (authored)** | Merged superset, see below |

The THZDMWJ-only `CC_DL_Performance` / `CC_DL_Targeting` duplicates were skipped (redundant
with #4 / #5, and nothing references them).

## OptInRegion compliance flag - READ THIS

`CaptainOptInRegion` (#13) is **not copied from any single container**. It is a newly authored
UNION of all three region logics found across the sources. It treats a region as opt-in
(explicit consent required) when the `cc_consent_cc-modal-user-location` cookie country/region is:

- **Europe**: EU-27 + UK + EEA/EFTA + **Switzerland (CH)**
- **International (from KFGX26)**: BR, AR, TR, KR, TH, CN, IN, IL, AE, ZA, NG, KE
- **Canada**: Quebec only (`regionCode === 'QC'`)
- **United States**: `regionCode` in **CA, FL, IL, MA, PA, WA** (all-party-consent / elevated-risk states)

> **SUPERSET of all four source containers - this treats MORE regions as opt-in than any
> single production site did. Confirm this region list with Captain Compliance compliance
> before shipping.** The same warning is a comment at the top of the variable body.

Being over-inclusive on opt-in is the conservative (privacy-forward) default, but it can
suppress analytics/ads in regions a given customer is not legally required to. Trim the list
per customer if compliance signs off on a narrower footprint.

## How a customer imports it

1. In GTM, open the destination **Web** container.
2. **Admin -> Import Container**.
3. Choose `captain-consent-cutover.container.json`.
4. Select a workspace. Choose **Merge** (keep your existing tags) or **Overwrite** for a true
   clean cutover - overwrite only in a fresh/dedicated container.
5. Preview the import. The placeholder account/container ids (`0000000000` / `00000000`) are
   remapped to the destination automatically on import.
6. Open **Captain Compliance CMP - Banner + Consent Mode** and set **Access Token** to your
   property token (the placeholder is `PASTE-YOUR-CC-ACCESS-TOKEN`). Review the Consent Mode
   region list on the tag if needed.
7. Repoint any downstream tags to fire on **`captainComplianceConsentNormalized`**.
8. **Preview / QA**, then **Submit / Publish**.

## Rebuilding

```
python3 build-cutover.py
```

Reads the four source exports plus `../template.tpl`, rewrites the JSON, and prints the full
validation report (JSON parses, all 13 variables present, no site-specific tags, no dangling
`{{variable}}` references, banner tag type matches the customTemplate `cvt_` id, OptInRegion
union markers + warning present).
