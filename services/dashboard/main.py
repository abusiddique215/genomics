import os
import sys
import boto3
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import requests
from botocore.exceptions import ClientError

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from services.utils.logging import setup_logging

logger = setup_logging()

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
patients_table = dynamodb.Table('Patients')

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], url_base_pathname='/dashboard/')

def get_patients():
    try:
        response = patients_table.scan()
        patients = response['Items']
        return [{'label': f"{patient['name']} (ID: {patient['id']})", 'value': patient['id']} for patient in patients]
    except ClientError as e:
        logger.error(f"Error fetching patients from DynamoDB: {str(e)}")
        return []

app.layout = dbc.Container([
    html.H1("Genomics Treatment Dashboard"),
    dbc.Row([
        dbc.Col([
            html.H2("Patient List"),
            dcc.Dropdown(
                id='patient-dropdown',
                options=get_patients(),
                placeholder="Select a patient"
            )
        ], width=6),
        dbc.Col([
            html.H2("AI Insights"),
            dbc.Input(id="question-input", type="text", placeholder="Ask a question about the patients..."),
            dbc.Button("Ask AI", id="ask-button", color="primary", className="mt-2"),
            html.Div(id="ai-response", className="mt-3")
        ], width=6)
    ])
])

@app.callback(
    Output("ai-response", "children"),
    Input("ask-button", "n_clicks"),
    State("question-input", "value"),
    prevent_initial_call=True
)
def query_ai(n_clicks, question):
    if question:
        try:
            response = requests.post("http://localhost:8006/query", json={"question": question})
            if response.status_code == 200:
                return response.json()["answer"]
            else:
                return "Error querying AI"
        except Exception as e:
            logger.error(f"Error querying RAG pipeline: {str(e)}")
            return "An error occurred while querying the AI."
    return "Please enter a question."

if __name__ == '__main__':
    print("Dashboard starting on http://0.0.0.0:8050/dashboard/")
    app.run_server(debug=True, host='0.0.0.0', port=8050)
