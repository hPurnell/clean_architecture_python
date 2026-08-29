from dataclasses import dataclass


@dataclass
class Token:
    # Seconds since the epoch, as JWT carries them.
    exp: float
    iat: float
    sub: str
