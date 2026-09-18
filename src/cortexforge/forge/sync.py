from logging import getLogger

from cortexforge.forge.utils.sync_barrier.sync_barrier_server import (
    SyncBarrierServer,
)
from cortexforge.forge.utils.sync_barrier.sync_config import SyncConfig

logger = getLogger(__name__)


def main(args) -> None:
    logger.info(
        "Starting synchronization coordinator for %d participants",
        args.expected_participants,
    )

    cfg = SyncConfig(
        server_host="0.0.0.0",
        port_reg=5555,
        port_pub=5556,
        expected_participants=args.expected_participants,
    )

    barrier = SyncBarrierServer(cfg)

    barrier.wait_for_all()

    logger.info("All participants registered. Releasing barrier.")

    barrier.broadcast_go()

    logger.info("Synchronization GO sent.")
