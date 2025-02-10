from logging import basicConfig, getLogger

import logfire

logger = getLogger("intern")


def init_logfire(app):
    logfire.configure()
    logfire.instrument_fastapi(app)
    basicConfig(handlers=[logfire.LogfireLoggingHandler()])

    logger.debug("Logger initialized")
