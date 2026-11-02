# UltraCart installer app: plan

The plan for a Captain Compliance app that a merchant installs on their
UltraCart account through OAuth, built the same way as the Shopify app
(cc-plugin-shopify) and the BigCommerce app (cc-app-bigcommerce), so Captain gets
an UltraCart listing. Decided Nov 1, 2026 (#12). It replaces "GTM template
first" as the UltraCart route; the manual guide in [`ultracart.md`](ultracart.md)
stays as the fallback and as the checklist the app is proven against.

No code is written until this plan is read and signed off.

Sources checked 2026-11-02:

- **[UC-OAUTH]** UltraCart, OAuth 2.0 Guide:
  <https://docs.ultracart.com/developer/essentials/oauth>
- **[UC-OAUTH-API]** UltraCart, OAuth endpoints (token, me, device, revoke):
  <https://docs.ultracart.com/developer/api/oauth> and
  <https://docs.ultracart.com/developer/api/oauth-me>
- **[UC-AUTH]** UltraCart, Authentication:
  <https://docs.ultracart.com/developer/essentials/authentication>
- **[UC-RATE]** UltraCart, Rate limiting:
  <https://docs.ultracart.com/developer/essentials/rate-limiting>
- **[UC-SDK]** UltraCart REST API v2 SDK (JavaScript, version 3.11.67, Feb 24,
  2026), the full endpoint list and the OAuth scope list:
  <https://github.com/UltraCart/rest_api_v2_sdk_javascript#documentation-for-authorization>
- **[UC-DEV]** UltraCart, Developer accounts:
  <https://www.ultracart.com/pricing/developers>
- **[UC-API]** UltraCart, API and webhooks overview:
  <https://www.ultracart.com/resources/api-and-webhooks.html>
- **[UC-PT]** and **[UC-GTM]**: the Privacy and Tracking and Google Tag Manager
  pages already cited in [`ultracart.md`](ultracart.md#ultracart-install-the-captain-compliance-cmp-template).

## What I found that shapes the plan

Two facts change the plan from a straight copy of the Shopify app:

1. **UltraCart's API cannot write the Privacy & Tracking tab.** The REST API v2
   has OAuth, StoreFront pages, the theme file manager, the code library,
   webhooks and the commerce objects, but no endpoint for the Tag Manager
   Container ID, the Privacy/Cookie Notice switch, the native Google and Other
   integrations or the Tracking and Conversion HTML fields [UC-SDK]. The
   endpoint that lists StoreFronts is marked "internal use only for security
   reasons" [UC-SDK]. On Shopify the app writes a ScriptTag and on BigCommerce
   a Script Manager entry; on UltraCart today there is no matching call.
2. **I found no public UltraCart App Store.** docs.ultracart.com (1,681 pages in
   its sitemap) and www.ultracart.com have no App Store, app marketplace or
   listing review page. `/apps/`, `/app-store/`, `/integrations/` and
   `/partners/` on www.ultracart.com return 404. What UltraCart does publish is
   OAuth Developer Applications, which any developer registers in their own
   account [UC-OAUTH], and an Integrations page of built-in features. So the
   listing itself has to start with a conversation with UltraCart (see
   [App Store listing review](#app-store-listing-review)).

The plan below works with today's API and asks UltraCart for the one endpoint
that would make install one click.

## The UltraCart developer app

- **Where it is registered.** In the UltraCart admin under Configuration →
  Development → Authorized Applications / API Keys → Developer Applications.
  That screen sets the application name, developer information, redirect URL
  and permissions. It also issues the client ID and secret [UC-OAUTH]. Developer
  accounts are free, need no card and include OAuth Developer Applications
  [UC-DEV].
- **Name.** "Captain Compliance Cookie Consent" (the Shopify app is "Captain
  GDPR Cookie Consent"; final name is Mo's call with the listing).
- **Redirect URL.** `https://ultracart.cptn.co/auth/callback` (one host per
  environment: `ultracart-dev.cptn.co` for dev, behind Tailscale like the rest
  of dev).
- **Flow.** Authorization code [UC-OAUTH]:
  1. The merchant clicks Connect. We send them to
     `https://secure.ultracart.com/admin/v2/oauth/authorize?client_id=…&redirect_uri=…&state=…&response_type=code`
     with a one-time `state` tied to their Captain session.
  2. They log into UltraCart and approve.
  3. UltraCart redirects back with `code` and `state`. We check `state`, then
     `POST https://secure.ultracart.com/rest/v2/oauth/token` with
     `grant_type=authorization_code`. The response has `access_token`,
     `refresh_token`, `expires_in` and `scope` [UC-SDK].
  4. We call `GET /oauth/me` at once to learn which UltraCart merchant
     account approved and which permissions it granted [UC-OAUTH-API].
  5. Refresh with `grant_type=refresh_token` before `expires_in` runs out.
  6. Disconnect calls `POST /oauth/revoke`. A `410` on any call means UltraCart
     disabled the app; a `401` after refresh means the merchant revoked it. Both
     mark the store disconnected [UC-OAUTH-API].
- **Where it runs.** A new repo, `cc-app-ultracart`, a small Node service on
  Fly under the scoped Captain token, shaped like cc-app-bigcommerce: OAuth
  routes, a settings view that deep-links to the Captain dashboard and a
  storefront verifier. It holds no data of its own; every row lives in
  cc-platform-api (next section).

## OAuth scopes

UltraCart sets permissions on the Developer Application, not per request, and
records what each merchant approved at the time they approve. Adding a
permission later does not reach merchants already connected until they approve
again [UC-OAUTH-API]. So the first set matters.

| Scope | Why | v1 |
|---|---|---|
| `storefront_read` | Find the merchant's StoreFronts, their hostnames and themes, so the app knows which hosts to verify | Yes |
| `storefront_write` | Only for the theme file route (Install route B below): write the GTM snippet into the theme's head template | No, held until Mo signs off on route B |
| everything else (`order_*`, `customer_*`, `item_*`, `checkout_*`, `configuration_*`, `user_*`, `webhook_*` and the rest of the list in [UC-SDK]) | Not needed. The banner and the template do the consent work in the browser | Never |

v1 asks for `storefront_read` and nothing else. No order, customer or checkout
data ever reaches Captain through the app. `configuration_read` and
`configuration_write` exist in the scope list but no published endpoint uses
them for Privacy & Tracking, so we do not ask for them until UltraCart says an
endpoint needs them.

## What we store per store and where

Settings live in the database and are controlled from Watchtower, never in env
vars. The app service is stateless.

**Table `UltraCartStore` in cc-platform-api's Postgres**, next to
`ShopifyStore` (migration `20251221163700_add_shopify_store`), with the same
link to a Captain scanner and account:

| Column | What |
|---|---|
| `id` | Primary key |
| `merchantId` | UltraCart merchant ID from `/oauth/me`, unique |
| `scannerId` | The Captain property (foreign key to `Scanner`), as on `ShopifyStore` |
| `userId`, `organizationId` | The Captain user and organization who connected it |
| `storefronts` | JSON: each StoreFront's oid and hostname, and which ones the banner covers |
| `gtmContainerId` | The merchant's `GTM-XXXXXX` |
| `installMethod` | `guided` (route A), `theme_file` (route B) or `api` (route C, once UltraCart ships it) |
| `themeFileRefs` | JSON: the theme file paths and versions the app changed, so uninstall can put them back (route B only) |
| `grantedScopes` | The permission list from `/oauth/me` |
| `accessToken`, `refreshToken` | Encrypted at rest; never returned by any endpoint, never shown in Watchtower |
| `tokenExpiresAt` | From `expires_in` |
| `status`, `statusMessage` | `connected`, `needs_setup`, `verified`, `drift`, `disconnected` and why |
| `lastVerifiedAt`, `lastVerifyResult` | The last storefront check (JSON per page: storefront, checkout, receipt) |
| `isActive`, `installedAt`, `createdAt`, `updatedAt` | As on `ShopifyStore` |

- **Endpoints** in cc-platform-api, mirroring `src/shopify`: link a store
  (behind `AuthenticationGuard`, the merchant's Captain login), unlink (behind
  an app key guard like `ShopifyAppKeyGuard`), read status, record a verify
  result. A route guard entry for each in `scripts/security`.
- **Watchtower** shows each UltraCart store: property, merchant, StoreFronts,
  container, install method, status and last check. It can also switch a store off.
- **What stays in env vars:** only secrets, never settings. The UltraCart client
  secret and the token encryption key, as Fly secrets on the app and the API.
- **What we never store:** shopper data, orders, customers, consent records
  (consent logging stays in the Captain platform).

## Install into the storefront

The manual guide [`ultracart.md`](ultracart.md) is the install. The app does
each step for the merchant where UltraCart's API allows it, walks them through
it where it does not, then checks the live pages. Three routes, from what works
today to what needs UltraCart:

- **Route A, guided (v1, works with today's API).** The app shows each step
  with the merchant's own values filled in and a "check now" button after
  each one. Nothing in UltraCart is written by us.
- **Route B, theme file (needs Mo's sign-off and the test store).** With
  `storefront_write`, the app writes the GTM snippet into the active theme's
  head template through the file manager endpoints (`getFsDirectory`,
  `getUploadFsFileUrl`, `uploadFsFile` in [UC-SDK]) with `data-uc-ignore`, and
  records what it changed so uninstall can restore it. It edits the merchant's
  own theme and a theme update can drop it. I do not know yet whether checkout
  and the receipt render from the same template. Only on the test store first.
- **Route C, API (needs UltraCart).** We ask UltraCart for an OAuth endpoint
  that reads and writes the Tag Manager Container ID and the Privacy/Cookie
  Notice switch. With it, install becomes one click like Shopify. UltraCart
  ships SDK changes most weeks [UC-SDK change log], so this is a fair ask.

Step by step, with the route that does each one:

| Step | From [`ultracart.md`](ultracart.md) | v1 (route A) | Later |
|---|---|---|---|
| 1 | [1. Set up the template in GTM](ultracart.md#1-set-up-the-template-in-gtm): Gallery template, Access Token, GPC variable, Consent Initialization | Merchant does it in GTM with our values shown; or the cutover container | Google OAuth from cc-admin-interface#132 adds the Gallery template tag for them. Always the Gallery template, never an imported `.tpl`, so the install counts for Google |
| 2 | [2. Connect the container](ultracart.md#2-connect-the-container-to-the-storefront): Privacy & Tracking → Google → Tag Manager → Container ID; leave Opt in to unset | Deep link plus the exact values; app verifies | Route C writes it; route B writes the snippet into the theme |
| 3 | [3. Turn off what would load outside the container](ultracart.md#3-turn-off-what-would-load-outside-the-container): Show Privacy/Cookie Notice off; native Adwords, Analytics, Other integrations and Tracking HTML moved into GTM | Checklist; app reads the public page and lists every tracking script it finds outside the container | Route C turns the notice off |
| 4 | [Script placement](ultracart.md#script-placement): UltraCart moves scripts to the bottom unless `data-uc-ignore` | App checks `gtm.js` is in the head and loads before other tags (checklist S3) | Route B adds `data-uc-ignore` itself |
| 5 | [4. Checkout and the receipt page](ultracart.md#4-checkout-and-the-receipt-page): Conversion HTML empty, purchase tags in GTM behind consent, Custom Thank You URL needs the container too | Checklist; app warns when a Custom Thank You URL is set | Same |

**How the app checks a store.** It fetches the StoreFront's public pages from
the server (home, a product, the cart) and `https://www.googletagmanager.com/gtm.js?id=<container>`,
and confirms: the container ID is on the page, `gtm.js` sits in the head, the
container includes the Captain Compliance CMP template and no tracking script
loads outside the container. These map to checklist rows S1, S3 and S7.
Checkout and the receipt need a real cart and a test order, so C1 to C3 and R1
to R5 are run by hand on the test store before launch and again after any
route B change. A store whose check fails shows `drift` in the app and in
Watchtower, like the BigCommerce app's `detectDrift()`.

**Uninstall.** Revoke the token, mark the row inactive, undo any route B theme
change from `themeFileRefs` and tell the merchant to clear the Container ID
(route A writes nothing, so it removes nothing).

## App Store listing review

UltraCart publishes no App Store or listing review rules that I could find
(checked 2026-11-02, see [What I found](#what-i-found-that-shapes-the-plan)).
What their pages do require, and what the Shopify and BigCommerce listings
taught us, gives this list:

From UltraCart's pages:

- A registered Developer Application with name, developer information,
  redirect URL and permissions [UC-OAUTH].
- The redirect URL must match one registered on the app, and the `state`
  parameter must round-trip [UC-OAUTH].
- Tokens kept server side, never shown to the merchant or committed
  [UC-OAUTH].
- Stay inside UltraCart's rate limits; a `429` means back off [UC-RATE].
- Handle a disabled app (`410`) cleanly [UC-OAUTH-API].
- A developer account to build and test in, with locked StoreFronts and test
  transactions [UC-DEV].

What a listing review asks for elsewhere and we should have ready:

- Least-privilege scopes with one line each on why (`storefront_read` only).
- A privacy policy and terms URL for the app, and a support contact.
- A data handling statement: what we store (the table above), where, how long,
  and that no shopper, order or customer data is read.
- Install, uninstall and reconnect working on a test store, with screenshots of
  each step and the test store checklist in [`ultracart.md`](ultracart.md#test-store-checklist)
  filled in.
- Listing copy: name, short and long description, icon, screenshots, pricing
  (Captain plans; no UltraCart billing in v1).
- Plain statement of limits: install is guided until UltraCart's API can write
  the Tag Manager field; checkout and receipt need the same container.

**To find out from UltraCart** (first step, via
<https://www.ultracart.com/help/support.html> or a contact Mo has): whether a
listing exists for third-party apps and how to apply; their review
requirements; and whether they will add an OAuth endpoint for the Tag Manager
Container ID and the Privacy/Cookie Notice switch (route C).

## Needs Mo's sign-off

These touch client data or security. Per the venture rules, anything that hosts
client data gets auth, a security review and Mo's sign-off.

1. **The scope list.** `storefront_read` only in v1. Adding any scope later
   means every merchant approves again.
2. **Storing merchant OAuth tokens** in cc-platform-api's Postgres: the
   `UltraCartStore` table, encryption at rest, where the key lives (Fly secret),
   who can read the row (no endpoint returns the token; Watchtower never shows
   it).
3. **The new endpoints** in cc-platform-api and their guards, and a security
   review of the app service before it goes live.
4. **Route B (theme file writes).** Writing into a merchant's theme with
   `storefront_write`. Only after it is proven on the test store.
5. **Google OAuth to write the merchant's GTM container** (cc-admin-interface#132),
   if the app uses it for step 1.
6. **The listing text and its compliance claims**, and the app's privacy policy
   and data handling statement.
7. **Contacting UltraCart** about the listing and route C, as Captain.

## What Mo provides

1. **An UltraCart developer account** (free, no card [UC-DEV]), or Captain's
   existing UltraCart login if there is one. It is where the Developer
   Application is registered and where the client ID and secret come from. The
   secret goes straight to Fly, never into a file or a chat.
2. **A test UltraCart store.** A StoreFront in the developer account may be
   enough: it runs the full theme stack with test transactions [UC-DEV]. If
   test orders do not fire receipt tracking (checklist R5), a real paid test
   store is needed; that is a spend and comes back as its own question.
3. **A GTM container** for the test store, and a Captain test property and its
   Access Token.
4. **The UltraCart contact** for the listing, if Mo already has one.
5. **Sign-off** on the list above before code starts.

## Build order once signed off

1. `UltraCartStore` table, migration and endpoints in cc-platform-api (dev
   first), with route guards.
2. `cc-app-ultracart`: OAuth connect, `/oauth/me`, refresh, revoke, link to a
   Captain property.
3. Route A guided install and the server side page check.
4. Watchtower view of UltraCart stores.
5. Test store checklist run in full; results recorded in
   [`ultracart.md`](ultracart.md#test-store-checklist).
6. Security review, then the listing.
7. Route B or C only after the above, and only with sign-off (B) or UltraCart's
   endpoint (C).
