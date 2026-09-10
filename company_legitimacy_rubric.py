"""
company_legitimacy_rubric.py

A weighted scoring rubric for an AI research agent to judge whether a company
looks like a real, currently-operating business (vs. a shell, defunct, or
fraudulent entity), based on evidence gathered via web research.

HOW AN AGENT USES THIS
-----------------------
1. For each entry in RUBRIC, use a web tool to look for the evidence
   described in "evidence_guidance".
2. Record a score from 0.0 to 1.0 for that id in a results dict:
     - "binary" items  -> 1.0 if clearly present, else 0.0
     - "graded" items  -> any fraction 0.0-1.0 for partial evidence
3. Do the same for each entry in RED_FLAGS (1.0 = clearly present,
   0.0 = not found, a fraction = ambiguous/partial).
4. Call score_company(results) for the final 0.0-1.0 score, a
   per-category breakdown, and a plain-language verdict.

All points are on a 0.00-1.00 scale (one "point" = 0.01). The 24 criteria
in RUBRIC sum to exactly 1.00. RED_FLAGS are separate deductions applied
on top, and the final score is clamped back into [0.0, 1.0].
"""

from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# 1. POSITIVE CRITERIA
#    id                  unique key used in the results dict
#    category            grouping used for reporting
#    criterion           short label
#    description         what "full points" means
#    points              max points if fully satisfied (0.00-1.00 scale)
#    scoring             "binary" (0 or full points) or "graded" (partial ok)
#    evidence_guidance   what the agent should check to score this item
# ---------------------------------------------------------------------------

