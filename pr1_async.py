import urllib.request
import urllib.error
import re
from multiprocessing import Queue, Pool
import csv


# Helper method used to search for new website from the current page's html
def find_urls(current_url, html: str, shared_queue, shared_visited):
    v1 = r'href=[\'"]?(?!/)([^\'" >]+)'
    regex = r'a href\s?=\s?[\'"]?(?![\W(mailto:)])([^\'" >]+)'
    for new_url in re.findall(regex, html):
        if re.search('\.', new_url):
            if re.search('\.html', new_url) and re.search('/', new_url):
                shared_queue.put(new_url)
                shared_visited[current_url].append(new_url)
            elif not re.search('\.html', new_url) and not re.search('javascript:', new_url):
                shared_queue.put(new_url)
                shared_visited[current_url].append(new_url)


def crawl(shared_queue, shared_visited):
    while len(shared_visited) <= 75 and shared_queue.qsize() > 0:
        url = shared_queue.get()
        try:
            if url not in shared_visited:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                page = urllib.request.urlopen(req)
                shared_visited[url] = []
                find_urls(url, str(page.read()), shared_queue, shared_visited)

        except urllib.error.HTTPError as err:
            print(err, url)

        except ValueError as err:
            print(err)

        except urllib.error.URLError as err:
            print(err, url)


if __name__ == '__main__':

    visited = {}
    url_queue = Queue(maxsize=0)
    for link in open('urls3.txt', 'r'):
        link = link.strip()
        url_queue.put(link)

    pool = Pool()
    result = pool.map(crawl, url_queue)
    # p = [Process(target=crawl, args=(url_queue, visited)) for i in range(4)]
    #
    # # start child processes
    # for each in p:
    #     each.start()
    #
    # # wait for all children to finish
    # for each in p:
    #     each.join()

    with open('output_async.csv', 'w') as f:
        w = csv.writer(f)
        w.writerow(["Page", "Links"])
        w.writerows(visited.items())
