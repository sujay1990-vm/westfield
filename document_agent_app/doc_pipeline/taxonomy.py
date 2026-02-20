# doc_pipeline/taxonomy.py

# ----------------------------
# Damage Types (taxonomy)
# ----------------------------
DAMAGE_TYPES = [
    "Compensatory Damages",
    "Punitive Damages",
    "Treble Damages",
    "Attorneys’ Fees Demand",
    "Emotional Distress Damages",
    "Loss of Future Earnings",
    "Regulatory Penalties",
]

DAMAGE_TYPES_TAXONOMY = {
    "Compensatory Damages": {
        "definition": (
            "Economic and non-economic damages intended to compensate for actual losses "
            "(medical expenses, lost wages, pain and suffering, etc.)."
        ),
        "core_phrases": ["compensatory damages", "actual damages"],
        "expanded_keywords": [
            "economic loss", "special damages", "general damages", "restitution",
            "back pay", "medical expenses", "indemnity", "out-of-pocket"
        ],
        "high_severity_indicators": ["plaintiff seeks", "demand includes", "claims for losses"],
    },
    "Punitive Damages": {
        "definition": (
            "Damages intended to punish and deter misconduct; typically requires willful, malicious, "
            "reckless, or intentional wrongdoing."
        ),
        "core_phrases": ["punitive damages", "exemplary damages"],
        "expanded_keywords": [
            "willful misconduct", "gross negligence", "reckless disregard",
            "malicious conduct", "intentional wrongdoing", "conscious disregard"
        ],
        "high_severity_indicators": ["prayer for punitive relief", "bad faith", "intentional violation"],
    },
    "Treble Damages": {
        "definition": (
            "Statutory damages multiplier (typically 3x) under specific laws (consumer fraud, RICO, "
            "unfair/deceptive trade practices)."
        ),
        "core_phrases": ["treble damages", "triple damages"],
        "expanded_keywords": [
            "3x damages", "statutory multiplier", "RICO damages",
            "unfair trade practices act", "consumer fraud statute"
        ],
        "high_severity_indicators": [
            "pursuant to statute", "statutory damages multiplier", "consumer fraud statute"
        ],
    },
    "Attorneys’ Fees Demand": {
        "definition": (
            "Demand for recovery of attorneys’ fees and litigation costs (fee-shifting, prevailing party, "
            "statutory entitlement)."
        ),
        "core_phrases": ["attorneys’ fees", "attorney fees", "legal fees"],
        "expanded_keywords": [
            "costs of suit", "fee petition", "fee shifting", "prevailing party fees",
            "litigation costs", "defense costs recovery"
        ],
        "high_severity_indicators": ["entitled to fees under statute", "statutory right to recover fees"],
    },
    "Emotional Distress Damages": {
        "definition": (
            "Damages for emotional/psychological harm (mental anguish, humiliation, anxiety, PTSD), "
            "often supported by therapy/counseling/psychiatric care."
        ),
        "core_phrases": ["emotional distress", "mental anguish"],
        "expanded_keywords": [
            "pain and suffering", "humiliation", "embarrassment", "anxiety", "depression",
            "psychological harm", "PTSD"
        ],
        "high_severity_indicators": ["therapy", "counseling", "psychiatric treatment", "stress leave"],
    },
    "Loss of Future Earnings": {
        "definition": (
            "Claim for loss of earning capacity or future income (front pay, projected earnings, diminished capacity), "
            "often tied to disability, termination, or inability to return to work."
        ),
        "core_phrases": ["loss of earning capacity", "future lost wages"],
        "expanded_keywords": [
            "front pay", "future income loss", "projected earnings",
            "diminished earning capacity", "career damage"
        ],
        "high_severity_indicators": ["employment termination", "wrongful discharge", "disability claim"],
    },
    "Regulatory Penalties": {
        "definition": (
            "Civil/administrative penalties or fines arising from regulatory enforcement (DOJ/SEC/EEOC/HIPAA/CMS etc.)."
        ),
        "core_phrases": ["civil penalty", "regulatory fine"],
        "expanded_keywords": [
            "administrative penalty", "enforcement action", "consent decree",
            "sanctions", "violation notice"
        ],
        "high_severity_indicators": ["SEC investigation", "DOJ inquiry", "EEOC charge", "HIPAA violation", "CMS penalty"],
    },
}

# Retrieval hint for damage-type detection
DAMAGE_TYPES_QUERY = (
    "damages compensatory actual punitive exemplary treble statutory multiplier "
    "attorneys fees fee shifting emotional distress mental anguish PTSD "
    "loss of earning capacity future lost wages regulatory fine civil penalty consent decree"
)

