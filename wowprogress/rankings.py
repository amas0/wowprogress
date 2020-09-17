import itertools as it
from typing import Generator, Optional

from . import scraping


def rankings(region: str = '', realm: str = '', tier: str = '',
             start_page: int = 0) -> Generator[scraping.Ranking, None, None]:
    for page in it.count(start_page):
        yield from scraping.get_rankings(region=region, realm=realm, tier=tier, page=page)
