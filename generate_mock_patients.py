import boto3
from faker import Faker
import random
from botocore.exceptions import ClientError

# Initialize Faker and boto3 clients
fake = Faker()
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Patients')

# Function to generate mock genomic data
def generate_genomic_data():
    return {
        "gene_" + str(i): {
            "variant": fake.lexify(text="??????????"),
            "zygosity": random.choice(["Heterozygous", "Homozygous"]),
            "clinical_significance": random.choice(["Benign", "Likely benign", "Uncertain significance", "Likely pathogenic", "Pathogenic"])
        } for i in range(1, 6)  # Generate data for 5 genes
    }

# Function to generate mock medical history
def generate_medical_history():
    return {
        "conditions": [fake.word() for _ in range(random.randint(0, 5))],
        "allergies": [fake.word() for _ in range(random.randint(0, 3))],
        "medications": [fake.word() for _ in range(random.randint(0, 4))]
    }

# Function to create a mock patient
def create_mock_patient():
    return {
        "id": fake.uuid4(),
        "name": fake.name(),
        "age": random.randint(18, 90),
        "genomic_data": generate_genomic_data(),
        "medical_history": generate_medical_history()
    }

# Function to add a patient to DynamoDB
def add_patient_to_dynamodb(patient):
    try:
        response = table.put_item(Item=patient)
        print(f"Added patient: {patient['name']}")
    except ClientError as e:
        print(f"Error adding patient: {e.response['Error']['Message']}")

# Main function to generate and add mock patients
def generate_mock_patients(num_patients):
    for _ in range(num_patients):
        patient = create_mock_patient()
        add_patient_to_dynamodb(patient)

if __name__ == "__main__":
    num_patients = int(input("Enter the number of mock patients to generate: "))
    generate_mock_patients(num_patients)
    print(f"Generated and added {num_patients} mock patients to DynamoDB.")