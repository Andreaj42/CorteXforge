"""Get node name identity."""

from socket import gethostname


def get_node_name(logger=None) -> str:
    try:
        hostname = gethostname()
        return hostname
    except Exception as e:
        logger.error(f"Error getting hostname: {e}")
        return "unknown"
