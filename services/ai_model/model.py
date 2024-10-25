import tensorflow as tf
import numpy as np
from typing import Dict, List, Tuple
import logging
import json

logger = logging.getLogger(__name__)

class GenomicsTreatmentModel:
    def __init__(self):
        self.model = self._build_model()
        
    def _build_model(self) -> tf.keras.Model:
        """Build and compile the TensorFlow model"""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(128, activation='relu', input_shape=(20,)),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(3, activation='softmax')  # 3 treatment options
        ])
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        return model
    
    def preprocess_data(self, genomic_data: Dict, medical_history: Dict) -> np.ndarray:
        """Convert genomic and medical data into model input format"""
        try:
            # Extract features from genomic data
            genomic_features = self._extract_genomic_features(genomic_data)
            
            # Extract features from medical history
            medical_features = self._extract_medical_features(medical_history)
            
            # Combine features
            combined_features = np.concatenate([genomic_features, medical_features])
            
            # Pad or truncate to expected input size (20)
            if len(combined_features) < 20:
                combined_features = np.pad(combined_features, (0, 20 - len(combined_features)))
            else:
                combined_features = combined_features[:20]
                
            return combined_features.reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Error preprocessing data: {str(e)}")
            raise
    
    def _extract_genomic_features(self, genomic_data: Dict) -> np.ndarray:
        """Extract numerical features from genomic data"""
        features = []
        for value in genomic_data.values():
            if isinstance(value, (int, float)):
                features.append(value)
            elif isinstance(value, str):
                # Convert categorical values to numerical
                features.append(hash(value) % 10)  # Simple hash-based encoding
        return np.array(features, dtype=np.float32)
    
    def _extract_medical_features(self, medical_history: Dict) -> np.ndarray:
        """Extract numerical features from medical history"""
        features = []
        for value in medical_history.values():
            if isinstance(value, (int, float)):
                features.append(value)
            elif isinstance(value, str):
                features.append(hash(value) % 10)
        return np.array(features, dtype=np.float32)
    
    def predict_treatment(self, input_data: np.ndarray) -> Tuple[str, float]:
        """Predict treatment and efficacy"""
        try:
            predictions = self.model.predict(input_data)
            treatment_idx = np.argmax(predictions[0])
            efficacy = float(predictions[0][treatment_idx])
            
            treatments = ['Treatment A', 'Treatment B', 'Treatment C']
            recommended_treatment = treatments[treatment_idx]
            
            return recommended_treatment, efficacy
            
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            raise
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, epochs: int = 10):
        """Train the model"""
        try:
            history = self.model.fit(
                X_train, y_train,
                epochs=epochs,
                validation_split=0.2,
                verbose=1
            )
            return history
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise
