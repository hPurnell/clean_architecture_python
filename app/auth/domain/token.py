from dataclasses import dataclass


@dataclass
class Token:
    # Seconds since the epoch, as JWT carries them.
    exp: float
    iat: float
    sub: str
    # The role values, as JWT carries them: a token that predates this claim is
    # not one this service will accept.
    roles: list[str]
