import httpx
import json

from pathlib import Path

class ModrinthAPI:
    # Modrinth API endpoints
    VERSION_ENDPOINT = "/project/{slug}/version"

    # Base URL for the Modrinth API and User-Agent header
    BASE_URL = "https://api.modrinth.com/v2"
    USER_AGENT = "juyens/mcnet (joseph.juliuscb@gmail.com)"

    def __init__(self):
        self.client = httpx.Client(
            headers={"User-Agent": self.USER_AGENT},
            follow_redirects=True,
        )
    
    def get_versions(self, slug: str, loaders: list, game_versions: list):
        url = f"{self.BASE_URL}/project/{slug}/version"
        params = {
            "loaders": json.dumps(loaders),
            "game_versions": json.dumps(game_versions)
        }
        response = self.client.get(url, params=params)
        return response.json()
    
    