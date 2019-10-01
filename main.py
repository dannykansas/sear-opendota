from argparse import ArgumentParser, FileType
from sys import stdout

import requests
import yaml

import time
import datetime
#import logging

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

cumulative_xp = {}

def main():
    args = parse_args()
    #    with open(args.output) as file:
    # TODO put yaml together
    #    logging.basicConfig(level=logging.args("-l"))

def get_proplayers():
    uri = 'https://api.opendota.com/api'
    req = requests.get(uri + '/proPlayers')
    for player in req.json():
        player_xp = check_experience(player)
        cumulative_xp = add_to_scoreboard(player, player_xp)
        print(cumulative_xp)
    # then start matching team IDs in cumulative_xp to /team/{team_id} and construct the YAML! easy.

def check_experience(player):
    if player['full_history_time'] not 'None':
        _player_history_time = player['full_history_time']
        _corrected_time = datetime.datetime.strptime(_player_history_time, '%Y-%m-%dT%H:%M:%S.%fZ')
        player_xp = time.time() - _corrected_time.timestamp()
    else:
        # TODO: log the fact that there was no data returned for this user
        player_xp = 0
    return player_xp

def add_to_scoreboard(player, player_xp):
    if player['team_id'] not in cumulative_xp.keys():
        cumulative_xp.update({player['team_id']:0})
    if player['team_id'] in cumulative_xp.keys():
        _last_team_xp = cumulative_xp.get(player['team_id'])
        _calc_team_xp = _last_team_xp + player_xp
        _new_team_dict = {player['team_id']:_calc_team_xp}
        cumulative_xp.update(_new_team_dict)
    return cumulative_xp

if __name__ == "__main__":
    main()
