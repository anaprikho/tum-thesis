import pandas as pd

from config import KEYWORDS_FILE

# total number of categories: 26
categories = [
    # Mental Health - 6
    "Mental Health",
    "Depression",
    "Anxiety",
    "ADHD",
    "Bipolar Disorder",
    "Eating Disorder",

    # Physical Health - 8
    "Diabetes",
    "Arthritis",
    "Hypertension",
    "Chronic Pain",
    "Autoimmune Disorder",
    "Nutrition and Wellness",
    "Sleep Disorder",
    "Neurological Disorder",

    # Women's Health - 4
    "Women's Health",
    "Menopause",
    "PCOS",
    "Ovarian Health",

    # Substance Abuse - 4
    "Alcohol Addiction",
    "Opioid Addiction",
    "Cocaine Dependency",
    "Nicotine Addiction",

    # Terminal Conditions - 4
    "Cancer",
    "ALS",
    "Dementia",
    "HIV"
]

# Define keywords and categories
keywords_mental_health= [
    # Mental Health
    ("mental wellbeing", "Mental Health"),
    ("psychological health", "Mental Health"),
    ("mental wellness", "Mental Health"),
    ("mental illness", "Mental Health"),
    ("mental health awareness", "Mental Health"),
    ("mental resilience", "Mental Health"),
    ("emotional wellbeing", "Mental Health"),
    ("behavioral health", "Mental Health"),
    ("therapy", "Mental Health"),
    ("self-care", "Mental Health"),
    ("counseling", "Mental Health"),
    ("mindfulness", "Mental Health"),
    ("mental disorder", "Mental Health"),
    ("spiritual health", "Mental Health"),
    
    # Depression
    ("sadness", "Depression"),
    ("melancholy", "Depression"),
    ("hopelessness", "Depression"),
    ("fatigue", "Depression"),
    ("isolation", "Depression"),
    ("loneliness", "Depression"),
    ("self-worth", "Depression"),
    ("antidepressants", "Depression"),
    ("psychotherapy", "Depression"),
    ("dysthymia", "Depression"),
    ("suicidal thoughts", "Depression"),
    ("mood disorders", "Depression"),
    ("behavioral therapy", "Depression"),
    ("seasonal affective disorder (SAD)", "Depression"),
    ("major depressive disorder (MDD)", "Depression"),
    ("rumination", "Depression"),

    # Anxiety
    ("generalized anxiety disorder (GAD)", "Anxiety"),
    ("phobias", "Anxiety"),
    ("worry", "Anxiety"),
    ("panic attacks", "Anxiety"),
    ("nervousness", "Anxiety"),
    ("stress", "Anxiety"),
    ("social anxiety", "Anxiety"),
    ("hypervigilance", "Anxiety"),
    ("relaxation techniques", "Anxiety"),
    ("CBT (Cognitive Behavioral Therapy)", "Anxiety"),
    ("exposure therapy", "Anxiety"),
    ("OCD (Obsessive-Compulsive Disorder)", "Anxiety"),
    ("performance anxiety", "Anxiety"),
    ("intrusive thoughts", "Anxiety"),

    # ADHD (Attention Deficit Hyperactivity Disorder)
    ("hyperactivity", "ADHD"),
    ("impulsivity", "ADHD"),
    ("inattention", "ADHD"),
    ("executive dysfunction", "ADHD"),
    ("focus", "ADHD"),
    ("time management", "ADHD"),
    ("disorganization", "ADHD"),
    ("concentration", "ADHD"),
    ("attention span", "ADHD"),
    ("procrastination", "ADHD"),
    ("ADHD medication", "ADHD"),
    ("stimulants", "ADHD"),
    ("non-stimulants", "ADHD"),

    # Bipolar Disorder
    ("mania", "Bipolar disorder"),
    ("hypomania", "Bipolar disorder"),
    ("mood swings", "Bipolar disorder"),
    ("depression", "Bipolar disorder"),
    ("mixed episodes", "Bipolar disorder"),
    ("lithium", "Bipolar disorder"),
    ("rapid cycling", "Bipolar disorder"),
    ("psychosis", "Bipolar disorder"),
    ("mood stabilizers", "Bipolar disorder"),
    ("emotional regulation", "Bipolar disorder"),
    ("bipolar I", "Bipolar disorder"),
    ("bipolar II", "Bipolar disorder"),
    ("cyclothymia", "Bipolar disorder"),

    # Eating Disorder
    ("anorexia", "Eating Disorder"),
    ("bulimia", "Eating Disorder"),
    ("binge eating disorder", "Eating Disorder"),
    ("disordered eating", "Eating Disorder"),
    ("body image", "Eating Disorder"),
    ("orthorexia", "Eating Disorder"),
    ("ARFID (Avoidant Restrictive Food Intake Disorder)", "Eating Disorder"),
    ("compulsive overeating", "Eating Disorder"),
    ("weight preoccupation", "Eating Disorder"),
    ("restrictive eating", "Eating Disorder")
]

