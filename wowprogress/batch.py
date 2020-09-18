import json
import gzip
import itertools as it
from dataclasses import dataclass
from typing import Callable, Dict, Generator, List, Optional, Union

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
    """Parse html of export list page for available links.

    Filters out non-gzipped links and properly links to be absolute URLs

    Args:
        soup: BeautifulSoup object of export page
    Returns:
        List of BatchRankingLinks available for download
    """
    links = soup.find_all('a')
    links = [link.attrs.get('href') for link in links]
    urls = [f'{URL}{link}' for link in links if link.endswith('gz')]
    return [BatchRankingLink.from_url(url) for url in urls]


def list_files(session: Optional[requests.Session] = None) -> List[BatchRankingLink]:
    """List available export files for download as BatchRankingLinks

    Args:
        session: Optionally provide an existing requests session. When doing multiple requests,
            this is highly recommended.
    Returns:
        List of BatchRankingLinks available for download
    """
    res = session.get(URL) if session else requests.get(URL)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    links = get_links(soup)
    return links


def download_export(link: str, session: Optional[requests.Session] = None) -> dict:
    """Downloads gzipped-json file and returns a dict

    Args:
        link: url to gzipped json
        session: Optionally provide an existing requests session. When doing multiple requests,
            this is highly recommended.
    Returns:
        dict representation of json
    """
    res = session.get(link) if session else requests.get(link)
    res.raise_for_status()
    unzipped = gzip.decompress(res.content)
    return json.loads(unzipped)


def get_export_rankings_from_link(link: BatchRankingLink,
                                  session: Optional[requests.Session] = None) -> Generator[BatchRanking, None, None]:
    """Downloads and yields rankings from a given export link

    Args:
        link: BatchRankingLink to download
        session: Optionally provide an existing requests session. When doing multiple requests,
            this is highly recommended.
    Yields:
        BatchRankings from the downloaded export
    """
    dl_rankings = download_export(link.export_url, session=session)
    rankings = (BatchRanking(**rank, area=link.area, realm=link.realm, tier=link.tier)
                for rank in dl_rankings)
    yield from rankings


def get_export_rankings(area: str = '', realm: str = '', tier: int = 0,
                        filter_fn: Callable[[BatchRankingLink], bool] = None,
                        as_dict: bool = False) -> Generator[Union[BatchRanking, Dict], None, None]:
    """Downloads, filters, and structures WoWProgress export rankings

    WoWProgress provides bulk downloads of their rankings via https://wowprogress.com/export/ranks
    This is the most efficient means of pulling bulk data, but is limited due to only a few tiers
    being available.

    Args:
        area: area or region to filter for rankings, e.g. us, eu. Defaults to
            empty string which is no filter
        realm: realm to filter for rankings. Defaults to empty string which is no filter
        tier: tier to pull rankings for, defaults to zero which is no filter
        filter_fn: function that allows for complex filtering on BatchRankingLink attributes
            for example:
                filter_fn = lambda l: (l.area == 'us') and (l.tier >= 25)

            will return all US rankings from tier 25 and later.

            Providing this overrides previous area, realm, and tier args.
        as_dict: returns results as dicts instead of BatchRanking objects. Defaults to False
    Yields:
        rankings that fit the filter criteria, either BatchRanking or dicts determined by as_dict
    """
    if filter_fn is None:
        def filter_fn(link):
            return (((area == '') or (link.area == area)) and
                    ((realm == '') or (link.realm == realm)) and
                    ((tier == 0) or (link.tier == tier)))
    with requests.Session() as session:
        to_download = [link for link in list_files(session) if filter_fn(link)]
        rankings = (get_export_rankings_from_link(link, session) for link in to_download)
        yield from (ranking.to_dict() if as_dict else ranking for ranking in it.chain(*rankings))
