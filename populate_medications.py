#!/usr/bin/env python3
"""
Populate medications table with common medications
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')

print("\n" + "="*60)
print("Populating medications table")
print("="*60 + "\n")

medications_data = [
    {
        'name': 'metformin',
        'generic_name': 'Metformin Hydrochloride',
        'description': 'Diabetes medication that helps control blood sugar',
        'common_side_effects': 'Nausea, diarrhea, GI upset',
        'how_it_works': 'Reduces glucose production in the liver and increases insulin sensitivity',
        'plain_language_explanation': 'Helps your body use insulin better and controls blood sugar levels',
        'contraindications': 'Kidney disease, liver disease, heart failure',
        'storage_instructions': 'Store at room temperature, away from moisture',
        'manufacturer': 'Generic'
    },
    {
        'name': 'aspirin',
        'generic_name': 'Acetylsalicylic Acid',
        'description': 'Pain reliever and anti-inflammatory medication',
        'common_side_effects': 'Stomach upset, heartburn, increased bleeding',
        'how_it_works': 'Reduces pain and inflammation by inhibiting prostaglandins',
        'plain_language_explanation': 'Relieves pain, fever, and inflammation; thins blood at low doses',
        'contraindications': 'Ulcers, bleeding disorders, allergy to aspirin',
        'storage_instructions': 'Store at room temperature in a dry place',
        'manufacturer': 'Generic'
    },
    {
        'name': 'amoxicillin',
        'generic_name': 'Amoxicillin Trihydrate',
        'description': 'Antibiotic used to treat bacterial infections',
        'common_side_effects': 'Nausea, diarrhea, allergic reactions, rash',
        'how_it_works': 'Kills bacteria by inhibiting cell wall synthesis',
        'plain_language_explanation': 'Antibiotic that kills harmful bacteria causing infections',
        'contraindications': 'Penicillin allergy, mononucleosis',
        'storage_instructions': 'Store in refrigerator if liquid; tablets at room temperature',
        'manufacturer': 'Generic'
    },
    {
        'name': 'lisinopril',
        'generic_name': 'Lisinopril Dihydrate',
        'description': 'ACE inhibitor for blood pressure control',
        'common_side_effects': 'Dry cough, dizziness, fatigue',
        'how_it_works': 'Relaxes blood vessels by blocking angiotensin II production',
        'plain_language_explanation': 'Lowers blood pressure and reduces heart workload',
        'contraindications': 'Pregnancy, kidney disease, angioedema history',
        'storage_instructions': 'Store at room temperature away from light',
        'manufacturer': 'Generic'
    },
    {
        'name': 'ibuprofen',
        'generic_name': 'Ibuprofen',
        'description': 'NSAID for pain and inflammation relief',
        'common_side_effects': 'Stomach upset, heartburn, dizziness',
        'how_it_works': 'Reduces prostaglandins that cause pain and inflammation',
        'plain_language_explanation': 'Relieves pain, fever, and inflammation quickly',
        'contraindications': 'Ulcers, kidney disease, heart problems, aspirin allergy',
        'storage_instructions': 'Store at room temperature, away from moisture and heat',
        'manufacturer': 'Generic'
    },
    {
        'name': 'atorvastatin',
        'generic_name': 'Atorvastatin Calcium',
        'description': 'Statin medication to lower cholesterol',
        'common_side_effects': 'Muscle pain, liver problems, digestive issues',
        'how_it_works': 'Inhibits HMG-CoA reductase to reduce cholesterol production',
        'plain_language_explanation': 'Lowers bad cholesterol (LDL) and reduces heart disease risk',
        'contraindications': 'Liver disease, pregnancy, active muscle problems',
        'storage_instructions': 'Store at room temperature away from light',
        'manufacturer': 'Generic'
    },
    {
        'name': 'omeprazole',
        'generic_name': 'Omeprazole',
        'description': 'Proton pump inhibitor for acid reflux',
        'common_side_effects': 'Headache, nausea, abdominal pain',
        'how_it_works': 'Blocks acid production in the stomach',
        'plain_language_explanation': 'Reduces stomach acid and heals acid reflux damage',
        'contraindications': 'Certain drug interactions, long-term use concerns',
        'storage_instructions': 'Store at room temperature in original container',
        'manufacturer': 'Generic'
    },
    {
        'name': 'levothyroxine',
        'generic_name': 'Levothyroxine Sodium',
        'description': 'Thyroid hormone replacement',
        'common_side_effects': 'Tremor, anxiety, insomnia, heart palpitations',
        'how_it_works': 'Replaces thyroid hormone and regulates metabolism',
        'plain_language_explanation': 'Replaces thyroid hormone when your thyroid doesn\'t produce enough',
        'contraindications': 'Hyperthyroidism, untreated heart conditions',
        'storage_instructions': 'Store at room temperature away from moisture',
        'manufacturer': 'Generic'
    },
    {
        'name': 'metoprolol',
        'generic_name': 'Metoprolol Tartrate',
        'description': 'Beta-blocker for heart and blood pressure',
        'common_side_effects': 'Fatigue, dizziness, cold hands/feet',
        'how_it_works': 'Blocks beta-adrenergic receptors to reduce heart rate and blood pressure',
        'plain_language_explanation': 'Slows heart rate and lowers blood pressure',
        'contraindications': 'Asthma, COPD, heart block, cardiogenic shock',
        'storage_instructions': 'Store at room temperature, protect from light',
        'manufacturer': 'Generic'
    },
    {
        'name': 'sertraline',
        'generic_name': 'Sertraline Hydrochloride',
        'description': 'SSRI antidepressant for depression and anxiety',
        'common_side_effects': 'Nausea, dry mouth, insomnia, sexual dysfunction',
        'how_it_works': 'Increases serotonin levels in the brain',
        'plain_language_explanation': 'Helps balance brain chemicals to improve mood and reduce anxiety',
        'contraindications': 'MAOI use, bipolar disorder without mood stabilizer',
        'storage_instructions': 'Store at room temperature away from moisture',
        'manufacturer': 'Generic'
    }
]

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=10
    )
    print(f"✓ Connected to PostgreSQL\n")
    
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM medications")
    deleted = cursor.rowcount
    print(f"Cleared {deleted} old records\n")
    
    print("Adding medications:\n")
    
    for med in medications_data:
        cursor.execute("""
            INSERT INTO medications
            (name, generic_name, description, common_side_effects, 
             how_it_works, plain_language_explanation, contraindications,
             storage_instructions, manufacturer, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            med['name'],
            med['generic_name'],
            med['description'],
            med['common_side_effects'],
            med['how_it_works'],
            med['plain_language_explanation'],
            med['contraindications'],
            med['storage_instructions'],
            med['manufacturer']
        ))
        
        print(f"  ✓ {med['name'].capitalize()} ({med['generic_name']})")
    
    conn.commit()
    print(f"\n✓ Successfully inserted {len(medications_data)} medications\n")
    
    # Show summary
    cursor.execute("SELECT COUNT(*) FROM medications")
    count = cursor.fetchone()[0]
    print(f"Total medications in database: {count}")
    
    # List all
    cursor.execute("SELECT name FROM medications ORDER BY name")
    print("\nAll medications:")
    for row in cursor.fetchall():
        print(f"  ✓ {row[0]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60 + "\n")
