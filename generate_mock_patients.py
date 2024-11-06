import json
import random
from datetime import datetime
import uuid
from typing import Dict, Any, List

def generate_mock_patient(patient_id: int) -> Dict[str, Any]:
    """Generate a single mock patient with string values for numeric fields"""
    first_names = ['John', 'Jane', 'Michael', 'Emily', 'David', 'Sarah', 'James', 'Emma', 'William', 'Olivia']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
    
    conditions = ['Hypertension', 'Diabetes', 'Asthma', 'Arthritis', 'Cancer', 'Heart Disease', 'COPD', 'Depression']
    treatments = ['Chemotherapy', 'Radiation', 'Surgery', 'Immunotherapy', 'Hormone Therapy', 'Targeted Therapy']
    medications = ['Lisinopril', 'Metformin', 'Albuterol', 'Ibuprofen', 'Omeprazole', 'Levothyroxine']
    allergies = ['Penicillin', 'Sulfa', 'Aspirin', 'Latex', 'Peanuts', 'None']
    
    genes = ['BRCA1', 'BRCA2', 'TP53', 'EGFR', 'KRAS', 'BRAF', 'ALK', 'PTEN']
    variants = ['variant1', 'variant2', 'variant3', 'variant4', 'variant5']
    
    # Generate gene variants and scores
    selected_genes = random.sample(genes, random.randint(2, 5))
    gene_variants = {gene: random.choice(variants) for gene in selected_genes}
    mutation_scores = {
        gene: str(round(random.uniform(0.1, 1.0), 2))  # Convert to string
        for gene in selected_genes
    }
    
    return {
        "id": f"P{str(patient_id).zfill(3)}",
        "name": f"{random.choice(first_names)} {random.choice(last_names)}",
        "age": str(random.randint(25, 80)),  # Convert to string
        "gender": random.choice(['M', 'F']),
        "genomic_data": {
            "gene_variants": gene_variants,
            "mutation_scores": mutation_scores,
            "sequencing_quality": str(round(random.uniform(0.8, 1.0), 2))  # Convert to string
        },
        "medical_history": {
            "conditions": random.sample(conditions, random.randint(1, 3)),
            "treatments": random.sample(treatments, random.randint(1, 3)),
            "medications": random.sample(medications, random.randint(1, 4)),
            "allergies": random.sample(allergies, random.randint(0, 2))
        },
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
    }

def generate_treatment_history(patient_id: str) -> Dict[str, Any]:
    """Generate treatment history for a patient"""
    return {
        "patient_id": patient_id,
        "treatment_id": str(uuid.uuid4()),
        "treatment": random.choice([
            'Chemotherapy', 'Radiation', 'Surgery', 
            'Immunotherapy', 'Hormone Therapy', 'Targeted Therapy'
        ]),
        "start_date": (datetime.now().isoformat()),
        "end_date": (datetime.now().isoformat()) if random.random() > 0.3 else None,
        "efficacy_score": str(round(random.uniform(0.3, 0.9), 2)),  # Convert to string
        "side_effects": random.sample([
            'Nausea', 'Fatigue', 'Pain', 'Hair Loss', 
            'Appetite Loss', 'Skin Issues'
        ], random.randint(0, 3))
    }

def main():
    """Generate mock patients and their treatment histories"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate mock patient data')
    parser.add_argument('--count', type=int, default=10, help='Number of patients to generate')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--treatment-history', action='store_true', help='Generate treatment history')
    parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    
    args = parser.parse_args()
    
    # Generate patients
    patients = [generate_mock_patient(i+1) for i in range(args.count)]
    
    # Save patients
    if args.output:
        with open(args.output, 'w') as f:
            if args.pretty:
                json.dump(patients, f, indent=2)
            else:
                json.dump(patients, f)
        print(f"Generated {args.count} mock patients")
        print(f"Data saved to {args.output}")
    
    # Generate and save treatment history if requested
    if args.treatment_history and args.output:
        histories = []
        for patient in patients:
            num_treatments = random.randint(1, 3)
            for _ in range(num_treatments):
                histories.append(generate_treatment_history(patient['id']))
        
        history_file = args.output.replace('.json', '_history.json')
        with open(history_file, 'w') as f:
            if args.pretty:
                json.dump(histories, f, indent=2)
            else:
                json.dump(histories, f)
        print(f"Treatment history saved to {history_file}")

if __name__ == '__main__':
    main()
