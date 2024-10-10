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

2. Set up environment variables:
   Create a `.env` file in the root directory with the following content:
   ```
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   ```

3. Build and run the services:
   ```
   docker-compose up --build
   ```

## API Endpoints

- Data Ingestion: `POST http://localhost:8001/ingest/`
- Preprocessing: `POST http://localhost:8002/preprocess/{file_name}`
- AI Model Training: `POST http://localhost:8003/train/{file_name}`
- Treatment Prediction: `POST http://localhost:8004/predict/{model_name}`

## Running Tests

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

## Dashboard

The project includes a Plotly Dash dashboard for visualizing patient data and treatment efficacy. To access the dashboard:

1. Ensure all services are running (`docker-compose up --build`)
2. Open a web browser and navigate to `http://localhost:8005/dashboard`

The dashboard provides interactive visualizations of patient age distribution and treatment efficacy.

## AWS Setup

This project uses the following AWS services:

1. DynamoDB: For storing patient data
2. S3: For storing genomic data files

Make sure to set up these services and update the `.env` file with the necessary credentials and configurations.