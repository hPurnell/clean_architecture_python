from dataclasses import dataclass


@dataclass
class User:
    id: str
    name: str
    username: str
    # The hash, never the password. Nothing in the application stores or
    # compares a plaintext password; the credential a caller sends is checked
    # against this by an AbstractPasswordService and then forgotten.
    password_hash: str
