# UltraCart: install the Captain Compliance CMP template

How to run the Captain Compliance banner and Google Consent Mode on an UltraCart
StoreFront through the community GTM template, plus the checklist we run on a
test store before calling the integration proven.

Sources checked 2026-10-27. Every UltraCart step links the UltraCart doc page it
comes from:

- **[UC-PT]** UltraCart, Privacy and Tracking:
  <https://docs.ultracart.com/storefronts-themes/tracking-analytics/>
- **[UC-GTM]** UltraCart, Integrating Google Tag Manager into Your UltraCart
  Storefront:
  <https://docs.ultracart.com/account-settings/tutorials/google-integration/google-tag-manager>

Section names in brackets after a link (for example "Tag Manager") are the
heading on that page.

## Scope

UltraCart gets the same shape as Shopify, BigCommerce and WordPress, built in
phases:

1. **GTM template path (this guide).** The merchant's own GTM container,
   loaded by UltraCart's Tag Manager field, runs the community template. No
   code on UltraCart's side and nothing for us to host.
2. **Later, if the template path holds up:** an UltraCart app that sets the
   container and the privacy settings for the merchant through UltraCart's
   OAuth developer apps. Not started, and not needed for phase 1.

Live clients use the community template from the Gallery, never an imported
`.tpl` download. Only Gallery installs count for Google.

## Before you start

- A Captain Compliance property and its Access Token (the property UUID).
- A GTM web container you can publish, and its ID (`GTM-XXXXXX`).
- Admin access to the UltraCart StoreFront.

## 1. Set up the template in GTM

These steps happen in GTM, not UltraCart, and are the same on every platform.
See [`INSTALL.md`](../INSTALL.md) for the full field list.

1. In the container: **Templates** → **Tag Templates** → **Search Gallery**,
   pick **Captain Compliance CMP** and add it to the workspace.
2. **Tags** → **New** → **Captain Compliance CMP**. Paste the Access Token.
   Leave **Consent scope** on "Use my Captain Compliance regions".
3. Set **GPC signal variable** to a Custom JavaScript variable returning
   `navigator.globalPrivacyControl === true` (the cutover container ships it as
   `{{CaptainGPCSignalDetected}}`).
4. Fire the tag on **Consent Initialization - All Pages**.
5. Put every other tag behind consent: Google tags rely on Consent Mode and fire
   on `captainComplianceConsentReady`; non-Google tags (Meta, affiliate,
   custom HTML) get a trigger condition on the `Captain*` variables. The
   [cutover container](../cutover/README.md) has all of this pre-wired.
6. **Submit** and **Publish**.

## 2. Connect the container to the StoreFront

1. Go to **Storefronts** → choose the StoreFront → **Privacy & Tracking** →
   **Google** tab → scroll to **Tag Manager**.
   Source: [UC-GTM] (Prerequisites, "Navigate").
2. Paste the GTM ID into **Container ID**.
   Source: [UC-GTM] (Prerequisites, "Container ID (Required)").
3. Leave **Server Side Script URL** blank unless the merchant hosts their own
   container. Source: [UC-GTM] ("Server Side Script URL (Optional - Advanced)").
