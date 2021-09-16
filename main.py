import argparse
import json
import logging
import math
import matplotlib.pyplot as plt

from collections import namedtuple
from matplotlib.patches import Circle
from typing import List
from typing import Optional


Point = namedtuple('Point', ['x', 'y'])


class Transceiver:
    REC_MIN_DENSITY = 1
    __all = []

    """
    Transceiver is modelled as having antenna with ideal spherical radiation.
    It's coverage will be defined as a sphere, where it's signal power density is at required minimum value.
    """
    def __init__(self, location, power):
        self.location = Point(*location)            # type: Point
        self.power = power                          # type: int

        self.__all.append(self)
        self.nr = len(self.__all)

    def __repr__(self):
        return f'Transceiver: {self.nr}: {self.location}->{self.range}'

    @property
    def all(self):
        return self.__all

    @property
    def range(self):
        # type: () -> float
        """
        S = 4 * math.pi * r**2
        r = math.sqrt(S / (4 * math.pi))
        power density d = P / S, S = P / d
        """
        r = math.sqrt(self.power / self.REC_MIN_DENSITY / (4 * math.pi))
        return r

    def covers_point(self, point):
        # type: (Point) -> bool
        """
        return True if point is in range
        """
        within_range = (point.x - self.location.x) ** 2 + (point.y - self.location.y) ** 2 <= self.range ** 2
        logging.info(
            f'Transceiver({self} {"covers" if within_range else "does not cover"} '
            f'point({point})'
        )
        return within_range

    def is_neighbour(self, other):
        # type: (Transceiver) -> bool
        """
        Circles overlap or are contiguous if distance between their middle points is not higher than sum of their radius
        """

        return (other.location.x - self.location.x) ** 2 + (other.location.y - self.location.y) ** 2 \
            <= (self.range + other.range) ** 2

    @property
    def neighbours(self):
        return filter(lambda t: self.is_neighbour(t) and self is not t, self.all)

    def generate_possible_routes(self, routes=None, visited=None):
        # type: (Optional[List[List[Transceiver]]], Optional[List[Transceiver]]) -> List[List[Transceiver]]
        routes = routes or [[self]]
        visited = visited or [self]
        
        for route in routes:
            last = route[-1]
            for transceiver in last.neighbours:
                if transceiver not in visited:
                    visited.append(transceiver)
                    new_route = route + [transceiver]
                    routes.append(new_route)
                    yield new_route
                    yield from transceiver.generate_possible_routes(routes, visited)


def find_route(data):
    """
    There will be a route from A to B, under transceiver coverage, when exists such a set of transceiver coverage
    circles, that are contiguous or overlap each other and contain both points A and B
    """
    transceivers = [Transceiver(t["location"], t["power"]) for t in data['transceivers']]
    point_a = Point(*data['A'])
    point_b = Point(*data['B'])

    start_transceivers = filter(lambda t: t.covers_point(point_a), transceivers)

    for transceiver in start_transceivers:
        for route in transceiver.generate_possible_routes():
            last = route[-1]
            if last.covers_point(point_b):
                return route
    return None


def draw_route(ax, route):
    # type: (List[Transceiver]) -> None

    for transceiver in route:
        ax.add_patch(Circle(transceiver.location, transceiver.range, fill=False, color='black'))


def draw_all_transceivers(ax, transceivers):
    for transceiver in transceivers:
        ax.add_patch(Circle(transceiver.location, transceiver.range, fill=False, color="red"))


def draw_all(data, route):
    transceivers = [Transceiver(t["location"], t["power"]) for t in data['transceivers']]
    point_a = Point(*data['A'])
    point_b = Point(*data['B'])

    fig, ax = plt.subplots()
    draw_all_transceivers(ax, transceivers)
    if route:
        draw_route(ax, route)
    ax.autoscale(enable=True, axis='both', tight=None)
    plt.plot(*point_a, 'bo')
    plt.plot(*point_b, 'bo')
    plt.show()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-file_path", type=str, help='data file location', default="data.json")
    args = parser.parse_args()

    with open(args.file_path) as f:
        data = json.load(f)

    route = find_route(data)
    draw_all(data, route)

    if route:
        print("Path from A to B under transceivers coverage exists")
    else:
        print("Path from A to B under transceivers coverage does not exist!")