keywords_physical_health = [
    # Diabetes
    ("insulin resistance", "Diabetes"),
    ("blood sugar", "Diabetes"),
    ("type 1 diabetes", "Diabetes"),
    ("type 2 diabetes", "Diabetes"),
    ("gestational diabetes", "Diabetes"),
    ("diabetic neuropathy", "Diabetes"),
    ("hyperglycemia", "Diabetes"),
    ("hypoglycemia", "Diabetes"),
    ("prediabetes", "Diabetes"),
    ("diabetic retinopathy", "Diabetes"),
    ("continuous glucose monitoring (CGM)", "Diabetes"),
    ("insulin pump", "Diabetes"),
    ("ketoacidosis", "Diabetes"),

    # Arthritis
    ("rheumatoid arthritis", "Arthritis"),
    ("osteoarthritis", "Arthritis"),
    ("joint pain", "Arthritis"),
    ("inflammation", "Arthritis"),
    ("autoimmune disease", "Arthritis"),
    ("gout", "Arthritis"),
    ("psoriatic arthritis", "Arthritis"),
    ("cartilage", "Arthritis"),
    ("ankylosing spondylitis", "Arthritis"),
    ("fibromyalgia", "Arthritis"),
    ("joint stiffness", "Arthritis"),
    ("anti-inflammatory medications", "Arthritis"),
    
    # Hypertension (High Blood Pressure)
    ("systolic pressure", "Hypertension"),
    ("diastolic pressure", "Hypertension"),
    ("hypertensive crisis", "Hypertension"),
    ("cardiovascular disease", "Hypertension"),
    ("stroke", "Hypertension"),
    ("sodium intake", "Hypertension"),
    ("atherosclerosis", "Hypertension"),
    ("hypertension treatment", "Hypertension"),
    ("heart health", "Hypertension"),

    # Chronic Pain
    ("neuropathic pain", "Chronic pain"),
    ("fibromyalgia", "Chronic pain"),
    ("pain management", "Chronic pain"),
    ("nerve pain", "Chronic pain"),
    ("opioids", "Chronic pain"),
    ("inflammatory pain", "Chronic pain"),
    ("musculoskeletal pain", "Chronic pain"),
    ("phantom limb pain", "Chronic pain"),
    ("pain flare-ups", "Chronic pain"),
    ("pain threshold", "Chronic pain"),
    ("nerve blocks", "Chronic pain"),
    ("physical therapy", "Chronic pain"),

    # Autoimmune Disorder
    ("lupus", "Autoimmune disorder"),
    ("multiple sclerosis (MS)", "Autoimmune disorder"),
    ("Crohn’s disease", "Autoimmune disorder"),
    ("Hashimoto’s thyroiditis", "Autoimmune disorder"),
    ("celiac disease", "Autoimmune disorder"),
    ("psoriasis", "Autoimmune disorder"),
    ("Sjogren’s syndrome", "Autoimmune disorder"),
    ("inflammation", "Autoimmune disorder"),
    ("autoimmune flares", "Autoimmune disorder"),
    ("chronic immune response", "Autoimmune disorder"),

    # Nutrition and Wellness
    ("healthy eating", "Nutrition and Wellness"),
    ("weight management", "Nutrition and Wellness"),
    ("nutrition deficiencies", "Nutrition and Wellness"),
    ("supplements", "Nutrition and Wellness"),
    ("vegan diet", "Nutrition and Wellness"),
    ("keto diet", "Nutrition and Wellness"),
    ("intermittent fasting", "Nutrition and Wellness"),
    ("balanced diet", "Nutrition and Wellness"),
    ("gut health", "Nutrition and Wellness"),
    ("hydration", "Nutrition and Wellness"),
    ("anti-inflammatory diet", "Nutrition and Wellness"),
    ("plant-based eating", "Nutrition and Wellness"),

    # Sleep Disorder
    ("insomnia", "Sleep disorder"),
    ("sleep apnea", "Sleep disorder"),
    ("restless leg syndrome (RLS)", "Sleep disorder"),
    ("narcolepsy", "Sleep disorder"),
    ("circadian rhythm disorders", "Sleep disorder"),
    ("parasomnia", "Sleep disorder"),
    ("hypersomnia", "Sleep disorder"),
    ("CPAP therapy", "Sleep disorder"),
    ("sleep hygiene", "Sleep disorder"),
    ("melatonin", "Sleep disorder"),
    ("leg cramps", "Sleep disorder"),
    ("urge to move legs", "Sleep disorder"),
    ("sleep disturbance", "Sleep disorder"),
    ("deep sleep", "Sleep disorder"),
    ("REM sleep", "Sleep disorder"),
    ("snoring", "Sleep disorder"),

    # Neurological Disorder
    ("epilepsy", "Neurological disorder"),
    ("Parkinson’s disease", "Neurological disorder"),
    ("migraines", "Neurological disorder"),
    ("traumatic brain injury (TBI)", "Neurological disorder"),
    ("multiple sclerosis", "Neurological disorder"),
    ("seizures", "Neurological disorder"),
    ("neuralgia", "Neurological disorder"),
    ("neuroinflammation", "Neurological disorder")
]

