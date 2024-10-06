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

2. Create a virtual environment and activate it:
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
