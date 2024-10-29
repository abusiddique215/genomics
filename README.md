# AI-Enhanced Treatment Recommendation System

A scalable, microservices-based system that analyzes genomics data and medical history to provide personalized treatment recommendations.

## System Architecture

The system consists of several microservices:

- **Patient Management Service** (Port 8080)
  - Handles patient data CRUD operations
  - Integrates with DynamoDB for data persistence
  - Provides treatment recommendation endpoints

- **Treatment Prediction Service** (Port 8083)
  - AI-powered treatment recommendation engine
  - Uses TensorFlow for prediction models
  - Analyzes genomic markers and medical history

- **Data Ingestion Service** (Port 8084)
  - Handles genomics data ingestion
  - Supports multiple data formats (CSV, FASTA)
  - Performs data validation and preprocessing

- **DynamoDB Local** (Port 8000)
  - Local DynamoDB instance for development
  - Stores patient records and medical history
  - Maintains treatment outcomes

## Prerequisites

- Python 3.10 or higher
- Java Runtime Environment (for DynamoDB Local)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd genomics
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the System

The system can be started using a single command:

```bash
python run_system.py
```

This will:
1. Start DynamoDB Local
2. Initialize required database tables
3. Start all microservices
4. Run system tests to verify functionality

## API Endpoints

### Patient Management Service (8080)

- `GET /patients` - List all patients
- `GET /patients/{id}` - Get patient details
- `POST /patients` - Create new patient
- `GET /patients/{id}/treatment_recommendation` - Get treatment recommendation

### Treatment Prediction Service (8083)

- `POST /predict` - Generate treatment prediction
- `GET /health` - Service health check

### Data Ingestion Service (8084)

- `POST /ingest/genomics` - Ingest genomics data
- `POST /ingest/medical-history` - Ingest medical history
- `GET /health` - Service health check

## Data Models

### Patient Record
```json
{
  "id": "string",
  "name": "string",
  "age": number,
  "genomic_data": {
    "gene_variants": {
      "BRCA1": "string",
      "BRCA2": "string"
    },
    "mutation_scores": {
      "BRCA1": "string",
      "BRCA2": "string"
    }
  },
  "medical_history": {
    "conditions": ["string"],
    "treatments": ["string"],
    "allergies": ["string"],
    "medications": ["string"]
  }
}
```

### Treatment Recommendation
```json
{
  "recommended_treatment": "string",
  "efficacy": number,
  "confidence_level": "string"
}
```

## Development

### Project Structure
```
genomics/
├── services/
│   ├── patient_management/
│   ├── treatment_prediction/
│   ├── data_ingestion/
│   └── utils/
├── tests/
├── requirements.txt
└── run_system.py
```

### Running Tests

System tests are automatically run during startup, but can also be run manually:

```bash
python -m tests.system_test
```

### Logging

The system uses structured logging with different levels:
- INFO: Service status, health checks
- DEBUG: Detailed operation logs
- ERROR: Error conditions

Logs are filtered to show relevant information while running.

## Monitoring

The system provides real-time status updates and health checks:
- Service startup status
- Database connectivity
- API endpoint health
- Treatment prediction status

## Shutdown

To gracefully shut down all services:
1. Press Ctrl+C in the terminal running `run_system.py`
2. The system will automatically clean up all processes

## Security

- All services use CORS middleware
- DynamoDB uses secure credentials
- Input validation on all endpoints
- Error handling and logging

## Future Improvements

1. Add authentication and authorization
2. Implement more sophisticated AI models
3. Add real-time monitoring dashboard
4. Implement data backup and recovery
5. Add support for more genomic data formats

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
