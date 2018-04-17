import requests
from urllib.parse import urlencode
from pyquery import PyQuery as pq
from pymongo import MongoClient
import time

base_url = 'https://m.weibo.cn/api/container/getIndex?'
headers = {
    'Host': 'm.weibo.cn',
    'Referer': 'https://m.weibo.cn/u/5708857943',
    'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}
client = MongoClient()
db = client['weibo']
collection = db['dagujijr']
max_page = 58


def get_page(page):
    params = {
        'type': 'uid',
        'value': '5708857943',
        'containerid': '1076035708857943',
        'page': page
    }
    url = base_url + urlencode(params)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
    except requests.ConnectionError as e:
        print('Error', e.args)


def get_long_text(weibo_id):
    text_url = "https://m.weibo.cn/statuses/extend?id="+weibo_id
    text_headers = {
        #'Cookie': 'put your cookie here',
        'Host': 'm.weibo.cn',
        'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
        'Referer': 'https://m.weibo.cn/status/' + weibo_id,
        'X-Requested-With': 'XMLHttpRequest',
    }
    r_long = requests.get(text_url, headers=text_headers)
    json_long = r_long.json()
    data = json_long.get('data')
    long_text = pq(data.get('longTextContent')).text()
    return long_text


def parse_page(json):
    if json:
        items = json.get('data').get('cards')
        for item in items:
            item = item.get('mblog')
            if not item.get('raw_text'):
                if not item.get('page_info'):
                    weibo = {}
                    weibo['created_at'] = item.get('created_at')
                    weibo['id'] = item.get('id')
                    if item.get('isLongText'):
                        weibo_id = item.get('id')
                        weibo['text'] = get_long_text(weibo_id)
                    else:
                        weibo['text'] = pq(item.get('text')).text()
                    weibo['attitudes'] = item.get('attitudes_count')
                    weibo['comments'] = item.get('comments_count')
                    weibo['reposts'] = item.get('reposts_count')
                    yield weibo


def save_to_mongo(result):
    collection.insert(result)


if __name__ == '__main__':
    for page in range(2, max_page + 1):
        json = get_page(page)
        print(page)
        results = parse_page(json)
        for result in results:
            save_to_mongo(result)
        time.sleep(1)
