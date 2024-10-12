from dataclasses import dataclass


@dataclass
class Data:
    payload: bytes
    flags: int
    expiration_time: int
    size: int
