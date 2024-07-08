
from dataclasses import dataclass

@dataclass(init = True)
class Peer:
    host: str
    port: int = 1993

    def to_json(self) -> dict:
        return {
            'host': self.host,
            'port': self.port
        }

    @staticmethod
    def from_json(json_data: dict):

        params = ['host', 'port']

        for param in params:
            if param not in json_data:
                return None
        
        if not json_data['port'].isdigit(): return None

        return Peer(
            host = json_data['host'],
            port = int(json_data['port'])
        )
