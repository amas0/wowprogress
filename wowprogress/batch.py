import json
import gzip
from dataclasses import dataclass
from typing import List

import bs4
import requests

URL = 'https://wowprogress.com/export/ranks/'


@dataclass
class Ranking:
    score: int
    world_rank: int
    area_rank: int
    realm_rank: int
    name: str
    url: str
    region: str
    area: str
    tier: int

    def to_dict(self):
        return {'score': self.score, 'world_rank': self.world_rank,
                'area_rank': self.area_rank, 'realm_rank': self.realm_rank,
                'name': self.name, 'url': self.url, 'region': self.region,
                'area': self.area, 'tier': self.tier}


def get_links(soup: bs4.BeautifulSoup) -> List[str]:
    links = soup.find_all('a')
    links = [link.attrs.get('href') for link in links]
    return [f'{URL}{link}' for link in links if link.endswith('gz')]


def list_files() -> List[str]:
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


def get_export_metadata(link: str) -> dict:
    file_name = link.split('/')[-1]
    file_name = file_name.rstrip('.json.gz')
    region, area, tierstr = file_name.split('_')
    tier = int(tierstr.lstrip('tier'))
    return {'region': region, 'area': area, 'tier': tier}


def get_export_rankings(link: str) -> List[Ranking]:
    em = get_export_metadata(link)
    dl_rankings = download_export(link)
    rankings = [Ranking(**rank, **em) for rank in dl_rankings]
    return rankings