# ----------------------------
# Language Intensity (taxonomy)
# ----------------------------
LANGUAGE_INTENSITY_TERMS = [
    "willful",
    "reckless",
    "malicious",
    "systemic failure",
    "pattern and practice",
]

LANGUAGE_INTENSITY_TAXONOMY = {
    "Willful": {
        "definition": "Intentional or knowing misconduct; conscious disregard / deliberate act.",
        "core_phrases": ["willful", "wilful"],
        "expanded_variants": ["intentional", "knowingly", "deliberate", "conscious disregard", "purposeful"],
        "common_patterns": [
            "willful violation", "knowingly concealed", "intentional misconduct", "deliberately ignored"
        ],
    },
    "Reckless": {
        "definition": "Heedless or wanton disregard; gross negligence / conscious indifference.",
        "core_phrases": ["reckless", "recklessness"],
        "expanded_variants": ["gross negligence", "wanton", "heedless", "indifference", "conscious indifference"],
        "common_patterns": [
            "reckless disregard for", "grossly negligent", "wanton conduct", "utter indifference"
        ],
    },
    "Malicious": {
        "definition": "Bad faith / spiteful or oppressive conduct; sometimes tied to fraudulent intent.",
        "core_phrases": ["malicious", "malice"],
        "expanded_variants": ["bad faith", "spiteful", "vindictive", "fraudulent intent", "oppressive"],
        "common_patterns": [
            "malicious intent", "acted in bad faith", "oppressive conduct", "fraudulent scheme"
        ],
    },
    "Systemic failure": {
        "definition": "Organization-wide control/governance breakdown; failure of oversight/internal controls.",
        "core_phrases": ["systemic failure", "systemic issues"],
        "expanded_variants": [
            "breakdown in controls", "governance failure", "enterprise-wide", "control failure",
            "compliance failure", "lack of oversight"
        ],
        "common_patterns": [
            "failure of internal controls", "organizational failure", "control environment was deficient"
        ],
    },
    "Pattern and practice": {
        "definition": "Repeated or routine misconduct; not an isolated incident; widespread practice.",
        "core_phrases": ["pattern and practice"],
        "expanded_variants": ["repeated conduct", "ongoing violations", "widespread", "routine practice", "common scheme"],
        "common_patterns": [
            "pattern of behavior", "repeated violations", "not an isolated incident", "company practice"
        ],
    },
}

LANGUAGE_INTENSITY_RUBRIC = """
Score language intensity 0–4 based on the document’s accusatory posture:

0 = Neutral/factual, no pressure or blame framing
1 = Firm demand posture (trial readiness, deadlines) without inflammatory terms
2 = Accusatory negligence framing, stronger blame/indifference language
3 = Inflammatory terms like willful/reckless/malicious/conscious disregard
4 = Nuclear framing: systemic failure, pattern and practice, corporate culture, repeated misconduct, regulatory threats

Return score + the exact phrases used as evidence with page number.
"""

LANGUAGE_INTENSITY_QUERY = (
    "willful wilful intentional knowingly deliberate conscious disregard "
    "reckless recklessness gross negligence wanton heedless indifference "
    "malicious malice bad faith oppressive fraudulent scheme "
    "systemic failure internal controls governance failure compliance failure "
    "pattern and practice repeated violations not an isolated incident"
)