keywords_women_health = [
    # Women's Health
    ("gynecological health", "Women's Health"),
    ("reproductive health", "Women's Health"),
    ("pelvic health", "Women's Health"),
    ("hormone balance", "Women's Health"),
    ("fertility", "Women's Health"),
    ("prenatal care", "Women's Health"),
    ("postpartum care", "Women's Health"),
    ("menstrual health", "Women's Health"),
    ("contraception", "Women's Health"),
    ("breast health", "Women's Health"),
    ("sexual wellness", "Women's Health"),
    ("hormonal health", "Women's Health"),
    ("thyroid disorders", "Women's Health"),

    # Menopause
    ("hot flashes", "Menopause"),
    ("night sweats", "Menopause"),
    ("mood swings", "Menopause"),
    ("hormone replacement therapy (HRT)", "Menopause"),
    ("perimenopause", "Menopause"),
    ("postmenopause", "Menopause"),
    ("vaginal dryness", "Menopause"),
    ("osteoporosis risk", "Menopause"),
    ("sleep disturbances", "Menopause"),
    ("weight gain", "Menopause"),
    ("menopause supplements", "Menopause"),

    # PCOS (Polycystic Ovary Syndrome)
    ("irregular periods", "PCOS"),
    ("insulin resistance", "PCOS"),
    ("fertility issues", "PCOS"),
    ("ovarian cysts", "PCOS"),
    ("hormonal imbalance", "PCOS"),
    ("weight gain", "PCOS"),
    ("excessive hair growth (hirsutism)", "PCOS"),
    ("acne", "PCOS"),
    ("thinning hair", "PCOS"),
    ("lifestyle changes", "PCOS"),
    ("PCOS diet", "PCOS"),

    # Ovarian Health
    ("ovarian cancer", "Ovarian Health"),
    ("pelvic pain", "Ovarian Health"),
    ("ovarian cysts", "Ovarian Health"),
    ("egg health", "Ovarian Health"),
    ("ovarian reserve", "Ovarian Health"),
    ("follicle count", "Ovarian Health"),
    ("infertility", "Ovarian Health"),
    ("ovarian aging", "Ovarian Health"),
    ("egg freezing", "Ovarian Health"),
    ("hormonal testing", "Ovarian Health"),
]

