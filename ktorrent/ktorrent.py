import json

import requests
from bs4 import BeautifulSoup

# Base search link
BASE_LINK = 'https://kat.cr'


class Status:
    """Result status"""
    BADREQUEST = '{"status" : 400}'
    NOTFOUND = '{"status" : 404}'
    TIMEOUT = '{"status" : 408}'


class Filter:
    """Keys and Args Filter"""
    # Torrent result keys
    KEYS = ['name', 'web', 'link', 'magnet', 'verified', 'category', 'size',
            'files', 'age', 'seed', 'leech']
    # Function args
    FIELD = {
        'size': 'size',
        'files': 'files_count',
        'age': 'time_add',
        'seed': 'seeders',
        'leech': 'leechers'
    }
    SORDER = ['asc', 'desc']
    CATEGORY = ['all', 'movies', 'tv', 'anime', 'music', 'books',
                'applications', 'games', 'other', 'xxx']


def request(url):
    """Generate request result"""

    try:
        response = requests.get(url)
    except:
        return Status.TIMEOUT

    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.select('[id^=torrent_]')
    rows_found = len(rows)

    if rows_found > 0:
        result = []
        for row in rows:
            cols = row.find_all('td')
            links = cols[0].select('.iaconbox a')   # All related links

            # Extracting Torrent information
            name = (cols[0].select('.cellMainLink'))[0].text
            web = BASE_LINK + (cols[0].select('.cellMainLink'))[0].get('href')
            link = 'http:' + links[-1].get('href')
            magnet = links[-2].get('href')
            category = (cols[0].select('[id^=cat_]'))[0].text
            # Check if verified
            verified = '0'    # False
            if len(links) >= 3:
                if links[-3].get('title') == "Verified Torrent":
                    verified = '1'

            row_data = [name, web, link, magnet, verified, category]

            for i in range(1, 6):
                row_data.append(cols[i].text.strip())

            # Zip keys with values
            row_data = dict(zip(Filter.KEYS, list(
                (x.replace(u'\xa0', u' ')) for x in row_data)))

            # Append current torrent to results
            result.append(row_data)

        # Calculate total pages
        pager = soup.select('.pages a')
        total_pages = 1 if len(pager) == 0 else int(pager[- 1].text)

        # find page number
        page = url.split('/')
        if page[-1].isdigit():
            page = page[-1]
        else:
            page = page[-2]

        data = {
            'status': 200,
            'meta': {
                'pageCurrent': int(page),
                'pageResult': rows_found,
                'pageTotal': total_pages
            },
            'torrent': result
        }
    else:
        return Status.NOTFOUND

    return json.dumps(data, sort_keys=True)


def top(**args):
    """Top torrents category wise"""

    category = args.get('category')
    page = args.get('page', 1)

    # Validating args
    if category not in Filter.CATEGORY or category == 'all' \
            or (not isinstance(page, int)):
        return Status.BADREQUEST

    # Generate final link
    url = BASE_LINK + '/' + category + '/' + str(page)

    return request(url)


def search(**args):
    """Do a search"""

    search = args.get('search', '')
    strict = args.get('strict', 0)
    safe = args.get('safe', 0)
    verified = args.get('verified', 0)
    subtract = args.get('subtract', '')
    user = args.get('user', '')
    category = args.get('category', 'all')
    field = args.get('field', 'seed')
    sorder = args.get('sorder', 'desc')
    page = args.get('page', 1)

    # Validating args
    if search == '' \
            or strict not in range(-1, 2) \
            or safe not in range(0, 2) \
            or verified not in range(0, 2) \
            or category not in Filter.CATEGORY \
            or field not in Filter.FIELD.keys() \
            or sorder not in Filter.SORDER \
            or (not isinstance(page, int)):
        return Status.BADREQUEST

    # Generate search query
    if strict == -1:
        search_query = search.replace(" ", " OR ")
    elif strict == 1:
        search_query = '"' + search + '"'
    else:
        search_query = search

    search_query += ' category:' + category

    search_query += ' is_safe:1' if safe == 1 else ''

    search_query += ' verified:1' if verified == 1 else ''

    search_query += ' user:' + user if user != '' else ''

    if subtract != '':
        search_query += ' -' + ' -'.join(subtract.split())

    # Generate final link
    url = BASE_LINK + '/usearch/' + search_query + '/' + \
        str(page) + '/?field=' + Filter.FIELD[field] + '&sorder=' + sorder

    return request(url)
