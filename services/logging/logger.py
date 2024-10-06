import logging
import watchtower
import boto3
from botocore.exceptions import ClientError

# Set up CloudWatch logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    # Attempt to set up CloudWatch handler
    cloudwatch_handler = watchtower.CloudWatchLogHandler(
        log_group='GenomicsTreatmentAPI',
        stream_name='ApplicationLogs',
        boto3_session=boto3.Session()
    )
    logger.addHandler(cloudwatch_handler)
except ClientError as e:
    # Fall back to console logging if CloudWatch setup fails
    console_handler = logging.StreamHandler()
    logger.addHandler(console_handler)
    logger.error(f"Failed to set up CloudWatch logging: {str(e)}")

def log_event(event_type, event_data):
    logger.info({
        'event_type': event_type,
        'data': event_data
    })

def log_error(error_message):
    logger.error({
        'event_type': 'error',
        'message': error_message
    })