# Captain Compliance CMP — GTM Community Template

A Google Tag Manager (Web) custom template that loads the Captain Compliance
consent banner **and** natively powers **Google Consent Mode v2**.

Unlike a plain "paste the banner script into a Custom HTML tag" setup, this
template does what Google's certified-CMP / Consent Mode audit requires:

1. On initialization it calls `setDefaultConsentState` with **all four required
   purposes** (`ad_storage`, `analytics_storage`, `ad_user_data`,
   `ad_personalization`) plus `functionality_storage`, `personalization_storage`
   and `security_storage` — **denied by default** in consent-required regions,
   region-scoped, with `wait_for_update` — **before** any Google tag fires.
2. It injects the Captain Compliance banner (`<base>/banner/script?accessToken=…`)
   early so the CMP UI, geo detection and GPC handling load.
3. When the visitor makes a choice, it reads the `captainComplianceConsent`
   dataLayer event (falling back to the `cc_consent_preference` cookie), maps
   Captain Compliance's categories to Google's signals, and calls
   `updateConsentState` so all four purposes flip correctly. GPC is honored.

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
| **Access Token** (required) | — | Your Captain Compliance property UUID. The only field a typical install needs. |
| Set Google Consent Mode default + update | on | Master switch for the native Consent Mode wiring. |
| Consent-required regions | EEA + UK + CH ISO codes | Regions where non-essential defaults to denied (opt-in). **Empty = apply denied to all regions** (required for a certification/audit test site). |
| Default state for opt-out regions | granted | US-style opt-out behavior outside the required list. |
| Wait for update (ms) | 500 | How long Google tags hold for the consent signal. |
| Honor GPC | on | Force ad/analytics denied when a GPC signal is present. |
| Enable ads_data_redaction | on | Redact ad identifiers while ad_storage is denied. |
| Enable url_passthrough | off | Pass ad click info via URL params when storage is denied. |
| Banner base URL (advanced) | `https://api-prod.cptn.co` | Override for staging / self-host. |
| Consent dataLayer event name (advanced) | `captainComplianceConsent` | The banner's consent event. |
| Consent cookie name (advanced) | `cc_consent_preference` | Fallback consent source. |
| Enable IAB TCF (advanced) | off | Only for vendors that need a TC string. Captain Compliance runs Consent Mode, not TCF, by default. |

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
