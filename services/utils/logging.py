import logging

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add the console handler to the logger
    logger.addHandler(console_handler)
    
    return logger

# You can add more logging functions here if needed
