import json
import time
from logging import getLogger

import zmq

from cortexforge.forge.utils.sync_barrier.sync_config import SyncConfig

logger = getLogger(__name__)


class SyncBarrierServer:
    def __init__(self, cfg: SyncConfig):
        self.cfg = cfg
        self.ctx = zmq.Context.instance()

        self.rep = self.ctx.socket(zmq.REP)
        self.rep.bind(f"tcp://*:{cfg.port_reg}")
        logger.info("[SYNC][REP] bind tcp://*:%s", cfg.port_reg)

        self.pub = self.ctx.socket(zmq.PUB)
        self.pub.bind(f"tcp://*:{cfg.port_pub}")
        logger.info("[SYNC][PUB] bind tcp://*:%s", cfg.port_pub)

        self.registered = set()

    def wait_for_all(self) -> None:
        logger.info(
            "[SYNC] Waiting for %d participants...",
            self.cfg.expected_participants,
        )

        while len(self.registered) < self.cfg.expected_participants:
            raw = self.rep.recv()
            now = time.time()

            logger.info("[SYNC][REP][recv %.6f] %r", now, raw)

            data = json.loads(raw.decode("utf-8"))

            node = data.get("node")
            role = data.get("role")
            msg_type = data.get("type")

            if msg_type != "READY":
                reply = {
                    "ok": False,
                    "error": f"Unsupported message type: {msg_type}",
                }
                self.rep.send_string(json.dumps(reply))
                continue

            if not node:
                reply = {
                    "ok": False,
                    "error": "Missing node identity",
                }
                self.rep.send_string(json.dumps(reply))
                continue

            self.registered.add(node)

            logger.info(
                "[SYNC] READY from node=%s role=%s (%d/%d)",
                node,
                role,
                len(self.registered),
                self.cfg.expected_participants,
            )

            reply = {
                "ok": True,
                "registered": sorted(self.registered),
                "count": len(self.registered),
                "expected": self.cfg.expected_participants,
            }

            self.rep.send_string(json.dumps(reply))

        logger.info(
            "[SYNC] All participants ready: %s",
            sorted(self.registered),
        )

    def broadcast_go(self) -> None:
        payload = {"type": "GO"}

        logger.info("[SYNC][PUB] broadcast %s", payload)
        self.pub.send_string(json.dumps(payload))
