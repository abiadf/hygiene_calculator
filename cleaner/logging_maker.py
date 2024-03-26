
import logging

'''Setup logging'''

logger = logging.getLogger()
logger.handlers = []

# Set the desired log level
logger.setLevel(logging.DEBUG)

# Create a console handler and set its log level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create a formatter and set it on the console handler
formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(formatter)

# Add the console handler to the logger
logger.addHandler(console_handler)
