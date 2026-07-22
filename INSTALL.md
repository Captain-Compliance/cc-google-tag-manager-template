# Install & Verify: Captain Compliance CMP GTM Template

Team instructions for importing, configuring, testing, and deploying the
Consent-Mode-native Captain Compliance template.

---

## 1. Import the template into a workspace

You can install from the Gallery once published, or import `template.tpl`
directly (use this during development / before publication):

1. In GTM, open the target container and select a workspace.
2. Left nav → **Templates** → under **Tag Templates** click **New**.
3. In the template editor, click the **⋮** (top right) → **Import**.
4. Choose `template.tpl` from this repo. Click **Save**, then close the editor.

The template now appears under **Tag Templates**.

---

## 2. Create the tag and configure fields

1. **Tags** → **New** → **Tag Configuration** → pick **Captain Compliance CMP**.
2. Fill in the fields:
   - **Access Token** (required): paste the property UUID from the Captain
     Compliance dashboard. For a basic install this is the only field to touch.
   - **Consent-required regions**: leave the default (EEA + UK + CH) for a real
     customer. **For a Google certification / audit test site, set this to
     EMPTY** so Consent Mode is enabled for all regions (Google requires this on
     the audit site).
   - Leave **Set Google Consent Mode**, **Honor GPC**, **wait_for_update = 500**
     at defaults.
   - **Advanced** → only change **Banner base URL** for staging/self-host.
3. **Triggering**: fire on **Consent Initialization - All Pages**. This
   guarantees `setDefaultConsentState` runs before every Google tag. (If that
   trigger type is not offered, use **Initialization - All Pages**.)
4. **Save**.

> One tag = one property/token. For multi-domain sites, add one tag per domain
> (each with its own access token), and scope each tag's trigger to its hostname.

---

## 3. Verify in Tag Assistant / Consent Mode debug

1. Click **Preview** in GTM and load the site in the connected tab.
2. In Tag Assistant, open the **Consent** tab (or add the **On-page** consent
   panel). Confirm the **default** state on the very first event:
   - `ad_storage`, `analytics_storage`, `ad_user_data`, `ad_personalization`
     all show **denied** (in a consent-required region, or everywhere if the
     region list is empty).
   - `security_storage` shows **granted**.
3. Confirm the Captain Compliance banner renders and the network tab shows a
   request to `…/banner/script?accessToken=…`.
4. Make a choice in the banner (Accept / customize). On the resulting
   `captainComplianceConsent` event, confirm the **Consent** tab now shows the
   updated (**granted** where accepted) values for all four purposes, and that
   the change was applied via `updateConsentState`.
5. GPC check: load with a GPC-signalling browser/extension. Confirm ad and
   analytics purposes stay **denied** even after an "accept".
6. Cross-check in the browser console: `google_tag_data.ics` reflects the same
   grant/deny states, and the `cc_consent_preference` cookie holds the JSON with
   `selectedCookies`.

Also run the built-in unit tests: template editor → **Tests** tab → **Run all**.
All five scenarios (init defaults, all-regions, injection, update, GPC) pass.

---

## 4. Deploy for a real customer

1. Confirm the correct **Access Token** and the region list is the real
   consent-required set (not empty; empty is only for the audit test site).
2. **Submit** the workspace changes → **Publish**.
3. Smoke-test the live site with Tag Assistant one more time (steps in §3).

---

## 5. Gallery publication (separate, required for certification)

Publishing to the Community Template Gallery is **not** the same as importing the
`.tpl`. To be listed and to complete Google's certified-CMP process:

1. Push this repo to a **public** GitHub repository whose root contains
   `template.tpl`, `metadata.yaml`, `LICENSE`, and `README.md`.
2. Ensure `metadata.yaml` `versions[].sha` matches the published commit and the
   `changeNotes` are current.
3. Go to <https://tagmanager.google.com/gallery> → **Submit your template** and
   point it at the public repo.
4. Google reviews the submission. For CMP certification, the audit site must
   have Consent Mode enabled for **all regions** (region list empty) and must
   demonstrably set the four purposes on default and on update, which this
   template does.