RUBRIC: List[Dict[str, Any]] = [

    # -- Legal & Registration existence (0.25) --------------------------------
    {"id": "reg_entity_found", "category": "Legal & Registration",
     "criterion": "Registered legal entity located",
     "description": "A matching entity exists in an official business/company registry.",
     "points": 0.10, "scoring": "binary",
     "evidence_guidance": "Search official registries (Secretary of State, Companies "
                           "House, national commercial register, OpenCorporates) for the "
                           "exact or clearly matching legal name."},

    {"id": "reg_active_status", "category": "Legal & Registration",
     "criterion": "Registration active / in good standing",
     "description": "The registry entry is not dissolved, revoked, or struck off.",
     "points": 0.06, "scoring": "binary",
     "evidence_guidance": "Read the registry status field. Score 0 automatically if "
                           "reg_entity_found is 0."},

    {"id": "reg_tax_id_valid", "category": "Legal & Registration",
     "criterion": "Valid tax / VAT / company ID",
     "description": "A tax ID, VAT number, or company number is published and matches the name.",
     "points": 0.05, "scoring": "binary",
     "evidence_guidance": "Look for an ID in the registry, invoices, or site footer; check "
                           "its format is valid for that country."},

    {"id": "reg_filing_recent", "category": "Legal & Registration",
     "criterion": "Recent filing history",
     "description": "Registry shows filings, renewals, or annual reports in the recent past.",
     "points": 0.04, "scoring": "graded",
     "evidence_guidance": "1.0 for a filing within ~1 year, ~0.5 within 2-3 years, 0.0 if "
                           "none or stale."},

    # -- Digital presence & website quality (0.20) -----------------------------
    {"id": "website_live", "category": "Digital Presence",
     "criterion": "Website is live",
     "description": "The site resolves and loads (not parked, for-sale, or dead).",
     "points": 0.05, "scoring": "binary",
     "evidence_guidance": "Fetch the homepage; fail if it's a parked/placeholder page or "
                           "hard error."},

    {"id": "website_https", "category": "Digital Presence",
     "criterion": "Valid HTTPS",
     "description": "Site is served over HTTPS with a valid certificate.",
     "points": 0.02, "scoring": "binary",
     "evidence_guidance": "Check the URL scheme and certificate validity."},

    {"id": "domain_age", "category": "Digital Presence",
     "criterion": "Domain age",
     "description": "Older domains are harder to fake and correlate with longevity.",
     "points": 0.03, "scoring": "graded",
     "evidence_guidance": "WHOIS lookup; score = min(age_years / 3, 1.0)."},

    {"id": "website_content_depth", "category": "Digital Presence",
     "criterion": "Substantive site content",
     "description": "Specific, non-generic content across About / Services-Products / Contact.",
     "points": 0.05, "scoring": "graded",
     "evidence_guidance": "1.0 for detailed, specific copy across multiple pages; lower "
                           "for thin, vague, or single-page sites."},

    {"id": "website_policies", "category": "Digital Presence",
     "criterion": "Privacy policy / terms present",
     "description": "Standard legal boilerplate most real businesses need for compliance.",
     "points": 0.02, "scoring": "binary",
     "evidence_guidance": "Check the footer/site map for a Privacy Policy and Terms of Service."},

    {"id": "website_functional", "category": "Digital Presence",
     "criterion": "Site is functional",
     "description": "Core pages and navigation work; any forms are wired up correctly.",
     "points": 0.03, "scoring": "binary",
     "evidence_guidance": "Click through main nav links; note broken links or leftover "
                           "template placeholder text."},

    # -- Contact verifiability (0.15) -------------------------------------------
    {"id": "contact_email_domain_match", "category": "Contact Verifiability",
     "criterion": "Company-domain email",
     "description": "Contact email uses the company's own domain, not a free provider.",
     "points": 0.04, "scoring": "binary",
     "evidence_guidance": "Compare the published email domain to the website domain."},

    {"id": "contact_phone_valid", "category": "Contact Verifiability",
     "criterion": "Consistent phone number",
     "description": "A correctly formatted number appears and matches across sources.",
     "points": 0.04, "scoring": "graded",
     "evidence_guidance": "1.0 if the same number appears on the site and one independent "
                           "listing; 0.5 if on one source only; 0 if none."},

    {"id": "contact_address_verifiable", "category": "Contact Verifiability",
     "criterion": "Verifiable physical address",
     "description": "A specific address is given and maps to a real, plausible location.",
     "points": 0.04, "scoring": "graded",
     "evidence_guidance": "1.0 for a full address matching a real building/suite consistent "
                           "with the business; 0.5 for a vague area only; 0 for none/flagged."},

    {"id": "contact_consistency", "category": "Contact Verifiability",
     "criterion": "Cross-source consistency",
     "description": "Name, address, and phone match across website, registry, and directories.",
     "points": 0.03, "scoring": "binary",
     "evidence_guidance": "Compare name/address/phone across at least two independent sources."},

    # -- Online reputation & third-party presence (0.20) -------------------------
    {"id": "linkedin_company_page", "category": "Online Reputation",
     "criterion": "Active company page",
     "description": "A LinkedIn (or regionally relevant) company page with a plausible profile.",
     "points": 0.05, "scoring": "graded",
     "evidence_guidance": "1.0 for an active page with a plausible follower/employee count "
                           "for the claimed size; lower for empty pages."},

    {"id": "linkedin_employees_found", "category": "Online Reputation",
     "criterion": "Real employees findable",
     "description": "Individuals list this company as a current employer.",
     "points": 0.04, "scoring": "graded",
     "evidence_guidance": "0 employees found = 0.0, 1-2 = 0.5, 3+ = 1.0."},

    {"id": "directory_listings", "category": "Online Reputation",
     "criterion": "Independent directory listings",
     "description": "Listed somewhere the company doesn't control, e.g. Google Business "
                     "Profile, Crunchbase, trade directories.",
     "points": 0.04, "scoring": "graded",
     "evidence_guidance": "0/1/2/3+ credible listings -> 0.0/0.4/0.7/1.0."},

    {"id": "press_mentions", "category": "Online Reputation",
     "criterion": "Independent press coverage",
     "description": "Coverage from outlets the company doesn't own or write itself.",
     "points": 0.04, "scoring": "graded",
     "evidence_guidance": "Weight credible outlets over blogs/press-release mills; 0 for none."},

    {"id": "customer_reviews", "category": "Online Reputation",
     "criterion": "Customer reviews exist",
     "description": "A reasonable volume of reviews on Google/Trustpilot/industry sites.",
     "points": 0.03, "scoring": "graded",
     "evidence_guidance": "Score up with more reviews across more platforms, unless they "
                           "look mass-fabricated (identical wording, all 5-star, same-day burst)."},

    # -- Operational activity signals (0.20) --------------------------------------
    {"id": "product_service_clarity", "category": "Operational Activity",
     "criterion": "Clear, plausible offering",
     "description": "What's actually sold/offered is specific and makes business sense.",
     "points": 0.05, "scoring": "graded",
     "evidence_guidance": "Penalize vague, jargon-only copy that never says what the "
                           "company actually does."},

    {"id": "evidence_real_customers", "category": "Operational Activity",
     "criterion": "Evidence of real customers",
     "description": "Named clients, case studies, testimonials, or a visible customer base.",
     "points": 0.05, "scoring": "graded",
     "evidence_guidance": "Verify at least one named client independently if possible; "
                           "generic/unverifiable quotes score lower."},

    {"id": "recent_activity", "category": "Operational Activity",
     "criterion": "Recent activity",
     "description": "Some sign of life in the last several months.",
     "points": 0.05, "scoring": "graded",
     "evidence_guidance": "1.0 for activity within ~3 months, ~0.5 within a year, 0 for "
                           "nothing newer than a year."},

    {"id": "job_postings", "category": "Operational Activity",
     "criterion": "Active hiring",
     "description": "Open roles posted for this company on its site or job boards.",
     "points": 0.03, "scoring": "binary",
     "evidence_guidance": "Check the careers page and major job boards for open roles."},

    {"id": "pricing_availability", "category": "Operational Activity",
     "criterion": "Pricing or quote process exists",
     "description": "A real path to pay or request pricing, implying actual commerce.",
     "points": 0.02, "scoring": "binary",
     "evidence_guidance": "Check for a pricing page, checkout, or quote-request flow."},
]

