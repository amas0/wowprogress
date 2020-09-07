from dataclasses import dataclass
from typing import List

import bs4
import requests

URL = 'https://www.wowprogress.com'


@dataclass
class Ranking:
    rank: int
    guild: str
    realm: str
    progress: str

    @classmethod
    def from_row(cls, row: bs4.element.Tag):
        cols = row.find_all('td')
        rank = int(cols[0].text.strip())
        guild = cols[1].text.strip()
        realm = cols[2].text.strip()
        progress = cols[3].text.split('\n')[0].strip()
        return cls(rank, guild, realm, progress)


def get_rankings_page(region='world', realm=None, page: int = 0) -> requests.Response:
    if region == 'world':
        endpoint = f'{URL}/pve/rating'
    else:
        if realm:
            endpoint = f'{URL}/pve/{region}/{realm}/rating'
        else:
            endpoint = f'{URL}/pve/{region}/rating'
    if page > 0:
        endpoint = f'{endpoint}/next/{page-1}/rating'
    response = requests.get(endpoint)
    return response


def get_rankings_page_html(response: requests.Response) -> str:
    response.raise_for_status()
    return response.text


def get_rankings_table(html: str) -> bs4.element.Tag:
    soup = bs4.BeautifulSoup(html, 'html.parser')
    table = soup.find('table', {'class': 'rating'})
    return table


def get_rankings_from_table(table: bs4.element.Tag) -> List[Ranking]:
    header, *rows = table.find_all('tr')
    rankings = [Ranking.from_row(row) for row in rows]
    return rankings


def get_rankings(region='world', realm=None, page: int = 0):
    res = get_rankings_page(region=region, realm=realm, page=page)
    html = get_rankings_page_html(res)
    table = get_rankings_table(html)
    rankings = get_rankings_from_table(table)
    return rankings