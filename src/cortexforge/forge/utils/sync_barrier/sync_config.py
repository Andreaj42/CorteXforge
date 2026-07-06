from dataclasses import dataclass


@dataclass
class SyncConfig:
    server_host: str
    port_reg: int = 5555
    port_pub: int = 5556
    expected_tx: int = 3
