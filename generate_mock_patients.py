#!/usr/bin/env python3

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
import argparse
import os
from pathlib import Path

# Gene variants and their associated conditions
GENE_VARIANTS = {
    'BRCA1': ['variant1', 'variant2', 'variant3'],
    'BRCA2': ['variant1', 'variant2', 'variant3'],
    'TP53': ['variant1', 'variant2'],
    'EGFR': ['variant1', 'variant2', 'variant3', 'variant4'],
    'KRAS': ['variant1', 'variant2'],
    'BRAF': ['variant1', 'variant2'],
    'ALK': ['variant1', 'variant2', 'variant3'],
    'PTEN': ['variant1', 'variant2']
}

MEDICAL_CONDITIONS = [
    'Breast Cancer',
    'Ovarian Cancer',
    'Lung Cancer',
    'Colorectal Cancer',
    'Melanoma',
    'Leukemia',
    'Lymphoma',
    'Pancreatic Cancer'
]

TREATMENTS = [
    'Chemotherapy',
    'Radiation Therapy',
    'Immunotherapy',
    'Targeted Therapy',
    'Hormone Therapy',
    'Surgery',
    'Stem Cell Transplant',
    'Gene Therapy'
]

MEDICATIONS = [
    'Tamoxifen',
    'Letrozole',
    'Trastuzumab',
    'Pembrolizumab',
    'Nivolumab',
    'Olaparib',
    'Palbociclib',
    'Erlotinib'
]

ALLERGIES = [
    'Penicillin',
    'Sulfa Drugs',
    'Iodine',
    'Latex',
    'Aspirin',
    'Morphine',
    'Codeine'
]

def generate_genomic_data() -> Dict[str, Any]:
    """Generate mock genomic data"""
    gene_variants = {}
    mutation_scores = {}
    
    # Select random genes and variants
    selected_genes = random.sample(list(GENE_VARIANTS.keys()), random.randint(2, 5))
    
    for gene in selected_genes:
        # Select random variant
        variant = random.choice(GENE_VARIANTS[gene])
        gene_variants[gene] = variant
        
        # Generate mutation score
        mutation_scores[gene] = round(random.uniform(0.1, 1.0), 2)
    
    return {
        "gene_variants": gene_variants,
        "mutation_scores": mutation_scores,
        "sequencing_quality": round(random.uniform(0.8, 1.0), 2),
        "analysis_date": (
            datetime.now() - timedelta(days=random.randint(0, 365))
        ).isoformat()
    }

def generate_medical_history() -> Dict[str, Any]:
    """Generate mock medical history"""
    num_conditions = random.randint(1, 3)
    num_treatments = random.randint(1, 4)
    num_medications = random.randint(1, 5)
    num_allergies = random.randint(0, 3)
    
    return {
        "conditions": random.sample(MEDICAL_CONDITIONS, num_conditions),
        "treatments": random.sample(TREATMENTS, num_treatments),
        "medications": random.sample(MEDICATIONS, num_medications),
        "allergies": random.sample(ALLERGIES, num_allergies),
        "diagnosis_dates": [
            (datetime.now() - timedelta(days=random.randint(0, 730))).isoformat()
            for _ in range(num_conditions)
        ]
    }

def generate_patient(patient_id: str = None) -> Dict[str, Any]:
    """Generate a mock patient record"""
    if not patient_id:
        patient_id = f"P{uuid.uuid4().hex[:6].upper()}"
    
    # Generate name
    first_names = ['John', 'Jane', 'Michael', 'Emily', 'David', 'Sarah']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia']
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    
    return {
        "id": patient_id,
        "name": name,
        "age": random.randint(25, 85),
        "gender": random.choice(['M', 'F']),
        "genomic_data": generate_genomic_data(),
        "medical_history": generate_medical_history(),
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "data_version": "1.0"
        }
    }

def generate_patient_batch(
    count: int,
    output_file: str = None,
    pretty: bool = False
) -> List[Dict[str, Any]]:
    """Generate a batch of mock patients"""
    patients = [generate_patient() for _ in range(count)]
    
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            if pretty:
                json.dump(patients, f, indent=2)
            else:
                json.dump(patients, f)
    
    return patients

def generate_treatment_history(patient: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate mock treatment history"""
    num_treatments = len(patient['medical_history']['treatments'])
    history = []
    
    for i in range(num_treatments):
        treatment = patient['medical_history']['treatments'][i]
        start_date = datetime.now() - timedelta(days=random.randint(30, 365))
        
        history.append({
            "patient_id": patient['id'],
            "treatment": treatment,
            "start_date": start_date.isoformat(),
            "end_date": (
                start_date + timedelta(days=random.randint(30, 180))
            ).isoformat() if random.random() > 0.3 else None,
            "efficacy_score": round(random.uniform(0.3, 0.9), 2),
            "side_effects": random.sample(
                ['Nausea', 'Fatigue', 'Pain', 'Hair Loss'],
                random.randint(0, 3)
            ),
            "notes": f"Treatment {i+1} notes"
        })
    
    return history

def main():
    parser = argparse.ArgumentParser(description='Generate mock patient data')
    parser.add_argument(
        '--count',
        type=int,
        default=10,
        help='Number of patients to generate'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path'
    )
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Pretty print JSON output'
    )
    parser.add_argument(
        '--treatment-history',
        action='store_true',
        help='Generate treatment history'
    )
    
    args = parser.parse_args()
    
    # Generate patients
    patients = generate_patient_batch(args.count, args.output, args.pretty)
    
    # Generate treatment history if requested
    if args.treatment_history:
        treatment_history = []
        for patient in patients:
            treatment_history.extend(generate_treatment_history(patient))
        
        if args.output:
            history_file = os.path.splitext(args.output)[0] + '_history.json'
            with open(history_file, 'w') as f:
                if args.pretty:
                    json.dump(treatment_history, f, indent=2)
                else:
                    json.dump(treatment_history, f)
    
    print(f"Generated {args.count} mock patients")
    if args.output:
        print(f"Data saved to {args.output}")
        if args.treatment_history:
            print(f"Treatment history saved to {history_file}")

if __name__ == '__main__':
    main()
