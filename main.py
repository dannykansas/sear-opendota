from argparse import ArgumentParser, FileType
from sys import stdout

import requests


def parse_args():
    """
    Retrieve args from command line.
    """
    parser = ArgumentParser(
        description="Find the DOTA 2 teams with the most combined player *experience",
        epilog="*Experience is defined as the length of a player's recorded history.",
    )
    parser.add_argument(
        "output", type=FileType("w"), nargs="?", default=stdout
    )
    parser.add_argument(
        "-n",
        "--num-teams",
        type=int,
        default=5,
        help="number of teams in output",
    )
    parser.add_argument(
        "-l",
        "--loglevel",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        default="WARNING",
        help="Only output log messages of this severity or above. Writes to stderr. (default: %(default)s)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

def connector():

def get_proplayers():

def get_teams():

def merge_proplayers():

def sum_experience_by_team():



if __name__ == "__main__":
    main()
