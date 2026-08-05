from typing import TypedDict


class GameVersionResource(TypedDict):
    version: str
    version_type: str
    # format: ISO-8601
    date: str
    major: bool
