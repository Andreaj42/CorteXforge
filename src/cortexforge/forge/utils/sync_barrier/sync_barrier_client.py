import json
import time
from logging import getLogger

import zmq

from cortexforge.forge.utils.sync_barrier.sync_config import SyncConfig

logger = getLogger(__name__)


class SyncBarrierClient:
    def __init__(
        self,
        cfg: SyncConfig,
        node_name: str,
        role: str,
    ):
        self.cfg = cfg
        self.node_name = node_name
        self.role = role
        self.ctx = zmq.Context.instance()

        self.req = self.ctx.socket(zmq.REQ)
        ep_req = f"tcp://{cfg.server_host}:{cfg.port_reg}"
        self.req.connect(ep_req)

        logger.info(
            "[%s:%s][REQ] connect %s",
            role.upper(),
            node_name,
            ep_req,
        )

        self.sub = self.ctx.socket(zmq.SUB)
        ep_sub = f"tcp://{cfg.server_host}:{cfg.port_pub}"
        self.sub.connect(ep_sub)
        self.sub.setsockopt_string(zmq.SUBSCRIBE, "")

        logger.info(
            "[%s:%s][SUB] connect %s",
            role.upper(),
            node_name,
            ep_sub,
        )

    def register(self) -> None:
        msg = {
            "type": "READY",
            "node": self.node_name,
            "role": self.role,
        }

        self.req.send_string(json.dumps(msg))

        logger.info(
            "[%s:%s][REQ][send %.6f] %s",
            self.role.upper(),
            self.node_name,
            time.time(),
            msg,
        )

        rep = self.req.recv_string()

        logger.info(
            "[%s:%s][REQ][recv %.6f] %s",
            self.role.upper(),
            self.node_name,
            time.time(),
            rep,
        )

    def wait_go(self) -> None:
        raw = self.sub.recv_string()

        logger.info(
            "[%s:%s][SUB][recv %.6f] %s",
            self.role.upper(),
            self.node_name,
            time.time(),
            raw,
        )

        msg = json.loads(raw)

        if msg.get("type") != "GO":
            raise RuntimeError(f"Expected GO message, received: {msg}")