# ----------------------------
# Generic Signals (v1 packs)
# ----------------------------
SIGNALS_V1 = {
    "Witness": {
        "type": "categorical_multi",
        "definition": "Detect whether witnesses are mentioned and whether testimony strengthens or weakens the defense.",
        "categories": [
            "General Witness Mention",
            "Favorable to Insured",
            "Adverse to Insured",
            "No Witness",
            "Multiple Witnesses",
            "Expert Witness",
            "Conflicting Testimony",
            "Written Documentation",
            "Hostile Witness",
            "Credibility Issue",
            "Internal Employee Witness",
            "Board Member",
            "Medical Staff (MPL)",
            "IT Staff (Cyber)",
        ],
        "keywords": {
            "General Witness Mention": ["witness", "eyewitness", "testified", "testimony", "statement", "affidavit", "deposition"],
            "Favorable to Insured": ["corroborates insured", "supports defense", "contradicts claimant", "refutes allegation"],
            "Adverse to Insured": ["corroborates claimant", "confirms allegation", "damaging testimony", "adverse statement"],
            "No Witness": ["no independent witness", "no corroboration", "unsubstantiated"],
            "Multiple Witnesses": ["multiple witnesses", "several witnesses", "several employees observed"],
            "Expert Witness": ["expert retained", "forensic expert", "independent expert opinion", "expert report"],
            "Conflicting Testimony": ["inconsistent statements", "contradictory accounts", "conflicting testimony"],
            "Written Documentation": ["signed statement", "recorded statement", "written statement"],
            "Hostile Witness": ["unwilling witness", "non-cooperative", "hostile witness"],
            "Credibility Issue": ["memory lapse", "biased", "credibility questioned", "credibility issue"],
            "Internal Employee Witness": ["compliance officer stated", "hr confirmed", "underwriter testified"],
            "Board Member": ["board minutes reflect", "director testified", "board minutes"],
            "Medical Staff (MPL)": ["nurse noted", "attending physician testified", "medical staff"],
            "IT Staff (Cyber)": ["it manager confirmed", "breach timeline", "security team confirmed"],
        },
        "interpretation": {
            "General Witness Mention": "Witness exists",
            "Favorable to Insured": "Strengthens defense",
            "Adverse to Insured": "Weakens defense",
            "No Witness": "He-said/she-said",
            "Multiple Witnesses": "Strong evidence environment",
            "Expert Witness": "Litigation phase / expert-driven",
            "Conflicting Testimony": "Fact dispute",
            "Written Documentation": "Evidence strength",
            "Hostile Witness": "Defense risk",
            "Credibility Issue": "Weak witness",
            "Internal Employee Witness": "Organizational risk",
            "Board Member": "Governance exposure",
            "Medical Staff (MPL)": "Standard of care issue",
            "IT Staff (Cyber)": "Coverage trigger",
        },
        "query": "witness eyewitness testified affidavit deposition expert inconsistent contradictory hostile credibility board minutes nurse physician IT manager breach timeline",
    },

    "Liability Clarity": {
        "type": "single_choice",
        "definition": "How clear liability is based on the narrative posture in the document.",
        "categories": [
            "Clear Liability",
            "Shared/Comparative Fault Alleged",
            "Disputed Liability",
            "No Liability Facts",
        ],
        "keywords": {
            "Clear Liability": ["rear-end", "stopped", "admitted", "cited", "police report confirms"],
            "Shared/Comparative Fault Alleged": ["comparative negligence", "contributory", "failed to yield", "sudden stop"],
            "Disputed Liability": ["disputes", "denies", "unclear", "conflicting accounts", "no independent evidence"],
            "No Liability Facts": ["insufficient facts", "unknown", "not established"],
        },
        "interpretation": {
            "Clear Liability": "Plaintiff leverage higher",
            "Shared/Comparative Fault Alleged": "Allocation risk reduces exposure",
            "Disputed Liability": "Investigation needed; litigation risk higher",
            "No Liability Facts": "Cannot evaluate liability from doc",
        },
        "query": "liability fault admitted cited police report rear-end comparative negligence contributory denies disputed conflicting accounts",
    },

    "Causation Weakness": {
        "type": "categorical_multi",
        "definition": "Defense-friendly causation vulnerabilities (pre-existing, treatment gaps, alternative cause, low impact).",
        "categories": [
            "Strong Causation",
            "Pre-existing Condition Emphasized",
            "Gap in Treatment",
            "Alternative Cause Alleged",
            "Low-Impact / MIST Setup",
        ],
        "keywords": {
            "Strong Causation": ["causally related", "reasonable medical probability", "direct result of"],
            "Pre-existing Condition Emphasized": ["pre-existing", "degenerative", "prior injury", "history of"],
            "Gap in Treatment": ["gap in care", "delayed treatment", "stopped treatment", "no treatment for"],
            "Alternative Cause Alleged": ["unrelated", "subsequent incident", "intervening cause"],
            "Low-Impact / MIST Setup": ["minor impact", "low speed", "minimal damage", "no airbags"],
        },
        "interpretation": {
            "Strong Causation": "Weakens defense on causation",
            "Pre-existing Condition Emphasized": "Strengthens defense causation argument",
            "Gap in Treatment": "Strengthens defense causation argument",
            "Alternative Cause Alleged": "Strengthens defense causation argument",
            "Low-Impact / MIST Setup": "Strengthens defense valuation/causation argument",
        },
        "query": "causally related reasonable medical probability pre-existing degenerative prior injury gap in treatment delayed treatment intervening cause minor impact low speed minimal damage",
    },

    "Treatment Severity": {
        "type": "single_choice",
        "definition": "Medical treatment intensity as a proxy for exposure severity.",
        "categories": [
            "Conservative Only",
            "Injections / Pain Management",
            "Surgery Performed",
            "Surgery Recommended",
            "Permanent Impairment Claimed",
        ],
        "keywords": {
            "Conservative Only": ["physical therapy", "PT", "chiropractic", "NSAIDs", "home exercise"],
            "Injections / Pain Management": ["epidural", "facet", "RFA", "injection", "pain management"],
            "Surgery Performed": ["ACDF", "fusion", "arthroscopy", "ORIF", "surgery performed", "underwent surgery"],
            "Surgery Recommended": ["recommend surgery", "candidate for surgery", "surgery recommended"],
            "Permanent Impairment Claimed": ["permanent", "MMI", "impairment rating", "permanent restrictions"],
        },
        "interpretation": {
            "Conservative Only": "Lower exposure baseline",
            "Injections / Pain Management": "Moderate exposure",
            "Surgery Performed": "High exposure",
            "Surgery Recommended": "Elevated exposure risk",
            "Permanent Impairment Claimed": "High exposure and future costs",
        },
        "query": "physical therapy chiropractic epidural injection pain management ACDF fusion surgery underwent recommend surgery impairment rating MMI permanent",
    },

    "Demand Posture": {
        "type": "single_choice",
        "definition": "How aggressive the plaintiff demand posture is (limits, deadlines, threats).",
        "categories": [
            "Policy Limits Demand",
            "Time-Limited Demand",
            "Anchoring High / Aggressive",
            "Inviting Negotiation",
            "Threat of Immediate Suit",
        ],
        "keywords": {
            "Policy Limits Demand": ["tender policy limits", "limits demand", "policy limits"],
            "Time-Limited Demand": ["time-limited", "must respond by", "deadline", "within ten days", "within 10 days"],
            "Anchoring High / Aggressive": ["excess exposure", "nuclear verdict", "will not negotiate below"],
            "Inviting Negotiation": ["open to discussion", "reasonable resolution", "willing to negotiate"],
            "Threat of Immediate Suit": ["file suit", "prepared to litigate", "we will file", "commence litigation"],
        },
        "interpretation": {
            "Policy Limits Demand": "Higher escalation / bad faith trap potential",
            "Time-Limited Demand": "Higher escalation / compliance risk",
            "Anchoring High / Aggressive": "High negotiation friction",
            "Inviting Negotiation": "Lower friction; likely settle path",
            "Threat of Immediate Suit": "Litigation imminent",
        },
        "query": "policy limits tender time-limited deadline must respond by prepared to litigate file suit commence litigation excess exposure nuclear verdict",
    },

    "Bad Faith Setup": {
        "type": "categorical_multi",
        "definition": "Indicators the letter is building extra-contractual exposure (delay/failure to investigate/settle).",
        "categories": [
            "Explicit Bad Faith Allegation",
            "Failure to Settle Alleged",
            "Unfair Claims Practices Threat",
            "Regulatory Complaint Threat",
        ],
        "keywords": {
            "Explicit Bad Faith Allegation": ["bad faith", "unreasonable delay", "failure to investigate"],
            "Failure to Settle Alleged": ["failed to settle", "refused to tender", "opportunity to settle within limits"],
            "Unfair Claims Practices Threat": ["unfair claims settlement practices", "statutory violations"],
            "Regulatory Complaint Threat": ["DOI complaint", "department of insurance", "regulatory complaint"],
        },
        "interpretation": {
            "Explicit Bad Faith Allegation": "Elevated extra-contractual exposure",
            "Failure to Settle Alleged": "Elevated extra-contractual exposure",
            "Unfair Claims Practices Threat": "Elevated compliance risk",
            "Regulatory Complaint Threat": "Regulatory escalation risk",
        },
        "query": "bad faith failure to investigate unreasonable delay failed to settle refused to tender unfair claims settlement practices statutory violations department of insurance DOI complaint",
    },

    "Documentation Strength": {
        "type": "categorical_multi",
        "definition": "Strength of objective documentation (reports, video, records, affidavits).",
        "categories": [
            "Police/Official Report Cited",
            "Video Evidence Exists",
            "Medical Records/Bills Provided",
            "Written Statements/Affidavits",
            "Sparse Documentation",
        ],
        "keywords": {
            "Police/Official Report Cited": ["police report", "incident report", "crash report", "body cam"],
            "Video Evidence Exists": ["video footage", "CCTV", "dashcam", "surveillance video"],
            "Medical Records/Bills Provided": ["records enclosed", "medical records", "billing statements", "operative report"],
            "Written Statements/Affidavits": ["affidavit", "signed statement", "recorded statement"],
            "Sparse Documentation": ["not provided", "no documentation", "insufficient documentation"],
        },
        "interpretation": {
            "Police/Official Report Cited": "Objective liability support",
            "Video Evidence Exists": "Strong objective evidence",
            "Medical Records/Bills Provided": "Supports valuation",
            "Written Statements/Affidavits": "Strengthens proof",
            "Sparse Documentation": "Increases dispute / investigation need",
        },
        "query": "police report incident report crash report CCTV dashcam surveillance video medical records billing statements operative report affidavit signed statement no documentation not provided",
    },
}
