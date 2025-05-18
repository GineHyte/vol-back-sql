from logging import basicConfig, getLogger, INFO, DEBUG, ERROR

logger = getLogger("intern")

def init_logging(app):
    # Set SQLAlchemy logger levels here
    # SQL statements are typically logged by sqlalchemy.engine at INFO level.
    # Setting it to ERROR will suppress them.
    logger.setLevel(DEBUG)
    
    logger.debug("Logger initialized")
