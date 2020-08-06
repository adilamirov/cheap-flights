import os

IN_PRODUCTION = os.getenv("ENV_NAME", False)
SECRET_KEY = os.getenv("SECRET_KEY", "7TehVmTJG2<U0cJ3uUc]lF<HQd)esN")

# infrastructure
local_db = "postgresql://postgres:postgres@localhost:5432/flights"
DATABASE_URI = os.getenv("DATABASE_URI", local_db)

# internal configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(name)s:%(lineno)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {"local": {"class": "logging.StreamHandler", "formatter": "standard"}},
    "loggers": {
        "app": {"handlers": ["local"], "level": "INFO" if IN_PRODUCTION else "DEBUG"}
    },
}
