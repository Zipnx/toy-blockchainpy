
from dataclasses import dataclass

# TODO: Add a penalty system at some point

@dataclass(init = True)
class Peer:
    host: str
    port: int = 1993
    
    ssl_enabled: bool = False # TODO: Fix this at some point 

    def form_url(self, endpoint) -> str:
        if len(endpoint) <= 0: endpoint = '/'

        if not endpoint[0] == '/': endpoint = '/' + endpoint

        return f'{"https" if self.ssl_enabled else "http"}://{self.host}:{self.port}{endpoint}'

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
