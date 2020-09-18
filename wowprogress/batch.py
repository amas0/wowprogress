import json
import gzip
import itertools as it
from dataclasses import dataclass
from typing import Callable, Generator, List, Optional

import bs4
import requests

URL = 'https://wowprogress.com/export/ranks/'


@dataclass
class BatchRankingLink:
    area: str
    realm: str
    tier: int
    export_url: str

    @classmethod
    def from_url(cls, url: str):
        file_name = url.split('/')[-1]
        file_name = file_name.rstrip('.json.gz')
        area, realm, tier_str = file_name.split('_')
        tier = int(tier_str.lstrip('tier'))
        return cls(area=area, realm=realm, tier=tier, export_url=url)


@dataclass
class BatchRanking:
    score: int
    world_rank: int
    area_rank: int
    realm_rank: int
    name: str
    url: str
    area: str
    realm: str
    tier: int

    def to_dict(self):
        return {'score': self.score, 'world_rank': self.world_rank,
                'area_rank': self.area_rank, 'realm_rank': self.realm_rank,
                'name': self.name, 'url': self.url, 'area': self.area,
                'realm': self.realm, 'tier': self.tier}


def get_links(soup: bs4.BeautifulSoup) -> List[BatchRankingLink]:
    links = soup.find_all('a')
    links = [link.attrs.get('href') for link in links]
    urls = [f'{URL}{link}' for link in links if link.endswith('gz')]
    return [BatchRankingLink.from_url(url) for url in urls]


def list_files(session: Optional[requests.Session] = None) -> List[BatchRankingLink]:
    res = session.get(URL) if session else requests.get(URL)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    links = get_links(soup)
    return links


def download_export(link: str, session: Optional[requests.Session] = None) -> dict:
    res = session.get(link) if session else requests.get(link)
    res.raise_for_status()
    unzipped = gzip.decompress(res.content)
    return json.loads(unzipped)


def get_export_rankings_from_link(link: BatchRankingLink,
                                  session: Optional[requests.Session] = None) -> Generator[BatchRanking, None, None]:
    dl_rankings = download_export(link.export_url, session=session)
    rankings = (BatchRanking(**rank, area=link.area, realm=link.realm, tier=link.tier)
                for rank in dl_rankings)
    yield from rankings


def get_export_rankings(area: str = '', realm: str = '', tier: int = 0,
                        filter_fn: Callable[[BatchRankingLink], bool] = None):
    if filter_fn is None:
        def filter_fn(link):
            return (((area == '') or (link.area == area)) and
                    ((realm == '') or (link.realm == realm)) and
                    ((tier == 0) or (link.tier == tier)))
    with requests.Session() as session:
        to_download = [link for link in list_files(session) if filter_fn(link)]
        rankings = (get_export_rankings_from_link(link, session) for link in to_download)
        yield from it.chain(*rankings)
