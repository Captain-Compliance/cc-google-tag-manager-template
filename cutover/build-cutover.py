#!/usr/bin/env python3
"""
Deterministic builder for the Captain Compliance "clean cutover" GTM container.

It SELECTS real objects out of the four source export containers so the carried
variable bodies are byte-identical to production, normalizes ids/account/container
placeholders, authors ONE new merged CaptainOptInRegion (superset of all four
source region logics), keeps the consent-normalization tag, drops every
site-specific / third-party tag, and inlines our local TAG template
(cc-google-tag-manager-template/template.tpl) as a customTemplate plus one tag
instance that fires on Consent Initialization.

Re-runnable: `python3 build-cutover.py` rewrites captain-consent-cutover.container.json
and prints the validation report. No hand-typed JSON bodies.
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)                       # cc-google-tag-manager-template/
TEMPLATE_TPL = os.path.join(REPO, "template.tpl")
SRC_DIR = "/home/malkady/clip-incoming/captaingtmexamples"

SRC = {
    "5CKCCV":  os.path.join(SRC_DIR, "GTM-5CKCCV_workspace1000213.json"),
    "KFGX26":  os.path.join(SRC_DIR, "GTM-KFGX26_workspace1000123.json"),
    "TDZK":    os.path.join(SRC_DIR, "GTM-TDZK_workspace1000925.json"),
    "THZDMWJ": os.path.join(SRC_DIR, "GTM-THZDMWJ_workspace539.json"),
}

OUT = os.path.join(HERE, "captain-consent-cutover.container.json")

# Placeholder identifiers used everywhere.
ACCT = "0000000000"
CONT = "00000000"
PUBLIC_ID = "GTM-XXXXXXX"

# --------------------------------------------------------------------------- #
# Load sources
# --------------------------------------------------------------------------- #
def load(key):
    with open(SRC[key]) as f:
        return json.load(f)["containerVersion"]

CV = {k: load(k) for k in SRC}

def getvar(key, name):
    for v in CV[key].get("variable", []):
        if v.get("name") == name:
            return json.loads(json.dumps(v))  # deep copy
    raise KeyError(f"variable {name!r} not found in {key}")

def gettag(key, name):
    for t in CV[key].get("tag", []):
        if t.get("name") == name:
            return json.loads(json.dumps(t))
    raise KeyError(f"tag {name!r} not found in {key}")

# --------------------------------------------------------------------------- #
# Normalize helper (applied to every carried-over object)
# --------------------------------------------------------------------------- #
def normalize(obj):
    obj["accountId"] = ACCT
    obj["containerId"] = CONT
    obj.pop("parentFolderId", None)
    obj["fingerprint"] = "0"
    return obj

# --------------------------------------------------------------------------- #
# 1. VARIABLES  (canonical superset, order = final variableId order)
# --------------------------------------------------------------------------- #
variables = []

# 12 carried-over variables selected from their designated source container.
carried = [
    ("5CKCCV",  "CaptainCookie"),
    ("5CKCCV",  "CaptainCookieParsed"),
    ("5CKCCV",  "CaptainConsentStatus"),           # cookie-based jsm form (self-contained)
    ("5CKCCV",  "CaptainPerformance"),
    ("5CKCCV",  "CaptainTargeting"),
    ("5CKCCV",  "CaptainFunctionality"),
    ("KFGX26",  "CaptainPerformancePassive"),       # GPC-aware passive form
    ("KFGX26",  "CaptainTargetingPassive"),
    ("KFGX26",  "CaptainFunctionalityPassive"),
    ("KFGX26",  "CaptainGPCSignalDetected"),
    ("KFGX26",  "CaptainConsentExistedAtPageLoad"),
    ("TDZK",    "CaptainTargeting (Active Accept)"),
]
for src, name in carried:
    variables.append(normalize(getvar(src, name)))

# 13. CaptainOptInRegion -- NEW authored merged jsm (UNION of all four logics).
OPTIN_JS = r"""function() {
  // SUPERSET of all four source containers - treats MORE regions as opt-in than
  // any single production site. Confirm this region list with Captain Compliance
  // compliance before shipping.
  var cookieMatch = document.cookie.match(/(?:^|; )cc_consent_cc-modal-user-location=([^;]*)/);
  if (!cookieMatch) return false;
  try {
    var cookieValue = decodeURIComponent(cookieMatch[1]);
    var locationData = JSON.parse(cookieValue);
    var code = locationData.countryCode.toUpperCase();
    var regionCode = locationData.regionCode ? locationData.regionCode.toUpperCase() : '';

    // Country-level opt-in (explicit consent required).
    var optIn = [
      // Europe: EU-27 + UK + EEA/EFTA + Switzerland (CH)
      'AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR','DE','GR','HU','IE','IT',
      'LV','LT','LU','MT','NL','PL','PT','RO','SK','SI','ES','SE','GB','UK',
      'IS','LI','NO','CH',
      // South America
      'BR','AR',
      // Asia-Pacific
      'TR','KR','TH','CN','IN',
      // Middle East
      'IL','AE',
      // Africa
      'ZA','NG','KE'
    ];

    // Canada: explicit opt-in required only for Quebec (QC).
    if (code === 'CA') {
      return regionCode === 'QC';
    }

    // United States: all-party-consent / elevated-risk states only.
    if (code === 'US') {
      // CA=California, FL=Florida, IL=Illinois, MA=Massachusetts, PA=Pennsylvania, WA=Washington
      var usOptInRegionCodes = ['CA', 'FL', 'IL', 'MA', 'PA', 'WA'];
      return usOptInRegionCodes.includes(regionCode);
    }

    return optIn.includes(code);
  } catch (e) {
    console.error('Error parsing cookie:', e);
    return false;
  }
}"""

optin = {
    "accountId": ACCT,
    "containerId": CONT,
    "name": "CaptainOptInRegion",
    "type": "jsm",
    "parameter": [
        {"type": "TEMPLATE", "key": "javascript", "value": OPTIN_JS}
    ],
    "fingerprint": "0",
    "formatValue": {},
}
variables.append(optin)

# Assign sequential variableId 1..N
for i, v in enumerate(variables, start=1):
    v["variableId"] = str(i)

# --------------------------------------------------------------------------- #
# 2. BUILT-IN VARIABLES  (only what the carried bodies resolve against)
# --------------------------------------------------------------------------- #
builtInVariable = [
    {"accountId": ACCT, "containerId": CONT, "type": "EVENT", "name": "Event"},
]

# --------------------------------------------------------------------------- #
# 3. TRIGGERS  (clean, sequential triggerId)
# --------------------------------------------------------------------------- #
def custom_event_trigger(name):
    return {
        "accountId": ACCT,
        "containerId": CONT,
        "name": name,
        "type": "CUSTOM_EVENT",
        "customEventFilter": [
            {
                "type": "EQUALS",
                "parameter": [
                    {"type": "TEMPLATE", "key": "arg0", "value": "{{_event}}"},
                    {"type": "TEMPLATE", "key": "arg1", "value": name},
                ],
            }
        ],
        "fingerprint": "0",
    }

trg_consent_init = {
    "accountId": ACCT,
    "containerId": CONT,
    "name": "Consent Initialization - All Pages",
    "type": "CONSENT_INIT",
    "fingerprint": "0",
}
trg_consent = custom_event_trigger("captainComplianceConsent")
trg_updated = custom_event_trigger("captainComplianceConsentUpdated")
trg_normalized = custom_event_trigger("captainComplianceConsentNormalized")

triggers = [trg_consent_init, trg_consent, trg_updated, trg_normalized]
for i, t in enumerate(triggers, start=1):
    t["triggerId"] = str(i)

# --------------------------------------------------------------------------- #
# 4. CUSTOM TEMPLATE  (inline our local template.tpl)
# --------------------------------------------------------------------------- #
with open(TEMPLATE_TPL) as f:
    template_data = f.read()

TEMPLATE_ID = "1"
custom_template = {
    "accountId": ACCT,
    "containerId": CONT,
    "templateId": TEMPLATE_ID,
    "name": "Captain Compliance CMP",
    "templateData": template_data,
    "fingerprint": "0",
    # NO galleryReference: this is a locally-authored template until published.
}
CVT_TYPE = "cvt_{}_{}".format(CONT, TEMPLATE_ID)

# --------------------------------------------------------------------------- #
# 5. TAGS  (keep normalization tag; add our banner tag; drop everything else)
# --------------------------------------------------------------------------- #
# 5a. Consent Normalization (carried from TDZK, Custom HTML).
norm = normalize(gettag("TDZK", "Captain Compliance CMP - Consent Normalization"))
norm.pop("monitoringMetadata", None)
norm["paused"] = False
# Rewire firing triggers: fire on the two raw consent events.
norm["firingTriggerId"] = [trg_consent["triggerId"], trg_updated["triggerId"]]

# 5b. Our inlined template instance (Banner + Consent Mode).
banner = {
    "accountId": ACCT,
    "containerId": CONT,
    "name": "Captain Compliance CMP - Banner + Consent Mode",
    "type": CVT_TYPE,
    "parameter": [
        {"type": "TEMPLATE", "key": "accessToken", "value": "PASTE-YOUR-CC-ACCESS-TOKEN"},
    ],
    "fingerprint": "0",
    "firingTriggerId": [trg_consent_init["triggerId"]],
    "tagFiringOption": "ONCE_PER_EVENT",
    "consentSettings": {"consentStatus": "NOT_SET"},
}

tags = [banner, norm]
for i, t in enumerate(tags, start=1):
    t["tagId"] = str(i)

# --------------------------------------------------------------------------- #
# 6. CONTAINER + ASSEMBLE
# --------------------------------------------------------------------------- #
container = {
    "accountId": ACCT,
    "containerId": CONT,
    "name": "Captain Compliance - Consent Cutover",
    "publicId": PUBLIC_ID,
    "usageContext": ["WEB"],
    "fingerprint": "0",
    "tagManagerUrl": "",
}

export = {
    "exportFormatVersion": 2,
    "exportTime": "2026-07-21 00:00:00",
    "containerVersion": {
        "accountId": ACCT,
        "containerId": CONT,
        "container": container,
        "builtInVariable": builtInVariable,
        "variable": variables,
        "trigger": triggers,
        "tag": tags,
        "customTemplate": [custom_template],
        "fingerprint": "0",
        "tagManagerUrl": "",
    },
}

with open(OUT, "w") as f:
    json.dump(export, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"Wrote {OUT}")

# --------------------------------------------------------------------------- #
# VALIDATION
# --------------------------------------------------------------------------- #
print("\n" + "=" * 68)
print("VALIDATION")
print("=" * 68)
results = []

# 1. json.load succeeds
try:
    with open(OUT) as f:
        doc = json.load(f)
    results.append(("json.load succeeds on output", True, ""))
except Exception as e:
    results.append(("json.load succeeds on output", False, str(e)))
    doc = None

cv = doc["containerVersion"] if doc else {}
var_names = [v["name"] for v in cv.get("variable", [])]
tag_names = [t["name"] for t in cv.get("tag", [])]

# 2. all 13 canonical variables present
CANON = [
    "CaptainCookie", "CaptainCookieParsed", "CaptainConsentStatus",
    "CaptainPerformance", "CaptainTargeting", "CaptainFunctionality",
    "CaptainPerformancePassive", "CaptainTargetingPassive", "CaptainFunctionalityPassive",
    "CaptainGPCSignalDetected", "CaptainConsentExistedAtPageLoad",
    "CaptainTargeting (Active Accept)", "CaptainOptInRegion",
]
print("\n-- canonical variables --")
all_present = True
for name in CANON:
    ok = name in var_names
    all_present = all_present and ok
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
results.append(("all 13 canonical variables present", all_present, ""))

# 3. no dropped/site-specific tag names; no non-Captain customTemplate
FORBIDDEN_SUBSTR = [
    "Base Tag -", "Stamp CC Settings ID", "Net Adds", "eFax Protect Direct Sale",
]
bad_tags = [t for t in tag_names
            if any(s in t for s in FORBIDDEN_SUBSTR)
            or (t.startswith("Captain Compliance CMP (") )
            or (not t.startswith("Captain Compliance"))]
ok3 = len(bad_tags) == 0
# customTemplate must be only our Captain one
ct_names = [c.get("name") for c in cv.get("customTemplate", [])]
ok3b = ct_names == ["Captain Compliance CMP"]
results.append(("no site-specific tags remain", ok3, ("offenders: " + str(bad_tags)) if bad_tags else ""))
results.append(("only Captain customTemplate remains", ok3b, "" if ok3b else str(ct_names)))

# 4. dangling reference scan
defined = set(var_names) | {b["name"] for b in cv.get("builtInVariable", [])}
ref_re = re.compile(r"\{\{([^}]+)\}\}")
orphans = set()
def scan(obj):
    if isinstance(obj, str):
        for m in ref_re.findall(obj):
            # ignore GTM internal refs like _event
            if m.startswith("_"):
                continue
            if m not in defined:
                orphans.add(m)
    elif isinstance(obj, dict):
        for v in obj.values():
            scan(v)
    elif isinstance(obj, list):
        for v in obj:
            scan(v)
for v in cv.get("variable", []):
    scan(v.get("parameter", []))
for t in cv.get("tag", []):
    scan(t.get("parameter", []))
ok4 = len(orphans) == 0
results.append(("no dangling {{variable}} references", ok4, ("orphans: " + str(sorted(orphans))) if orphans else ""))

# 5. inlined tag type matches customTemplate cvt id; templateData non-empty + TOS head
banner_tag = next((t for t in cv.get("tag", []) if t["name"].endswith("Banner + Consent Mode")), None)
ct = cv.get("customTemplate", [])[0]
expected_type = "cvt_{}_{}".format(ct["containerId"], ct["templateId"])
ok5a = banner_tag is not None and banner_tag["type"] == expected_type
ok5b = bool(ct.get("templateData")) and ct["templateData"].startswith("___TERMS_OF_SERVICE___")
results.append(("banner tag type matches cvt id", ok5a,
                "" if ok5a else f"{banner_tag and banner_tag['type']} != {expected_type}"))
results.append(("templateData non-empty + starts with ___TERMS_OF_SERVICE___", ok5b, ""))

# 6. OptInRegion union markers + compliance-warning comment
optin_body = next(p["value"] for v in cv["variable"] if v["name"] == "CaptainOptInRegion"
                  for p in v["parameter"] if p["key"] == "javascript")
markers = ["'CH'", "'BR'", "'QC'"] + ["'CA'", "'FL'", "'IL'", "'MA'", "'PA'", "'WA'"]
missing = [m for m in markers if m not in optin_body]
warn_ok = "SUPERSET of all four source containers" in optin_body and "Confirm this region list" in optin_body
ok6 = (not missing) and warn_ok
results.append(("OptInRegion contains union markers (CH,BR,QC,US states)", not missing,
                ("missing: " + str(missing)) if missing else ""))
results.append(("OptInRegion has compliance-warning comment", warn_ok, ""))

# summary
print("\n-- checks --")
allpass = True
for name, ok, detail in results:
    allpass = allpass and ok
    line = f"  [{'PASS' if ok else 'FAIL'}] {name}"
    if detail:
        line += f"  ({detail})"
    print(line)

print("\n" + "=" * 68)
print("FINAL:", "PASS - all checks green" if allpass else "FAIL - see above")
print("=" * 68)
sys.exit(0 if allpass else 1)
