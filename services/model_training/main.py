from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tensorflow as tf
import boto3
import pandas as pd
from datetime import datetime
from services.utils.logging import setup_logging, log_event, log_error

app = FastAPI()
logger = setup_logging()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

s3 = boto3.client('s3')

@app.post("/train")
async def train_model():
    try:
        # Load preprocessed data from S3
        data = load_data_from_s3()
        
        # Split data into features and labels
        X, y = prepare_data(data)
        
        # Create and train the model
        model = create_model(input_shape=X.shape[1])
        history = model.fit(X, y, epochs=10, validation_split=0.2, callbacks=[tf.keras.callbacks.EarlyStopping(patience=3)])
        
        # Save the trained model
        model_path = f'model_{datetime.now().strftime("%Y%m%d_%H%M%S")}.h5'
        model.save(model_path)
        s3.upload_file(model_path, 'genomics-models', model_path)
        
        # Log training event
        log_event(logger, "model_training", {
            "model_path": model_path,
            "epochs": len(history.history['loss']),
            "final_loss": history.history['loss'][-1],
            "final_accuracy": history.history['accuracy'][-1]
        })
        
        return {"message": "Model trained and saved successfully", "model_path": model_path}
    except Exception as e:
        log_error(logger, str(e))
        raise HTTPException(status_code=500, detail=str(e))

def load_data_from_s3():
    # Implement data loading from S3
    # For example:
    # s3.download_file('genomics-data', 'preprocessed/latest_data.csv', 'latest_data.csv')
    # return pd.read_csv('latest_data.csv')
    pass

def prepare_data(data):
    # Split data into features and labels
    X = data.drop('target', axis=1)
    y = data['target']
    return X, y

def create_model(input_shape):
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(64, activation='relu', input_shape=(input_shape,)),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model
