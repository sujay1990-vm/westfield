DAMAGE_TYPES = [
    "Compensatory Damages",
    "Punitive Damages",
    "Treble Damages",
    "Attorneys’ Fees Demand",
    "Emotional Distress Damages",
    "Loss of Future Earnings",
    "Regulatory Penalties",
]

LANGUAGE_INTENSITY_TERMS = [
    "willful",
    "reckless",
    "malicious",
    "systemic failure",
    "pattern and practice",
]

LANGUAGE_INTENSITY_RUBRIC = """
Score language intensity 0–4 based on the document’s accusatory posture:

0 = Neutral/factual, no pressure or blame framing
1 = Firm demand posture (trial readiness, deadlines) without inflammatory terms
2 = Accusatory negligence framing, stronger blame/indifference language
3 = Inflammatory terms like willful/reckless/malicious/conscious disregard
4 = Nuclear framing: systemic failure, pattern and practice, corporate culture, repeated misconduct, regulatory threats

Return score + the exact phrases used as evidence with page number.
"""
