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
