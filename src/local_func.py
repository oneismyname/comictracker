import requests


def take_data(start_day, end_day):
    headers = {
                'authority': 'pb.tana.moe',
                'accept': '*/*',
                'accept-language': 'en-US',
                'content-type': 'application/json',
                'origin': 'https://tana.moe',
                'referer': 'https://tana.moe/',
                'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            }

    params = {
        'page': '1',
        'perPage': '500',
        'skipTotal': '1',
        'filter': f"publishDate >= '{start_day}' && publishDate <= '{end_day}'",
        'sort': '+publishDate,+name,-edition',
        'expand': 'title, publisher',
    }

    response = requests.get('https://pb.tana.moe/api/collections/book_detailed/records', params=params,
                            headers=headers)
    data_test = response.json()
    return data_test


