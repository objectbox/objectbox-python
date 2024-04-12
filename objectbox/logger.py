import sys
import logging

logger = logging.getLogger("objectbox")


def setup_stdout_logger():
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    # Output format example:
    # 2024-04-04 10:16:46,272 [objectbox-py] [DEBUG] Creating property "id" (ID=1, UID=1001)
    formatter = logging.Formatter('%(asctime)s [objectbox-py] [%(levelname)-5s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# Not need to hook stdout as pytest will do the job. Use --log-cli-level= to set log level
# setup_stdout_logger()