assert abs(sum(_e["points"] for _e in RUBRIC) - 1.0) < 1e-6, "RUBRIC weights must sum to 1.00"

# ---------------------------------------------------------------------------
# 2. RED FLAGS - deducted from the base score when found (outside the 1.00 budget)
#    id                  unique key used in the results dict
#    criterion           short label
#    description         what triggers this flag
#    penalty             points subtracted if fully triggered (0.00-1.00 scale)
#    evidence_guidance   what the agent should check to score this item
# ---------------------------------------------------------------------------

RED_FLAGS: List[Dict[str, Any]] = [
    {"id": "rf_no_registry_match", "criterion": "No registry match at all",
     "description": "A reasonably thorough registry search finds no matching entity anywhere.",
     "penalty": 0.20,
     "evidence_guidance": "Only trigger after checking the most likely jurisdiction(s), not "
                           "just one registry."},

    {"id": "rf_scam_reports", "criterion": "Scam / fraud reports found",
     "description": "Independent scam-report sites, forums, or complaint boards flag this company.",
     "penalty": 0.25,
     "evidence_guidance": "Search '[company] scam / review / complaint' and check "
                           "consumer-protection or scam-tracker sites."},

    {"id": "rf_very_new_domain", "criterion": "Very new domain, no other footprint",
     "description": "Domain is under ~6 months old and nothing else corroborates the business.",
     "penalty": 0.15,
     "evidence_guidance": "Pair the WHOIS date with an overall lack of registry/social/press results."},

    {"id": "rf_copied_content", "criterion": "Plagiarized or duplicated site content",
     "description": "Website text or design is copied from another real company.",
     "penalty": 0.15,
     "evidence_guidance": "Spot-check distinctive sentences from the site verbatim in search."},

    {"id": "rf_untraceable_contact_only", "criterion": "Only untraceable contact methods",
     "description": "No phone, no verifiable email, only an anonymous form or chat app.",
     "penalty": 0.10,
     "evidence_guidance": "Confirm there is truly no verifiable channel anywhere, including "
                           "in registry filings."},

    {"id": "rf_fake_address", "criterion": "Address doesn't check out",
     "description": "The listed address is nonexistent, vacant, or a flagged mail-drop "
                     "presented as an office.",
     "penalty": 0.10,
     "evidence_guidance": "Check the address on a map/street view against the claimed use."},

    {"id": "rf_unrealistic_promises", "criterion": "Unrealistic guarantees",
     "description": "Guaranteed high returns, get-rich-quick claims, or similar fraud language.",
     "penalty": 0.15,
     "evidence_guidance": "Look for phrasing common to investment or advance-fee fraud."},

    {"id": "rf_no_employees_anywhere", "criterion": "No employees findable anywhere",
     "description": "Not a single real person online lists this company as their employer.",
     "penalty": 0.08,
     "evidence_guidance": "A harder check across all platforms, not just LinkedIn (see "
                           "linkedin_employees_found)."},
]

# Total possible weight per category, derived once from RUBRIC.
CATEGORY_WEIGHTS: Dict[str, float] = {}
for _entry in RUBRIC:
    CATEGORY_WEIGHTS[_entry["category"]] = CATEGORY_WEIGHTS.get(_entry["category"], 0.0) + _entry["points"]


# ---------------------------------------------------------------------------
# 3. SCORING
# ---------------------------------------------------------------------------

def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def total_possible_points() -> float:
    """Sanity check - should equal 1.00."""
    return round(sum(item["points"] for item in RUBRIC), 4)


