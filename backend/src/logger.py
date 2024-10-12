import logging


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Create a logger
    logger = logging.getLogger(__name__)

    return logger


# Create a global logger instance
logger = setup_logging()
