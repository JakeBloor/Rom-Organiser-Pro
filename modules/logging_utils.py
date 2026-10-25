import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Set up file logger
log_file = os.path.join(LOGS_DIR, f'rom_organiser_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Log level icons
LOG_ICONS = {
    'INFO': 'ℹ️',
    'WARNING': '⚠️',
    'ERROR': '❌',
    'DEBUG': '🐛',
    'SUCCESS': '✅'
}


class AppLogger:
    """Logger wrapper that stores messages in memory for web interface"""

    # The log file keeps everything; memory only holds the most recent lines
    MAX_MESSAGES = 5000

    def __init__(self):
        self.messages = []

    def log(self, message, level='INFO'):
        """Log message to file, console, and memory"""
        icon = LOG_ICONS.get(level, '📝')
        formatted_message = f"{icon} {message}"
        self.messages.append(formatted_message)
        if len(self.messages) > self.MAX_MESSAGES:
            del self.messages[:-self.MAX_MESSAGES]

        if level == 'INFO':
            logger.info(message)
        elif level == 'WARNING':
            logger.warning(message)
        elif level == 'ERROR':
            logger.error(message)
        elif level == 'DEBUG':
            logger.debug(message)
        elif level == 'SUCCESS':
            logger.info(message)
        else:
            logger.info(message)

    def info(self, message):
        self.log(message, 'INFO')

    def warning(self, message):
        self.log(message, 'WARNING')

    def error(self, message):
        self.log(message, 'ERROR')

    def debug(self, message):
        self.log(message, 'DEBUG')

    def success(self, message):
        self.log(message, 'SUCCESS')

    def clear(self):
        """Clear in-memory messages"""
        self.messages = []

    def get_messages(self):
        """Get all logged messages"""
        return self.messages