import urllib.request
import urllib.error
import re
from multiprocessing import Manager, Process, Lock, Value, current_process
import csv
from time import sleep


# Helper method used to search for new links from the current page's html, then append them to the shared queue
def find_urls(html: str, shared_queue):
    regex = r'a href\s?=\s?[\'"]?(?![\W(mailto:)])([^\'" >]+)'
    new_links = []
    for new_url in re.findall(regex, html):
        if new_url not in new_links:
            if re.search('\.', new_url):
                if re.search('\.html', new_url) and re.search('/', new_url):
                    shared_queue.put(new_url)
                    new_links.append(new_url)
                elif not re.search('\.html', new_url) and not re.search('javascript:', new_url):
                    shared_queue.put(new_url)
                    new_links.append(new_url)
    return new_links


# Crawls all the links in the queue if the shared exit flag is 0, exits if 1
# If the queue is empty, waits around 0.1 seconds before trying again.
def crawl(shared_lock, shared_exit_flag, shared_queue, shared_visited):
    while shared_exit_flag.value:
        if shared_queue.empty() is not True:
            url = shared_queue.get()
            try:
                if url not in shared_visited:
                    shared_lock.acquire()
                    if len(shared_visited) < 74:
                        shared_visited[url] = []
                        shared_lock.release()
                        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                        page = urllib.request.urlopen(req)
                        new_links = find_urls(str(page.read()), shared_queue)
                        shared_visited[url] = new_links
                    else:
                        shared_exit_flag.value = 0
                        shared_lock.release()
                        break

            except urllib.error.HTTPError as err:
                print(err, url)

            except ValueError as err:
                print(err)

            except urllib.error.URLError as err:
                print(err, url)
        else:
            sleep(0.1)


def get_top_link(visited_dict, shared_queue, shared_count, exit_flag):
    count_dict = {}
    for v in visited_dict.items():
        for c in v[1]:
            if c not in count_dict:
                count_dict[c] = 1
            else:
                count_dict[c] += 1
    max_links = []
    for count_item in count_dict.items():
        if count_item[1] > shared_count.value:
            max_links = [count_item[0]]
            shared_count.value = count_item[1]
        elif count_item[1] == shared_count.value:
            max_links.append(count_item[0])

    for l in max_links:
        shared_queue.put(l)
    exit_flag.value = 0


def csv_output(visited_dict, shared_count_queue, count, exit_flag):
    f = open('output_async.csv', 'w')
    w = csv.writer(f)
    w.writerow(["Page", "Links"])
    w.writerows(visited_dict.items())
    while exit_flag.value:
        sleep(0.1)
    w.writerow(['Top Link(s):' + str(count.value)])
    while shared_count_queue.empty() is False:
        w.writerow([shared_count_queue.get()])
    f.close()


def generate_output():
    count_queue = manager.Queue()
    count = Value('i', 0)
    exit_flag = Value('i', 1)
    p_csv = Process(target=csv_output, args=(visited, count_queue, count, exit_flag))
    p_count = Process(target=get_top_link, args=(visited, count_queue, count, exit_flag))

    p_count.start()
    p_csv.start()

    p_count.join()
    p_csv.join()


if __name__ == '__main__':
    lock = Lock()
    manager = Manager()
    url_queue = manager.Queue()
    visited = manager.dict()
    exit_flag = Value('i', 1)
    for link in open('urls6.txt', 'r'):
        link = link.strip()
        url_queue.put(link)

    p = [Process(target=crawl, args=(lock, exit_flag, url_queue, visited)) for i in range(8)]

    # start child processes
    for each in p:
        each.start()

    # wait for all children to finish
    for each in p:
        each.join()

    generate_output()