def blank_results() -> Dict[str, float]:
    """Template dict with every id defaulted to 0.0, for the agent to fill in
    while researching."""
    results = {item["id"]: 0.0 for item in RUBRIC}
    results.update({flag["id"]: 0.0 for flag in RED_FLAGS})
    return results


def interpret_score(score: float) -> str:
    if score >= 0.80:
        return "Likely a legitimate, active business"
    if score >= 0.60:
        return "Probably legitimate; some verification gaps"
    if score >= 0.40:
        return "Uncertain - mixed or thin evidence, manual review recommended"
    if score >= 0.20:
        return "Low confidence - several red flags or major gaps"
    return "Likely not a real/active business, or high fraud risk"


def score_company(results: Dict[str, float]) -> Dict[str, Any]:
    """
    results: dict mapping criterion/red-flag id -> a value in [0.0, 1.0].
             Missing keys are treated as 0.0 ("not verified").

    Returns total score, a category breakdown, and which red flags fired.
    """
    category_earned: Dict[str, float] = {cat: 0.0 for cat in CATEGORY_WEIGHTS}

    base_score = 0.0
    for item in RUBRIC:
        value = _clamp(float(results.get(item["id"], 0.0)))
        earned = value * item["points"]
        base_score += earned
        category_earned[item["category"]] += earned

    triggered_flags = []
    deduction = 0.0
    for flag in RED_FLAGS:
        value = _clamp(float(results.get(flag["id"], 0.0)))
        if value > 0:
            deduction += value * flag["penalty"]
            triggered_flags.append({"id": flag["id"], "criterion": flag["criterion"], "severity": value})

    total_score = _clamp(base_score - deduction)

    return {
        "total_score": round(total_score, 4),
        "verdict": interpret_score(total_score),
        "base_score_before_flags": round(base_score, 4),
        "total_deduction": round(deduction, 4),
        "category_breakdown": {
            cat: {
                "earned": round(category_earned[cat], 4),
                "possible": round(CATEGORY_WEIGHTS[cat], 4),
                "pct_of_category": (round(category_earned[cat] / CATEGORY_WEIGHTS[cat], 4)
                                     if CATEGORY_WEIGHTS[cat] else None),
            }
            for cat in CATEGORY_WEIGHTS
        },
        "triggered_red_flags": triggered_flags,
    }


# ---------------------------------------------------------------------------
# 4. Render the rubric as instructions for an LLM agent's research prompt
# ---------------------------------------------------------------------------

def rubric_as_prompt() -> str:
    lines = [
        "Evaluate the company against each item below using your web tool.",
        "For each id, output a score from 0.0 to 1.0 (use 0 or 1 for binary items).",
        "",
        "POSITIVE CRITERIA (max 1.00 total):",
    ]
    for item in RUBRIC:
        lines.append(f"- [{item['id']}] ({item['points']:.2f} pts, {item['scoring']}) "
                      f"{item['criterion']}: {item['evidence_guidance']}")
    lines.append("")
    lines.append("RED FLAGS (deducted if found):")
    for flag in RED_FLAGS:
        lines.append(f"- [{flag['id']}] (-{flag['penalty']:.2f} pts) "
                      f"{flag['criterion']}: {flag['evidence_guidance']}")
    return "\n".join(lines)


if __name__ == "__main__":
    import json

    print("Total possible points:", total_possible_points())
    print("Category weights:", CATEGORY_WEIGHTS)
    print()

    # Example: a plausible small-but-real local business
    example = blank_results()
    example.update({
        "reg_entity_found": 1.0, "reg_active_status": 1.0,
        "reg_tax_id_valid": 1.0, "reg_filing_recent": 1.0,
        "website_live": 1.0, "website_https": 1.0, "domain_age": 0.7,
        "website_content_depth": 0.8, "website_policies": 1.0, "website_functional": 1.0,
        "contact_email_domain_match": 1.0, "contact_phone_valid": 1.0,
        "contact_address_verifiable": 1.0, "contact_consistency": 1.0,
        "linkedin_company_page": 0.6, "linkedin_employees_found": 0.5,
        "directory_listings": 0.7, "press_mentions": 0.0, "customer_reviews": 0.6,
        "product_service_clarity": 1.0, "evidence_real_customers": 0.6,
        "recent_activity": 0.8, "job_postings": 0.0, "pricing_availability": 1.0,
    })

    result = score_company(example)
    print(json.dumps(result, indent=2))
