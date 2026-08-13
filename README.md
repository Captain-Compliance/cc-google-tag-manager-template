# Captain Compliance CMP: GTM Community Template

A Google Tag Manager (Web) custom template that loads the Captain Compliance
consent banner **and** natively powers **Google Consent Mode v2**.

Unlike a plain "paste the banner script into a Custom HTML tag" setup, this
template does what Google's certified-CMP / Consent Mode audit requires:

1. On initialization it calls `setDefaultConsentState` with **all four required
   purposes** (`ad_storage`, `analytics_storage`, `ad_user_data`,
   `ad_personalization`) plus `functionality_storage`, `personalization_storage`
   and `security_storage`, **denied by default** according to your chosen
   [consent scope](#choosing-your-consent-scope), with `wait_for_update`,
   **before** any Google tag fires.
2. It injects the Captain Compliance banner (`<base>/banner/script?accessToken=…`)
   early so the CMP UI, geo detection and GPC handling load.
3. When the visitor makes a choice, it reads the `captainComplianceConsent`
   dataLayer event (falling back to the `cc_consent_preference` cookie), maps
   Captain Compliance's categories to Google's signals, and calls
   `updateConsentState` so all four purposes flip correctly. GPC is honored.

> **Two surfaces, one system.** This tag template steers **Google** tags via
> Consent Mode. To gate **any other** tag (non-Google pixels, custom HTML,
> third-party vendors) by consent category, use the **`Captain*` variables**
> described in [Gating any tag by category](#gating-any-tag-by-category) below.
> Both come pre-wired in the [one-file cutover container](#one-file-install-the-cutover-container).

## Category mapping

Captain Compliance uses three consent categories; Google Consent Mode v2 uses
seven signals. The template maps them like this:

| Captain Compliance category | Google Consent Mode signal(s) |
|-----------------------------|-------------------------------|
| `PERFORMANCE_COOKIES`       | `analytics_storage` |
| `TARGETING_COOKIES`         | `ad_storage`, `ad_user_data`, `ad_personalization`, `personalization_storage` |
| `FUNCTIONALITY_COOKIES`     | `functionality_storage` |
| `STRICTLY_NECESSARY_COOKIES`| `security_storage` (always granted) |

## Fields

| Field | Default | Purpose |
|-------|---------|---------|
| **Access Token** (required) | none | Your Captain Compliance property UUID. The only field a typical install needs. |
| Set Google Consent Mode default + update | on | Master switch for the native Consent Mode wiring. |
| Consent scope | Opt-In (Specified Regions Only) | How the pre-consent default is applied. Four modes, see [Choosing your consent scope](#choosing-your-consent-scope). |
| Specified Regions (ISO 3166 codes, comma-separated) | blank | The regions the specified-region rule applies to. In opt-in mode they are denied (opt-in); in opt-out mode they are granted (opt-out). Blank denies everywhere. Shown for both specified-region modes. |
| Wait for update (ms) | 500 | How long Google tags hold for the consent signal. |
| Honor GPC | on | Force ad/analytics denied when a GPC signal is present. |
| Enable ads_data_redaction | on | Redact ad identifiers while ad_storage is denied. |
| Enable url_passthrough | off | Pass ad click info via URL params when storage is denied. |
| Banner base URL (advanced) | `https://api-prod.cptn.co` | Override for staging / self-host. |
| Consent dataLayer event name (advanced) | `captainComplianceConsent` | The banner's consent event. |
| Consent cookie name (advanced) | `cc_consent_preference` | Fallback consent source. |
| Enable IAB TCF (advanced) | off | Only for vendors that need a TC string. Captain Compliance runs Consent Mode, not TCF, by default. |

## Choosing your consent scope

The **Consent scope** field controls the pre-consent default (`setDefaultConsentState`),
the state that applies before the visitor makes a choice. Pick one of four modes:

- **Opt-In (Specified Regions Only)** (recommended). Non-essential storage is **denied**
  in the regions you list and **granted** everywhere else. This is the standard EEA-opt-in /
  US-opt-out setup. Fill the **Specified Regions** field with the regions where you require opt-in.
- **Opt-Out (Specified Regions Only)**. The inverse: non-essential storage is **granted**
  (opt-out) in the regions you list and **denied** (opt-in) everywhere else. Use this to go
  opt-in globally except a few opt-out regions, for example opt-in worldwide but opt-out in
  the U.S. Put those opt-out regions in the **Specified Regions** field.
- **Opt-In (Everywhere)**. Non-essential storage is **denied in every region** until the
  visitor consents. Use this for a globally strict site, or for a **Google certification /
  audit test site**, which must run Consent Mode everywhere. No region list is needed.
- **Opt-Out (Everywhere)**. Everything is **granted** until the visitor opts out. Weakest
  posture, only for cases with no opt-in requirement anywhere.

The **Specified Regions** field is shared by both specified-region modes, so it has no
default; enter the ISO 3166 codes for whichever rule you picked. Leaving it blank denies
non-essential everywhere (safe fallback). To go fully global in either direction, pick one
of the two "Everywhere" modes rather than clearing the region list.

`security_storage` (strictly necessary) is always granted. Per-category behaviour after the
visitor chooses comes from the banner's own categories, and for a single tag that needs
bespoke gating you can add Google tag consent settings or a trigger condition. There is no
per-category default in the template on purpose: defaulting a non-essential purpose to
granted before consent is exactly what Consent Mode's default-denied is meant to prevent in
opt-in regions.

## Permissions declared

- `access_consent` (read + write) for `ad_storage`, `ad_user_data`,
  `ad_personalization`, `analytics_storage`, `functionality_storage`,
  `personalization_storage`, `security_storage`.
- `inject_script` limited to `https://api-prod.cptn.co/*` and `https://*.cptn.co/*`.
- `read_data_layer` for `captainComplianceConsent`.
- `get_cookies` for `cc_consent_preference`.
- `logging` (debug environment).

## How it should fire

Set the tag to fire on **Consent Initialization - All Pages** (or, if that
trigger is unavailable, **All Pages / Initialization**) so the default consent
state is set before every other Google tag. The template also registers a
consent listener, so it reacts to later banner changes without re-firing.

## Gating any tag by category

Consent Mode only steers Google tags. To hold **any** tag (a Meta pixel, a
custom HTML tag, a third-party vendor) until the visitor consents to the right
category, gate it on a trigger condition using the **`Captain*` variables**.
These read the banner's `cc_consent_preference` cookie / `captainComplianceConsent`
dataLayer event and expose consent as GTM variables you can reference anywhere:

| Variable | Type | What it returns |
|----------|------|-----------------|
| `CaptainCookie` | 1st-party cookie | raw `cc_consent_preference` value |
| `CaptainCookieParsed` | custom JS | the parsed consent object |
| `CaptainConsentStatus` | custom JS | `accepted` / `rejected` / `undefined` (no choice yet) |
| `CaptainPerformance` | data layer | `true` when Performance/analytics is consented |
| `CaptainTargeting` | data layer | `true` when Targeting/ads is consented |
| `CaptainFunctionality` | data layer | `true` when Functionality is consented |
| `CaptainPerformancePassive` / `…TargetingPassive` / `…FunctionalityPassive` | custom JS | category state **including** the pre-interaction default; GPC-aware (returns `false` under GPC) |
| `CaptainOptInRegion` | custom JS | `true` when the visitor is in a consent-required (opt-in) region |
| `CaptainGPCSignalDetected` | custom JS | `true` when a Global Privacy Control signal is present |
| `CaptainConsentExistedAtPageLoad` | custom JS | `true` when a prior consent choice was already stored |
| `CaptainTargeting (Active Accept)` | custom JS | `true` only on an explicit accept (not passive/implied) |

Typical use: on your Meta pixel tag, add a trigger that fires only when
`CaptainTargeting` equals `true`. The tag stays blocked until the visitor
consents to targeting, and fires the moment they do.

You do **not** need to hand-build these; they ship pre-wired in the cutover
container below.

## One-file install: the cutover container

`cutover/captain-consent-cutover.container.json` is a GTM **container import**
that installs the whole setup in one step, replacing the old copy-paste recipe:

- every `Captain*` variable above (reconciled from production containers),
- the consent-normalization tag (so the data-layer variables resolve),
- **this template inlined** as the banner + Consent Mode tag,
- clean triggers, with all site-specific loaders stripped out.

Import it into a GTM workspace, paste your access token into the
`Captain Compliance CMP - Banner + Consent Mode` tag, and you are fully cut over.
See [`cutover/README.md`](cutover/README.md) for details, including the
`CaptainOptInRegion` region list (shipped as an editable default; trim it to
your own compliance posture).

## Testing

The template ships with `___TESTS___` scenarios covering: defaults set on init,
empty-region (all regions) mode, banner injection, consent update flipping all
four purposes, and the GPC path. Run them from the template editor's **Tests**
tab. See `INSTALL.md` for end-to-end verification in Tag Assistant.

## Gallery publication

Publishing to the GTM Community Template Gallery is a **separate step** (public
GitHub repo + submission at <https://tagmanager.google.com/gallery>). See
`INSTALL.md`.

Licensed under Apache 2.0 (see `LICENSE`).
