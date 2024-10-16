#!/bin/bash

set -x  # Add this line for verbose output

# Navigate to the project directory
cd "$(dirname "$0")"

# Activate the virtual environment
source venv/bin/activate

# Set environment variables
set -a
source .env
set +a

# Add the project root to PYTHONPATH
export PYTHONPATH="$PYTHONPATH:$(pwd)"

# Check AWS permissions
echo "Checking AWS permissions..."
python verify_iam_setup.py

# Start each service individually
echo "Starting dashboard service..."
python -m services.dashboard.main &
DASHBOARD_PID=$!

echo "Starting patient_management service..."
python -m services.patient_management.main &
PATIENT_MANAGEMENT_PID=$!

echo "Starting rag_pipeline service..."
python -m services.rag_pipeline.main &
RAG_PIPELINE_PID=$!

echo "Starting model_training service..."
python -m services.model_training.main &
MODEL_TRAINING_PID=$!

echo "Starting Streamlit dashboard..."
streamlit run services/dashboard/streamlit_app.py &
STREAMLIT_PID=$!

# Wait for all services to start
sleep 10

# Check if services are running
ps -p $DASHBOARD_PID > /dev/null && echo "Dashboard service is running" || echo "Dashboard service failed to start"
ps -p $PATIENT_MANAGEMENT_PID > /dev/null && echo "Patient Management service is running" || echo "Patient Management service failed to start"
ps -p $RAG_PIPELINE_PID > /dev/null && echo "RAG Pipeline service is running" || echo "RAG Pipeline service failed to start"
ps -p $MODEL_TRAINING_PID > /dev/null && echo "Model Training service is running" || echo "Model Training service failed to start"
ps -p $STREAMLIT_PID > /dev/null && echo "Streamlit dashboard is running" || echo "Streamlit dashboard failed to start"

# Keep the script running
echo "All services started. Press Ctrl+C to stop all services."
wait
