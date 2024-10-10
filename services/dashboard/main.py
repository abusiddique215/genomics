import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi import FastAPI
import boto3
from dash.dependencies import Input, Output

# Initialize FastAPI app
server = FastAPI()

# Initialize Dash app
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP], url_base_pathname='/dashboard/')

# Initialize AWS DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Patients')

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
    # Fetch patient data from DynamoDB
    response = table.scan()
    patients = response['Items']
    
    df = pd.DataFrame(patients)
    fig = px.histogram(df, x='age', title='Patient Age Distribution')
    return fig

@app.callback(
    Output('treatment-efficacy', 'figure'),
    Input('treatment-efficacy', 'relayoutData')
)
def update_treatment_efficacy(relayoutData):
    # This is a placeholder. In a real scenario, you'd fetch and process treatment data.
    treatments = ['Treatment A', 'Treatment B', 'Treatment C']
    efficacy = [0.75, 0.62, 0.88]
    
    fig = px.bar(x=treatments, y=efficacy, title='Treatment Efficacy')
    return fig

# Mount Dash app
server.mount("/dashboard", WSGIMiddleware(app.server))

@server.get("/")
def read_root():
    return {"message": "Welcome to the Genomics Treatment API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(server, host="0.0.0.0", port=8000)