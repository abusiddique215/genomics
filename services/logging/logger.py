import logging
import watchtower
import boto3
from botocore.exceptions import ClientError
import os

def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Always add a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    try:
        # Attempt to set up CloudWatch handler
        cloudwatch_handler = watchtower.CloudWatchLogHandler(
            log_group='GenomicsTreatmentAPI',
            stream_name='ApplicationLogs',
            use_queues=False,
            create_log_group=True,
            boto3_client=boto3.client('logs', region_name=os.getenv('AWS_DEFAULT_REGION'))
        )
        logger.addHandler(cloudwatch_handler)
        logger.info("CloudWatch logging setup successful")
    except Exception as e:
        logger.error(f"Failed to set up CloudWatch logging: {str(e)}")
        logger.warning("Continuing with console logging only")

    return logger

def log_event(logger, event_type, event_data):
    logger.info({
        'event_type': event_type,
        'data': event_data
    })

def log_error(logger, error_message):
    logger.error({
        'event_type': 'error',
        'message': error_message
    })