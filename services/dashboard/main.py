import os
import sys
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import logging
import requests

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
from flask import Flask, render_template
from dash.dependencies import Input, Output, State

# Initialize Flask app
server = Flask(__name__)

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    table = None  # Set table to None if connection fails

# Layout of the dashboard
app.layout = dbc.Container([
    html.H1("Genomics Treatment Dashboard"),
    dbc.Row([
        dbc.Col([
            html.H2("Patient List"),
            dcc.Dropdown(id="patient-dropdown"),
            html.Div(id="patient-details")
        ], width=6),
        dbc.Col([
            html.H2("AI Insights"),
            dbc.Input(id="ai-question-input", placeholder="Ask a question about the patients...", type="text"),
            dbc.Button("Ask AI", id="ai-question-button", color="primary", className="mt-2"),
            html.Div(id="ai-answer-output", className="mt-3")
        ], width=6)
    ])
])

@app.callback(
    Output("ai-answer-output", "children"),
    Input("ai-question-button", "n_clicks"),
    State("ai-question-input", "value")
)
def update_ai_answer(n_clicks, question):
    if n_clicks and question:
        answer = query_rag_pipeline(question)
        return html.P(answer)
    return ""

def query_rag_pipeline(question):
    try:
        response = requests.post(f"{os.getenv('RAG_SERVICE_URL')}/query", json={"question": question})
        if response.status_code == 200:
            return response.json()["answer"]
        else:
            logger.error(f"Failed to query RAG pipeline: {response.text}")
            return "Failed to get an answer from the AI."
    except Exception as e:
        logger.error(f"Error querying RAG pipeline: {str(e)}")
        return "An error occurred while querying the AI."

# Add a route for the root URL
@server.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=8050)