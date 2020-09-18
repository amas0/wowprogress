# wowprogress

This Python library provides an interface for downloading structured data on WoW raid rankings
from https://wowprogress.com.

_This library is very much in development and as such the interfaces and structure will change
significantly._

## Installation

```
git clone https://github.com/amas0/wowprogress.git
pip install ./wowprogress
```

## Example usage

This library provides two different interfaces for pulling data: from
[batch exports](https://wowprogress.com/export/ranks/) or scraped from the UI. Utilizing
batch exports is more efficient and preferred, but only provides limited data compared to
the UI. Scraping from the UI will allow more detailed information, but it is not at all
appropriate for pulling large datasets as each page only call only returns ~20 results.

#### Batch rankings

Here we'll show basic querying of rankings that returns `BatchRanking` objects.

```python
import wowprogress

us_illidan_rankings_tier_25 = wowprogress.batch.get_export_rankings(area='us', realm='illidan', tier=25)
print(next(us_illidan_rankings_tier_25))
# BatchRanking(score=7500000, world_rank=2, area_rank=1, realm_rank=1, name='Complexity Limit', url='https://www.wowprogress.com/guild/us/illidan/Complexity+Limit/rating.tier25', area='us', realm='illidan', tier=25)
```

Perhaps a more useful workflow for analysis purposes is to pull this data into a `pandas` dataframe:

```python
import pandas as pd
import wowprogress

us_illidan_rankings_tier_25 = wowprogress.batch.get_export_rankings(area='us', realm='illidan', tier=25, as_dict=True)
df = pd.DataFrame(us_illidan_rankings_tier_25)
```

For clarity, the rankings are structured by the following data class:

```python
from dataclasses import dataclass

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
```

Batch exports are organized into files separated by area + realm + tier, which is why those are provided
as explicit filtering operations in the `get_export_rankings` function. We can provide fully custom querying
of these files with a little extra effort.

In `wowprogress.batch` we define the following dataclass:

```python
from dataclasses import dataclass

@dataclass
class BatchRankingLink:
    area: str
    realm: str
    tier: int
    export_url: str
```

The `get_export_rankings` function takes a `filter_fn` argument to define a predicate on these objects.
See the below where we pull all US-Illidan rankings from tier 23 onwards.

```python
import pandas as pd
import wowprogress

def my_filter(link: wowprogress.batch.BatchRankingLink):
    return (link.area == 'us') and (link.realm == 'illidan') and (link.tier >= 23)

us_illidan_t23_present = wowprogress.batch.get_export_rankings(filter_fn=my_filter, as_dict=True)
df = pd.DataFrame(us_illidan_t23_present)
```

_Note: because each realm is in a different file, if you want to do area-wide rankings, such as 
looking at the top 1000 ranked guilds in the EU, you'll need to pull ALL the EU data and then 
filter after the fact._

#### Scraped rankings

Scraped rankings are less developed and less efficient but give more detailed progress info. For
example:

```python
import itertools as it
from pprint import pprint

import wowprogress

us_guilds = wowprogress.scraping.get_rankings(area='us')  # Omitting tier defaults to most recent tier
top_5_us = it.islice(us_guilds, 5)

pprint(list(top_5_us))

# [Ranking(rank=1, guild='Complexity Limit', realm='US-Illidan', progress='12/12 (M)'),
# Ranking(rank=2, guild='BDGG', realm='US-Illidan', progress='12/12 (M)'),
# Ranking(rank=3, guild='Honestly', realm='OC-Frostmourne', progress='12/12 (M)'),
# Ranking(rank=4, guild='Ethical (r)', realm='OC-Frostmourne', progress='12/12 (M)'),
# Ranking(rank=5, guild='Midwinter', realm='US-Area 52', progress='12/12 (M)')]
```

The dataclass that structures the scraped rankings is given by:

```python
from dataclasses import dataclass

@dataclass
class Ranking:
    rank: int
    guild: str
    realm: str
    progress: str
```