import logging

logger = logging.getLogger(__name__)

def daily_heartbeat():
    logger.info("Daily scheduled job ran successfully.")