#!/usr/bin/env python3
import csv            # read CSV rows as dicts
import sys            # read command-line args / exit
from util import Node, StackFrontier, QueueFrontier

# Maps names (lowercased) -> set(person_id)
names = {}
# Maps person_id -> {"name": str, "birth": str, "movies": set(movie_id)}
people = {}
# Maps movie_id -> {"title": str, "year": str, "stars": set(person_id)}
movies = {}


def load_data(directory):
    """
    Load CSV data into memory: names, people, movies.
    """
    # people.csv
    with open(f"{directory}/people.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            people[row["id"]] = {
                "name": row["name"],
                "birth": row["birth"],
                "movies": set(),
            }
            names.setdefault(row["name"].lower(), set()).add(row["id"])

    # movies.csv
    with open(f"{directory}/movies.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            movies[row["id"]] = {
                "title": row["title"],
                "year": row["year"],
                "stars": set(),
            }

    # stars.csv (edges person <-> movie)
    with open(f"{directory}/stars.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                people[row["person_id"]]["movies"].add(row["movie_id"])
                movies[row["movie_id"]]["stars"].add(row["person_id"])
            except KeyError:
                # ignore rows that reference missing ids
                pass


def pretty_print(source_id, path):
    """
    Print the path returned by shortest_path without inserting a dummy step.
    source_id: starting person_id
    path: list[(movie_id, person_id)] from shortest_path
    """
    degrees = len(path)
    print(f"{degrees} degrees of separation.")
    prev = source_id
    for i, (movie_id, person_id) in enumerate(path, start=1):
        p1 = people[prev]["name"]
        p2 = people[person_id]["name"]
        mv = movies[movie_id]["title"]
        print(f"{i}: {p1} and {p2} starred in {mv}")
        prev = person_id


def main():
    if len(sys.argv) > 2:
        sys.exit("Usage: python degrees.py [directory]")
    directory = sys.argv[1] if len(sys.argv) == 2 else "large"

    print("Loading data...")
    load_data(directory)
    print("Data loaded.")

    source = person_id_for_name(input("Name: "))
    if source is None:
        sys.exit("Person not found.")
    target = person_id_for_name(input("Name: "))
    if target is None:
        sys.exit("Person not found.")

    path = shortest_path(source, target)
    if path is None:
        print("Not connected.")
    else:
        pretty_print(source, path)


def shortest_path(source, target):
    """
    Return the shortest list of (movie_id, person_id) pairs that connect
    the actor `source` to actor `target`.

    Strategy: Breadth-First Search over the implicit graph where
    - state  = person_id (actor)
    - action = movie_id that connects to a co-star
    - neighbors_for_person(state) yields (movie_id, person_id) for all co-stars

    All edges cost 1, so BFS yields a minimum-length chain.
    """
    # source == target -> zero steps
    if source == target:
        return []

    # BFS frontier seeded with the source
    frontier = QueueFrontier()
    frontier.add(Node(state=source, parent=None, action=None))

    explored = set()        # expanded actors
    in_frontier = {source}  # queued actors

    def rebuild(goal_node):
        """Walk parents to build [(movie_id, person_id), ...] from source->target."""
        path = []
        node = goal_node
        while node.parent is not None:
            path.append((node.action, node.state))
            node = node.parent
        path.reverse()
        return path

    while not frontier.empty():
        current = frontier.remove()
        in_frontier.discard(current.state)
        explored.add(current.state)

        # generate neighbors (movie, co-star)
        for movie_id, person_id in neighbors_for_person(current.state):
            if person_id in explored or person_id in in_frontier:
                continue

            child = Node(state=person_id, parent=current, action=movie_id)

            # early goal test on generation
            if person_id == target:
                return rebuild(child)

            frontier.add(child)
            in_frontier.add(person_id)

    # no connection
    return None


def person_id_for_name(name):
    """
    Returns the IMDb id for a person's name (case-insensitive).
    If ambiguous, prompt for the intended id. Returns None if unknown.
    """
    person_ids = list(names.get(name.lower(), set()))
    if len(person_ids) == 0:
        return None
    elif len(person_ids) > 1:
        print(f"Which '{name}'?")
        for person_id in person_ids:
            person = people[person_id]
            print(f"ID: {person_id}, Name: {person['name']}, Birth: {person['birth']}")
        try:
            person_id = input("Intended Person ID: ")
            if person_id in person_ids:
                return person_id
        except ValueError:
            pass
        return None
    else:
        return person_ids[0]


def neighbors_for_person(person_id):
    """
    For a given person_id, return a set of (movie_id, person_id) pairs
    for all co-stars who share a movie with that person.
    """
    movie_ids = people[person_id]["movies"]
    neighbors = set()
    for movie_id in movie_ids:
        for pid in movies[movie_id]["stars"]:
            neighbors.add((movie_id, pid))
    return neighbors


if __name__ == "__main__":
    main()

# Note:
# Heavily commented on purpose — this helps me remember what I built
# and understand the mechanics of the code step by step.
