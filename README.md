# Genomics Treatment API

This project is an AI-enhanced personalized treatment recommendation system using genomics data. It analyzes a patient's genetic profile and medical history to suggest tailored treatment options and predict treatment efficacy.

## Features

- Genomics data ingestion and preprocessing
- AI model training for treatment prediction
- Personalized treatment recommendations
- Patient data management
- Integration with Power BI for data visualization

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/genomics-treatment-api.git
   cd genomics-treatment-api
   ```

2. Create a new virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up your AWS credentials for S3 and DynamoDB access.

5. Configure your Power BI integration settings in `services/powerbi_integration/main.py`.

## Running the Services

Each service can be run independently using Uvicorn. For example:

```
uvicorn services.data_ingestion.main:app --reload
```

Replace `data_ingestion` with the name of the service you want to run.

## Testing

Run the tests using pytest:

```
pytest
```

## Deployment

This project is designed to be deployed as serverless functions. Refer to `template.yaml` for the AWS SAM template.

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct, and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.