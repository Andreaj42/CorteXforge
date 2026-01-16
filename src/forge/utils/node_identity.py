import socket

def get_node_name(logger=None) -> str:
    try:
        hostname = socket.gethostname()
        return hostname
    except Exception as e:
        logger.error(f"Error getting hostname: {e}")
        return "unknown"
