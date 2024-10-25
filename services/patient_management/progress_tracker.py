from typing import Dict, List, Optional
import boto3
from datetime import datetime
import json
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class ProgressTracker:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('patient_progress')
        
    def add_progress_entry(self, patient_id: str, data: Dict) -> Dict:
        """Add a new progress entry for a patient"""
        try:
            timestamp = datetime.utcnow().isoformat()
            item = {
                'patient_id': patient_id,
                'timestamp': timestamp,
                'treatment': data['treatment'],
                'efficacy_score': data['efficacy_score'],
                'side_effects': data.get('side_effects', []),
                'notes': data.get('notes', ''),
                'metrics': data.get('metrics', {}),
                'next_appointment': data.get('next_appointment', '')
            }
            
            self.table.put_item(Item=item)
            
            logger.info(f"Added progress entry for patient {patient_id}")
            return item
            
        except Exception as e:
            logger.error(f"Error adding progress entry: {str(e)}")
            raise
    
    def get_patient_progress(self, patient_id: str, start_date: Optional[str] = None) -> List[Dict]:
        """Get progress history for a patient"""
        try:
            params = {
                'KeyConditionExpression': 'patient_id = :pid',
                'ExpressionAttributeValues': {':pid': patient_id}
            }
            
            if start_date:
                params['KeyConditionExpression'] += ' AND #ts >= :start'
                params['ExpressionAttributeValues'][':start'] = start_date
                params['ExpressionAttributeNames'] = {'#ts': 'timestamp'}
            
            response = self.table.query(**params)
            progress_entries = response.get('Items', [])
            
            # Sort by timestamp
            progress_entries.sort(key=lambda x: x['timestamp'])
            
            return progress_entries
            
        except Exception as e:
            logger.error(f"Error retrieving progress: {str(e)}")
            raise
    
    def update_progress_entry(self, patient_id: str, timestamp: str, updates: Dict) -> Dict:
        """Update an existing progress entry"""
        try:
            update_expr = 'SET '
            expr_attrs = {}
            expr_values = {}
            
            for key, value in updates.items():
                update_expr += f'#{key} = :{key}, '
                expr_attrs[f'#{key}'] = key
                expr_values[f':{key}'] = value
            
            update_expr = update_expr.rstrip(', ')
            
            response = self.table.update_item(
                Key={
                    'patient_id': patient_id,
                    'timestamp': timestamp
                },
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attrs,
                ExpressionAttributeValues=expr_values,
                ReturnValues='ALL_NEW'
            )
            
            return response.get('Attributes', {})
            
        except Exception as e:
            logger.error(f"Error updating progress entry: {str(e)}")
            raise
    
    def analyze_progress(self, patient_id: str) -> Dict:
        """Analyze patient's treatment progress"""
        try:
            progress_entries = self.get_patient_progress(patient_id)
            
            if not progress_entries:
                return {
                    'status': 'No progress data available',
                    'trend': None,
                    'average_efficacy': None
                }
            
            # Calculate metrics
            efficacy_scores = [entry['efficacy_score'] for entry in progress_entries]
            avg_efficacy = sum(efficacy_scores) / len(efficacy_scores)
            
            # Determine trend
            if len(efficacy_scores) >= 2:
                recent_avg = sum(efficacy_scores[-2:]) / 2
                older_avg = sum(efficacy_scores[:-2]) / (len(efficacy_scores) - 2) if len(efficacy_scores) > 2 else efficacy_scores[0]
                trend = 'improving' if recent_avg > older_avg else 'declining' if recent_avg < older_avg else 'stable'
            else:
                trend = 'insufficient data'
            
            # Analyze side effects
            side_effects_freq = {}
            for entry in progress_entries:
                for effect in entry.get('side_effects', []):
                    side_effects_freq[effect] = side_effects_freq.get(effect, 0) + 1
            
            return {
                'status': 'active',
                'trend': trend,
                'average_efficacy': avg_efficacy,
                'total_entries': len(progress_entries),
                'latest_entry': progress_entries[-1],
                'side_effects_summary': side_effects_freq,
                'treatment_duration': (
                    datetime.fromisoformat(progress_entries[-1]['timestamp']) -
                    datetime.fromisoformat(progress_entries[0]['timestamp'])
                ).days
            }
            
        except Exception as e:
            logger.error(f"Error analyzing progress: {str(e)}")
            raise
