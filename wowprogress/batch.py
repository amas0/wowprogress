import json
import gzip
from dataclasses import dataclass
from typing import List

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


def list_files() -> List[BatchRankingLink]:
    res = requests.get(URL)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    links = get_links(soup)
    return links


def download_export(link: str) -> dict:
    res = requests.get(link)
    res.raise_for_status()
    unzipped = gzip.decompress(res.content)
    return json.loads(unzipped)


def get_export_rankings(link: BatchRankingLink) -> List[BatchRanking]:
    dl_rankings = download_export(link.export_url)
    rankings = [BatchRanking(**rank, area=link.area, realm=link.realm, tier=link.tier)
                for rank in dl_rankings]
    return rankings