4. Leave **Opt in to** unset, so the container is not held behind UltraCart's
   own consent. Our banner loads inside the container: if UltraCart holds the
   container until a visitor opts in, our banner never gets the chance to ask.
   UltraCart describes this field as its own GDPR gate, applied per tracking
   service (Statistics, Preferences or Marketing; All, EEA or Non-US
   customers). Captain Compliance does that job inside the container instead.
   Source: [UC-GTM] ("Opt in to (recommended)") and [UC-PT] ("Configuring GDPR
   with specific tracking services").
5. **Save.** UltraCart places the GTM snippets in the page `<head>` and
   `<body>` itself, so nothing is pasted by hand. UltraCart notes a warning
   that the script is not rendering in the head may show and the script still
   works; checklist item S3 confirms the container still loads ahead of the
   page's other scripts. Source: [UC-GTM] (Prerequisites, "Note").
6. **Google Tag Gateway** is optional and billed by UltraCart. If the merchant
   turns it on, the whole container (our tag included) loads through the store
   domain; the banner itself still loads from `cptn.co`. Run the checklist
   again after turning it on. Source: [UC-GTM] ("Google Tag Gateway
   (First-Party Serving)", "Custom and Third-Party Tags in Your GTM
   Container").

## 3. Turn off what would load outside the container

Anything UltraCart injects itself bypasses GTM, so our template cannot hold it.
Move each one into the GTM container behind consent, then clear it in
UltraCart:

1. **Privacy** sub-tab: turn off **Show Privacy/Cookie Notice**, so visitors see
   one banner, ours. The other Privacy settings (Anonymize IP, Default Mailing
   List Off and the rest) are not consent banners and can stay as they are.
   Source: [UC-PT] ("Privacy Settings").
2. **Google** sub-tab: the native **Adwords** and **Analytics** fields inject
   Google tags outside the container (Adwords on the receipt page, GA4 with
   `page_view` and `purchase`). Rebuild them as GTM tags and clear the native
   fields. The GA4 **API Secret** sends offline conversions server side, which
   no banner can hold, so leave it off unless the merchant's counsel says
   otherwise. Source: [UC-PT] ("Google Integrations", "Adwords",
   "Analytics").
3. **Other** sub-tab: the built-in third-party integrations (Facebook Pixel and
   the rest) are injected by UltraCart onto StoreFront pages. Rebuild them in
   GTM gated on the `Captain*` variables and clear them here.
   Source: [UC-PT] ("Other", "Third-Party Integrations").
4. **Custom** sub-tab, **Tracking HTML**: this goes on every non-receipt page.
   Move any pixels or scripts into GTM. Do not paste the Captain banner here;
   the GTM template is the install. Source: [UC-PT] ("Custom Tracking and
   Scripts", "Section 1: Tracking HTML").
5. **Affiliate Networks** sub-tab: UltraCart fires the matching network's
   conversion pixel on the receipt itself. Note which are on; they are covered
   by checklist item R4. Source: [UC-PT] ("Affiliate Networks").

### Script placement

UltraCart moves JavaScript to the bottom of the page by default to speed it up.
A script that must load in place takes the `data-uc-ignore` attribute, for
example `<script src="/js/myscript.js" data-uc-ignore></script>`. The GTM
snippets from the Tag Manager field are placed by UltraCart and do not need it.
If a merchant has a hand-placed GTM snippet in a theme instead of using the
Tag Manager field, switch them to the field (or add `data-uc-ignore` to the
snippet) so Consent Initialization runs before the page's other scripts.
Source: [UC-PT] ("Preventing Script Relocation").

## 4. Checkout and the receipt page

1. **Receipt page tags live in GTM.** UltraCart's **Conversion HTML** field
   (Custom sub-tab) is injected into the receipt page only and runs outside the
   container, so a pixel there fires with no consent check. Keep it empty and
   build purchase tags in GTM on a receipt page trigger, behind consent. Order
   values for those tags come from the data layer or from UltraCart's custom
   tokens. Source: [UC-PT] ("Section 2: Conversion HTML", "What Are UltraCart
   Custom Tokens?").
2. **Conversion Pixel Only If Payment Successful** (Advanced sub-tab) can stay
   on. It stops conversion scripts on declined payments and does not change
   consent. Source: [UC-PT] ("Advanced Settings").
3. **Custom Thank You URL.** If the merchant sends buyers to their own thank
   you page, UltraCart still loads its own receipt page first as a "please
   wait, in progress" screen so receipt pixels can fire, then hands off. Our
   template has to gate that screen too (checklist item R3), and the merchant's
   own thank you page needs the same GTM container installed on it.
   Source: [UC-PT] ("Hosting the thank you page on your own site",
   "Frequently Asked Questions").
4. **The container on checkout.** UltraCart's GTM page says the UTM and
   funnel_hostname data layer pushes run "on your StoreFront pages and on the
   receipt page", and names "checkout and receipt pages" as UltraCart-hosted
   pages where tags load. It does not say in so many words that the container
   loads on every checkout step, or on which host. Checklist items C1 and C2
   settle both. Source: [UC-GTM] ("Sending UltraCart's UTM Values to Your GA4
   Tag", "Multi-Domain and Headless Setups").

## Test store checklist

Run on an UltraCart test store with GTM **Preview** (Tag Assistant) connected,
in a fresh browser profile, once with no GPC and once with GPC on. Use a test
order for the receipt rows.

**Status: no test UltraCart account exists yet, so every row is Not yet run.**

| # | Page | Check | Result |
|---|------|-------|--------|
| S1 | Storefront (home, category, product, cart) | The Captain Compliance CMP tag fires on Consent Initialization, and `…/banner/script?accessToken=…` is requested before any other tag fires | Not yet run |
| S2 | Storefront | On the first event the Consent tab shows `ad_storage`, `analytics_storage`, `ad_user_data` and `ad_personalization` denied (in an opt-in region) and `security_storage` granted | Not yet run |
| S3 | Storefront | `gtm.js` loads from the page head and is not moved to the bottom of the page by UltraCart's script relocation | Not yet run |
| S4 | Storefront | Before a choice, no non-Google tag fires and Google tags send no cookies; after Accept they fire, after Reject they stay held | Not yet run |
| S5 | Storefront | Only the Captain banner shows; UltraCart's own Privacy/Cookie Notice does not | Not yet run |
| S6 | Storefront | With GPC on, ads and analytics stay denied after Accept | Not yet run |
| S7 | Storefront | View source has no tracking script outside the container (native Google fields, Other integrations, Tracking HTML all empty) | Not yet run |
| C1 | Checkout (every step) | The container loads on each checkout step and the CMP tag fires on Consent Initialization there | Not yet run |
| C2 | Checkout | The choice made on the storefront carries into checkout (`cc_consent_preference` readable on the checkout host); if checkout runs on a different host, the banner asks again rather than assuming consent | Not yet run |
| C3 | Checkout | With consent denied, no tag other than the CMP tag fires during checkout | Not yet run |
| R1 | Receipt | The container loads on the receipt page and the CMP tag fires on Consent Initialization | Not yet run |
| R2 | Receipt | With consent denied, no purchase or conversion tag fires; with consent granted they fire once | Not yet run |
| R3 | Receipt | With a Custom Thank You URL set, the "please wait" receipt screen holds tags the same way before the handoff | Not yet run |
| R4 | Receipt | Nothing fires from Conversion HTML, native Google conversion fields or Affiliate Networks without consent | Not yet run |
| R5 | Receipt | Tracking fires at all on a test order, so R2 is a real result and not a silent skip (the two UltraCart pages above do not cover test orders; confirm on the store) | Not yet run |

Record each run with the date, the store URL, the browser and a Tag Assistant
screenshot per row, and change Not yet run to Pass or Fail.
