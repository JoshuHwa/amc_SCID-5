"""DSM-5 diagnostic categories and their ICD-10-CM chapter mapping.

Module J is only reached after the interviewer has ruled out the other DSM-5
categories, so the screening step needs a closed vocabulary to answer with.
Using slugs rather than free text is what makes the screening result
machine-checkable.
"""

DSM5_CATEGORIES: dict[str, str] = {
    "schizophrenia_spectrum": "Schizophrenia Spectrum and Other Psychotic Disorders",
    "neurodevelopmental": "Neurodevelopmental Disorders",
    "bipolar_and_related": "Bipolar and Related Disorders",
    "depressive": "Depressive Disorders",
    "anxiety": "Anxiety Disorders",
    "obsessive_compulsive": "Obsessive-Compulsive and Related Disorders",
    "trauma_and_stressor_related": "Trauma- and Stressor-Related Disorders",
    "dissociative": "Dissociative Disorders",
    "somatic_symptom": "Somatic Symptom and Related Disorders",
    "feeding_and_eating": "Feeding and Eating Disorders",
    "elimination": "Elimination Disorders",
    "sleep_wake": "Sleep-Wake Disorders",
    "sexual_dysfunction": "Sexual Dysfunctions",
    "gender_dysphoria": "Gender Dysphoria",
    "disruptive_impulse_control_conduct": "Disruptive, Impulse-Control, and Conduct Disorders",
    "substance_related_and_addictive": "Substance-Related and Addictive Disorders",
    "neurocognitive": "Neurocognitive Disorders",
    "personality": "Personality Disorders",
    "paraphilic": "Paraphilic Disorders",
    "other_mental_disorders": "Other Mental Disorders",
}

# Adjustment disorder sits in the trauma- and stressor-related chapter; every
# other DSM-5 category above is also an F-chapter condition in ICD-10-CM. The
# non-psychiatric chapters are kept because differential diagnosis routinely
# ends outside psychiatry (e.g. a neurological cause).
ICD10_CHAPTERS: dict[str, str] = {
    "mental_behavioural_neurodevelopmental": "F01-F99",
    "nervous_system": "G00-G99",
    "circulatory_system": "I00-I99",
    "endocrine_nutritional_metabolic": "E00-E89",
}

# ICD-10-CM codes for adjustment disorder by DSM-5 specifier.
ADJUSTMENT_DISORDER_CODES: dict[str, str] = {
    "with_depressed_mood": "F43.21",
    "with_anxiety": "F43.22",
    "with_mixed_anxiety_and_depressed_mood": "F43.23",
    "with_disturbance_of_conduct": "F43.24",
    "with_mixed_disturbance_of_emotions_and_conduct": "F43.25",
    "unspecified": "F43.20",
}


def icd10_for_specifier(specifier: str) -> str:
    """Return the ICD-10-CM code for an adjustment disorder specifier."""
    return ADJUSTMENT_DISORDER_CODES.get(specifier, ADJUSTMENT_DISORDER_CODES["unspecified"])


def icd10_chapter_for_category(category: str) -> str:
    """Return the ICD-10-CM chapter range for a screened-out DSM-5 category."""
    if category in DSM5_CATEGORIES:
        return ICD10_CHAPTERS["mental_behavioural_neurodevelopmental"]
    return "unmapped"