keywords_substance_abuse = [
    # Alcohol Addiction
    ("alcoholism", "Alcohol Addiction"),
    ("binge drinking", "Alcohol Addiction"),
    ("alcohol abuse", "Alcohol Addiction"),
    ("alcohol dependence", "Alcohol Addiction"),
    ("recovery", "Alcohol Addiction"),
    ("withdrawal", "Alcohol Addiction"),
    ("detoxification", "Alcohol Addiction"),
    ("AA (Alcoholics Anonymous)", "Alcohol Addiction"),
    ("sober living", "Alcohol Addiction"),
    ("alcohol-related liver disease", "Alcohol Addiction"),

    # Opioid Abuse
    ("oxycodone", "Opioid Abuse"),
    ("fentanyl", "Opioid Abuse"),
    ("heroin", "Opioid Abuse"),
    ("painkillers", "Opioid Abuse"),
    ("opioid dependence", "Opioid Abuse"),
    ("overdose", "Opioid Abuse"),
    ("naloxone", "Opioid Abuse"),
    ("prescription drug abuse", "Opioid Abuse"),
    ("methadone", "Opioid Abuse"),
    ("suboxone", "Opioid Abuse"),
    ("opioid crisis", "Opioid Abuse"),

    # Cocaine Dependency
    ("cocaine abuse", "Cocaine Dependency"),
    ("crack cocaine", "Cocaine Dependency"),
    ("cocaine addiction", "Cocaine Dependency"),
    ("stimulants", "Cocaine Dependency"),
    ("dependency treatment", "Cocaine Dependency"),
    ("withdrawal symptoms", "Cocaine Dependency"),
    ("relapse", "Cocaine Dependency"),
    ("powder cocaine", "Cocaine Dependency"),
    ("long-term effects", "Cocaine Dependency"),
    ("cocaine-induced psychosis", "Cocaine Dependency"),
    ("treatment centers", "Cocaine Dependency"),

    # Nicotine Addiction
    ("smoking", "Nicotine Addiction"),
    ("vaping", "Nicotine Addiction"),
    ("tobacco", "Nicotine Addiction"),
    ("cigarettes", "Nicotine Addiction"),
    ("nicotine replacement therapy", "Nicotine Addiction"),
    ("e-cigarettes", "Nicotine Addiction"),
    ("quitting smoking", "Nicotine Addiction"),
    ("nicotine withdrawal", "Nicotine Addiction"),
    ("chewing tobacco", "Nicotine Addiction"),
    ("nicotine patches", "Nicotine Addiction"),
    ("smoking cessation", "Nicotine Addiction"),
]

keywords_terminal_conditions = [
    # Cancer
    ("chemotherapy", "Cancer"),
    ("tumor", "Cancer"),
    ("radiation therapy", "Cancer"),
    ("oncology", "Cancer"),
    ("metastasis", "Cancer"),
    ("carcinoma", "Cancer"),
    ("immunotherapy", "Cancer"),
    ("biopsy", "Cancer"),
    ("palliative care", "Cancer"),
    ("malignancy", "Cancer"),
    ("cancer awareness", "Cancer"),
    ("breast cancer", "Cancer"),
    ("prostate cancer", "Cancer"),

    # ALS (Amyotrophic Lateral Sclerosis)
    ("neurodegenerative", "ALS"),
    ("motor neurons", "ALS"),
    ("muscle weakness", "ALS"),
    ("paralysis", "ALS"),
    ("Lou Gehrig’s disease", "ALS"),
    ("respiratory failure", "ALS"),
    ("speech therapy", "ALS"),
    ("spasticity", "ALS"),
    ("riluzole (drug)", "ALS"),
    ("progressive disorder", "ALS"),

    # Dementia
    ("Alzheimer's", "Dementia"),
    ("memory loss", "Dementia"),
    ("cognitive decline", "Dementia"),
    ("neurodegeneration", "Dementia"),
    ("caregiver support", "Dementia"),
    ("behavioral changes", "Dementia"),
    ("sundowning", "Dementia"),
    ("Lewy body dementia", "Dementia"),
    ("vascular dementia", "Dementia"),
    ("brain atrophy", "Dementia"),
    ("dementia awareness", "Dementia"),

    # HIV
    ("antiretroviral therapy (ART)", "HIV"),
    ("CD4 cells", "HIV"),
    ("viral load", "HIV"),
    ("opportunistic infections", "HIV"),
    ("PrEP (Pre-exposure prophylaxis)", "HIV"),
    ("HIV testing", "HIV"),
    ("stigma", "HIV"),
    ("immune suppression", "HIV"),
    ("Kaposi’s sarcoma", "HIV"),
    ("HIV prevention", "HIV"),
    ("T-helper cells", "HIV"),
]

# Merge lists, then convert to data frame
keywords_data = keywords_mental_health + keywords_physical_health + keywords_women_health + keywords_substance_abuse + keywords_terminal_conditions
df = pd.DataFrame(keywords_data, columns=["keyword", "category"])

print(f"path to store csv with keywords: {KEYWORDS_FILE}")
df.to_csv(KEYWORDS_FILE, index=False) 
