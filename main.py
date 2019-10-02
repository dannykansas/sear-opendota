from argparse import ArgumentParser, FileType
from sys import stdout
from heapq import nlargest

import requests
import yaml

import time
import datetime


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

# constants
cumulative_xp = {}
uri = 'https://api.opendota.com/api'
global_time = time.time()

def main():
    args = parse_args()
    #    with open(args.output) as file:
    #TODO: put yaml together
    #    logging.basicConfig(level=logging.args("-l"))
    get_proplayers(args)

def get_proplayers(args):
    """
    Retrieve players from OpenDota
    """
    req = requests.get(uri + '/proPlayers').json()
    for player in req:
        player_xp = check_experience(player)
        cumulative_xp = add_to_scoreboard(player, player_xp)

    sanitize_teams(cumulative_xp, req)

def check_experience(player):
    """
    Calculate player experience in a standardized format (diff of Unix timestamp)
    """
    try:
        _player_history_time = player['full_history_time']
        _corrected_time = datetime.datetime.strptime(_player_history_time, '%Y-%m-%dT%H:%M:%S.%fZ')
        player_xp = global_time - _corrected_time.timestamp()
    except:
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

def sanitize_teams(cumulative_xp, req):
    _arg_n = 4

    # remove entry for team "0"
    if 0 in cumulative_xp:
        del cumulative_xp[0]

    top_teams = nlargest(_arg_n, cumulative_xp, key = cumulative_xp.get)

    for _team_id in top_teams:
        #DEBUG: print(_team_id, ":", cumulative_xp.get(_team_id))
        try:
            team_name = requests.get(uri + '/teams/' + str(_team_id)).json()
            print("Team: ", team_name['name'])
            print("Wins: ", team_name['wins'])
            print("Losses: ", team_name['losses'])
            print("Rating: ", team_name['rating'])
            for player in req:
                if player['team_id'] == _team_id:
                    print("  - Persona:  ", player['personaname'])
                    print("         XP:  ", int(check_experience(player)))
                    print("    Country: ", player['country_code'])
        except:
            #print("Nothing returned for: ", _team_id)
            pass

    build_objects(top_teams)

def build_objects(top_teams):
    print("done.")


if __name__ == "__main__":
    main()
