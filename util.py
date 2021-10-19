import json
import re

from snyk import SnykClient
from datetime import timedelta, date
from typing import Dict



def get_yesterday() -> str:
    """
    Returns the date of yesterday, as YEAR-MO-DA
    """
    delta = timedelta(days=1)
    yesterday = date.today() - delta
    return yesterday.isoformat()

def get_eight_days_ago() -> str:
    """
    Returns the date eight days from today, as YEAR-MO-DA
    """
    delta = timedelta(days=8)
    eight_days_ago = date.today() - delta
    return eight_days_ago.isoformat()

def remove_pages(path: str) -> str:
    """
    Removes the page # and page size from the query string if it is included by accident
    """
 
    path = re.sub(r'&page=(\d+)', '', path)

    path = re.sub(r'&per[Pp]age=(\d+)', '', path)

    return path


def get_snyk_pages(client: SnykClient, path: str, body: Dict, per_page:int = 250):
    """
    Returns a List or a Dict depending on the response type (issues are dict, audit events list)
    """

    path = remove_pages(path)

    path = f'{path}&perPage={per_page}'

    first_resp = client.post(f'{path}&page=1',body)
    first_query = first_resp.json()

    if isinstance(first_query, list):
        all_pages = list()
        all_pages.extend(first_query)
        next_page = 2

        while 'next' in first_resp.links:
            first_resp = client.post(f'{path}&page={next_page}', body)
            all_pages.extend(first_resp.json())
            next_page+=1

    else:
        list_resp = [l for l in first_query.keys() if isinstance(first_query[l], list)]
        all_pages = {}
        for k in list_resp:
            all_pages[k] = first_query[k]
        
        total_count = int(first_query['total'])

        all_pages['total'] = total_count

        full_pages = int(total_count / per_page)

        for next_page in range(2,full_pages+2):
            next_query = json.loads(client.post(f'{path}&page={next_page}',body).text)
            for k in list_resp:
                all_pages[k].extend(next_query[k]) 
    

    return all_pages