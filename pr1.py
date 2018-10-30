import urllib.request
import urllib.error
import re
from queue import Queue
from pprint import pprint
import csv
import sys


def find_urls(html: str):
    v1 = r'href=[\'"]?(?!/)([^\'" >]+)'
    regex = r'a href\s?=\s?[\'"]?(?![\W(mailto:)])([^\'" >]+)'
    for new_url in re.findall(regex, html):
        if re.search('\.', new_url):
            if re.search('\.html', new_url) and re.search('/', new_url):
                url_queue.put(new_url)
                visited[url].append(new_url)
            elif not re.search('\.html', new_url) and not re.search('javascript:', new_url):
                url_queue.put(new_url)
                visited[url].append(new_url)


visited = {}
url_queue = Queue(maxsize=0)
for url in open('urls3.txt', 'r'):
    url = url.strip()
    url_queue.put(url)

while len(visited) <= 75 and url_queue.qsize() != 0:
    url = url_queue.get()
    try:
        if url not in visited:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            page = urllib.request.urlopen(req)
            visited[url] = []
            pageText = page.read()
            find_urls(str(pageText))

    except urllib.error.HTTPError as err:
        print(err, url)

    except ValueError as err:
        print(err)

    except urllib.error.URLError as err:
        print(err, url)

with open('output.csv', 'w') as f:
    w = csv.writer(f)
    w.writerow(["Page", "Links"])
    w.writerows(visited.items())
