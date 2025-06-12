import json
from dataclasses import dataclass

@dataclass
class Connection:
    host: str
    port: int
    username: str
    password: str
    database: str

def load(name: str) -> Connection:
    with open("connections.json") as f:
        content: dict = json.loads(f.read())
    
    if name not in content:
        raise KeyError(f"connection named '{name}' does not exist")

    return Connection(**content[name])
    