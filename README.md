# CaseCast

Synthetic patient vignettes for AI ground-truth labeling and medical education — no real patients required.

## The Problem

Building medical AI requires one thing above all else: high-quality, realistic patient data. But getting it is another matter.

Real patient data is expensive to license, kept behind health system walls, in need of standardization, and riddled with gaps. More 
fundamentally, it carries HIPAA and privacy obligations that create risk for developers even when data is properly de-identified.

The result: AI teams spend more time wrangling data than building models and often have to settle for incomplete datasets.

CaseCast sidesteps all of this. It generates synthetic patient vignettes with realistic histories of present illness, symptoms, lab values, and medications.

The cases CaseCast produces are designed for two audiences:

**AI developers** can use them as a structured substrate for ground-truth labeling. Esepcially for models seeking to augment clinical judgment, expert annotations can target the grey areas: triage decision, differential diagnoses, and medication selection. These are the places where clinical expertise matters and discrete data are not usually available.

**Medical educators** can use them to give students varied, refreshed, and realistic clinical scenarios for diagnosis and treatment decisions. These cases can be tailored by specialty and complexity.

## The Solution

### What CaseCast Generates
Each vignette is a structured clinical case that can include:
- Patient demographics: age, sex, relevant social, family, and travel history
- Chief complaint: the reason for the visit in the patient's own words
- History of present illness (HPI): a detailed, realistic narrative of symptom onset and progression
- Review of systems: relevant positives and negatives
- Physical exam findings: vital signs and examination results
- Lab values and imaging: results consistent with the clinical picture
- Medications and allergies: current medication lists with realistic details
- Clinical context: ED, inpatient, outpatient, ICU, and other care settings

Cases can be generated across specialties, difficulty levels, and degrees of diagnostic ambiguity — including deliberately complex or atypical presentations.

## Demo

[Coming Soon] A web-based tool where the user can choose conditions and severity for K number of cases.


## What I Learned

1. This is my first Git. It's both easier and harder than I expected. Set up is quite easy. I'm worried that I'm doing something wrong still!
2. This idea has been rattling around my head for years. Putting it down in words is forcing me to consider the details deeper than I had before. This is the exciting stuff of new products

## Next Steps

- Research [Synthetic Mass](https://synthea.mitre.org/?ck_subscriber_id=2438996986&utm_source=convertkit&utm_medium=email&utm_campaign=cool%20open%20source%20healthcare%20projects%20-%2021021367&sh_kit=c17fb063fed6efb2f12f03184637bf5f906072fb98dbbe4a4132881b274410f4)
- Decide on a validation approach

## Built With
Claude

---
Built by Jimish Mehta | [LinkedIn](https://www.linkedin.com/in/jimishmehta/)  # casecast
