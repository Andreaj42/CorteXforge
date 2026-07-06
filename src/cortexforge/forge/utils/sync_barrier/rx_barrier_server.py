import json
import time
import zmq
from logging import getLogger
from cortexforge.forge.utils.sync_barrier.sync_config import SyncConfig

logger = getLogger(__name__)


class RxBarrierServer:
    def __init__(self, cfg: SyncConfig):
        self.cfg = cfg
        self.ctx = zmq.Context.instance()

        self.rep = self.ctx.socket(zmq.REP)
        self.rep.bind(f"tcp://*:{cfg.port_reg}")
        logger.info("[RX][REP] bind tcp://*:%s", cfg.port_reg)

        self.pub = self.ctx.socket(zmq.PUB)
        self.pub.bind(f"tcp://*:{cfg.port_pub}")
        logger.info("[RX][PUB] bind tcp://*:%s", cfg.port_pub)

        self.registered = set()

    def wait_for_all(self):
        logger.info("[RX] Waiting for %d TX registrations...", self.cfg.expected_tx)
        while len(self.registered) < self.cfg.expected_tx:
            raw = self.rep.recv()
            now = time.time()
            logger.info("[RX][REP][recv %.6f] %r", now, raw)

            data = json.loads(raw.decode("utf-8"))
            node = data.get("node", "unknown")
            typ = data.get("type")
            logger.info("[RX] HELLO from node=%s type=%s", node, typ)

            self.registered.add(node)
            reply = {"ok": True, "registered": sorted(self.registered)}
            self.rep.send_string(json.dumps(reply))
            logger.info("[RX][REP][send %.6f] %s", time.time(), reply)

    def broadcast(self, payload: dict) -> None:
        logger.info("[RX][PUB] broadcast %s", payload)
        self.pub.send_string(json.dumps(payload))
