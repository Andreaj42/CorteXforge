import json
import time
import zmq
from logging import getLogger
from cortexforge.forge.utils.sync_barrier.sync_config import SyncConfig

logger = getLogger(__name__)


class TxBarrierClient:
    def __init__(self, cfg: SyncConfig, node_name: str):
        self.cfg = cfg
        self.node_name = node_name
        self.ctx = zmq.Context.instance()

        self.req = self.ctx.socket(zmq.REQ)
        ep_req = f"tcp://{cfg.server_host}:{cfg.port_reg}"
        self.req.connect(ep_req)
        logger.info("[TX:%s][REQ] connect %s", node_name, ep_req)

        self.sub = self.ctx.socket(zmq.SUB)
        ep_sub = f"tcp://{cfg.server_host}:{cfg.port_pub}"
        self.sub.connect(ep_sub)
        self.sub.setsockopt_string(zmq.SUBSCRIBE, "")
        logger.info("[TX:%s][SUB] connect %s + SUBSCRIBE ''", node_name, ep_sub)

    def register(self):
        msg = {"type": "HELLO", "node": self.node_name}
        self.req.send_string(json.dumps(msg))
        logger.info("[TX:%s][REQ][send %.6f] %s", self.node_name, time.time(), msg)

        rep = self.req.recv_string()
        logger.info("[TX:%s][REQ][recv %.6f] %s", self.node_name, time.time(), rep)

    def wait_broadcast(self):
        raw = self.sub.recv_string()
        logger.info("[TX:%s][SUB][recv %.6f] %s", self.node_name, time.time(), raw)
        return json.loads(raw)