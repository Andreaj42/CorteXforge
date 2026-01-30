"""Get node name identity."""

from socket import gethostname
from logging import getLogger

logger = getLogger(__name__)


def get_node_name() -> str:
    try:
        hostname = gethostname()
        return hostname
    except Exception as e:
        logger.error(f"Error getting hostname: {e}")
        return "unknown"
