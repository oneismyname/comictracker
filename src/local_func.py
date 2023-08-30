
import requests

headers = {
    'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
    'Content-Type': 'application/json',
    'Referer': 'https://tana.moe/',
    'Accept-Language': 'en-US',
    'sec-ch-ua-mobile': '?1',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
    'sec-ch-ua-platform': '"Android"',
}

params = {
    'page': '1',
    'perPage': '500',
    'skipTotal': '1',
    'filter': "publishDate >= '2022-10-01' && publishDate <= '2022-10-31'",
    'sort': '+publishDate,+name,-edition',
    'expand': 'title, publisher',
}

response = requests.get('https://pb.tana.moe/api/collections/book_detailed/records', params=params, headers=headers)

