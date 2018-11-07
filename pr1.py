import urllib.request
import urllib.error
import re
from multiprocessing import Manager, Process, Lock, Value
import csv
from time import sleep
from math import sin, cos, pi
from tkinter import Tk, Canvas


# Node class holds coordinates, link, and the links it points to
class Node:
    # Static variable used to keep track of how many nodes there are, also used as id
    link_id = 1

    def __init__(self, x, y, link, links):
        self.x = x
        self.y = y
        self.link = link
        self.links = links
        self.link_id = Node.link_id
        Node.link_id += 1


# Graphics class draws the given dictionary of links with the nodes evenly spaced out in a circle.
class Graphics:

    def __init__(self, links_dict, canvas_size=800):
        self.links_dict = links_dict
        self.canvas_size = canvas_size
        self.nodes = {}
        self.top = Tk()
        self.top.title("Graphics")

    def run(self):
        for key in self.links_dict.keys():
            radian = (Node.link_id - len(self.links_dict) // 4 - 1) / len(self.links_dict) * pi * 2
            x = cos(radian) * (self.canvas_size / 2 - 40) + self.canvas_size / 2
            y = sin(radian) * (self.canvas_size / 2 - 40) + self.canvas_size / 2
            self.nodes[key] = Node(x, y, key, self.links_dict[key])
        canvas = Canvas(self.top, width=self.canvas_size, height=self.canvas_size)
        canvas.pack()
        for key in self.links_dict.keys():
            x = self.nodes[key].x
            y = self.nodes[key].y
            for link in self.nodes[key].links:
                if link in self.nodes:
                    canvas.create_line(x, y, self.nodes[link].x, self.nodes[link].y)
            canvas.create_rectangle(x - self.canvas_size / 62, y - self.canvas_size / 62, x + self.canvas_size / 62,
                                    y + self.canvas_size / 62,
                                    outline='black', fill='white')
            canvas.create_text(x, y, text=self.nodes[key].link_id)
        self.top.mainloop()


# Helper method used to search for new links from the current page's html, put them to the shared queue, and
# return the list
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


# Crawls all the links in the queue if the shared exit flag is 1, exits if 0
# If the queue is empty, waits around 0.1 seconds before trying again.
# The function will keep working until the limit is reached (75).
def crawl(shared_lock, shared_exit_flag, shared_queue, shared_visited, max_links):
    while shared_exit_flag.value:
        if not shared_queue.empty():
            url = shared_queue.get()
            try:
                if url not in shared_visited:
                    shared_lock.acquire()
                    if len(shared_visited) < max_links:
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


# Generates the list of links with most referenced to. Exit flag is turned to 0 when the function is finished.
def get_top_link(visited_dict, shared_queue, shared_count, shared_exit_flag):
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
    shared_exit_flag.value = 0


# Generates a csv output for all the links in the dictionary
def csv_output(visited_dict, shared_count_queue, count, shared_exit_flag):
    f = open('output.csv', 'w')
    w = csv.writer(f)
    w.writerow(["Page", "Links"])
    w.writerows(visited_dict.items())
    while shared_exit_flag.value:
        sleep(0.1)
    w.writerow(['Top Link(s):' + str(count.value)])
    while shared_count_queue.empty() is False:
        w.writerow([shared_count_queue.get()])
    f.close()


# Generates a graphics representation of all the links
def generate_graphics(visited):
    graphics = Graphics(visited, 800)
    graphics.run()


# Generates output with 3 different processes that handle csv output, get most referenced links,
# and graphical representation.
def generate_output(visited):
    count_queue = manager.Queue()
    count = Value('i', 0)
    exit_flag = Value('i', 1)

    p_csv = Process(target=csv_output, args=(visited, count_queue, count, exit_flag))
    p_count = Process(target=get_top_link, args=(visited, count_queue, count, exit_flag))
    p_graphics = Process(target=generate_graphics, args=(visited,))
    p_count.start()
    p_csv.start()
    p_graphics.start()
    p_count.join()
    p_csv.join()
    p_graphics.join()


# Starts the crawling processes by generating 8 processes
def start_crawling():
    p = [Process(target=crawl, args=(lock, exit_flag, url_queue, visited, max_links)) for i in range(8)]

    # start child processes
    for each in p:
        each.start()

    # wait for all children to finish
    for each in p:
        each.join()


# Main method, initializes all the data structures.
if __name__ == '__main__':
    lock = Lock()
    manager = Manager()
    url_queue = manager.Queue()
    visited = manager.dict()
    exit_flag = Value('i', 1)
    max_links = 75
    for link in open('urls6.txt', 'r'):
        link = link.strip()
        url_queue.put(link)

    start_crawling()
    generate_output(visited)
