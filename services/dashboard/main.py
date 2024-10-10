import os
import sys
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from flask import Flask
from dash.dependencies import Input, Output
from services.utils.logging import setup_logging

# Initialize Flask app
server = Flask(__name__)
logger = setup_logging()

# Initialize Dash app
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP], url_base_pathname='/dashboard/')

# Initialize AWS DynamoDB client
try:
    aws_region = os.getenv('AWS_DEFAULT_REGION')
    if not aws_region:
        raise ValueError("AWS_DEFAULT_REGION is not set in the environment variables")
    
    dynamodb = boto3.resource('dynamodb',
                              region_name=aws_region,
                              aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                              aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
    table = dynamodb.Table('Patients')
    logger.info(f"Successfully connected to AWS DynamoDB in region: {aws_region}")
except (ClientError, ValueError) as e:
    logger.error(f"Error connecting to AWS: {str(e)}")
    raise

# Layout of the dashboard
app.layout = dbc.Container([
    html.H1("Genomics Treatment Dashboard"),
    dbc.Row([
        dbc.Col([
            html.H3("Patient Age Distribution"),
            dcc.Graph(id='age-distribution')
        ], width=6),
        dbc.Col([
            html.H3("Treatment Efficacy"),
            dcc.Graph(id='treatment-efficacy')
        ], width=6)
    ])
])

@app.callback(
    Output('age-distribution', 'figure'),
    Input('age-distribution', 'relayoutData')
)
def update_age_distribution(relayoutData):
    try:
        if table is None:
            raise Exception("DynamoDB table not initialized")
        
        # Fetch patient data from DynamoDB
        response = table.scan()
        patients = response['Items']
        
        df = pd.DataFrame(patients)
        fig = px.histogram(df, x='age', title='Patient Age Distribution')
        return fig
    except Exception as e:
        logger.error(f"Error fetching patient data: {str(e)}")
        return px.histogram(title='Error: Unable to fetch patient data')

@app.callback(
    Output('treatment-efficacy', 'figure'),
    Input('treatment-efficacy', 'relayoutData')
)
def update_treatment_efficacy(relayoutData):
    try:
        # This is a placeholder. In a real scenario, you'd fetch and process treatment data.
        treatments = ['Treatment A', 'Treatment B', 'Treatment C']
        efficacy = [0.75, 0.62, 0.88]
        
        fig = px.bar(x=treatments, y=efficacy, title='Treatment Efficacy')
        return fig
    except Exception as e:
        logger.error(f"Error generating treatment efficacy graph: {str(e)}")
        return px.bar(title='Error: Unable to generate treatment efficacy graph')

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8000)