import json
from dataclasses import dataclass

@dataclass
class ConfigEntry:
    username: str
    password: str
    host: str
    port: int

@dataclass
class Grid:
    column: int
    row: int

@dataclass
class Config:
    grid: Grid
    cameras: list[ConfigEntry]

def load() -> Config:
    cameras = []
    with open('config.json') as f:
        content = f.read()
    config = json.loads(content)
    for entry in config['cameras']:
        entry = ConfigEntry(entry['username'], entry['password'], entry['host'], entry['port']) 
        cameras.append(entry)
    
    grid = Grid(config['grid']['column'], config['grid']['row'])
    return Config(grid, cameras)

def get_entry_by_host(host: str) -> ConfigEntry | None:
    for entry in load().cameras:
        if entry.host == host:
            return entry
    return None