from argparse import ArgumentParser, FileType
from sys import stdout
from heapq import nlargest

import requests
import oyaml as yaml

import time
import datetime
import logging


def parse_args():
    """
    Retrieve args from command line.
    """
    parser = ArgumentParser(
        description="Find the DOTA 2 teams with the most combined player *experience",
        epilog="*Experience is defined as the length of a player's recorded history.",
    )
    parser.add_argument("output", type=FileType("w"), nargs="?", default=stdout)
    parser.add_argument(
        "-n", "--num-teams", type=int, default=5, help="number of teams in output"
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
uri = "https://api.opendota.com/api"
global_time = time.time()


def main():
    args = parse_args()
    #    with open(args.output) as file:
    # TODO: put yaml together
    #    logging.basicConfig(level=logging.args("-l"))
    get_proplayers(args)


def get_proplayers(args):
    """
    Retrieve players from OpenDota
    """
    req = requests.get(uri + "/proPlayers").json()
    for player in req:
        player_xp = check_experience(player)
        cumulative_xp = add_to_scoreboard(player, player_xp)

    sanitize_teams(cumulative_xp, req)


def check_experience(player):
    """
    Calculate player experience in a standardized format (diff of Unix timestamp)
    """
    try:
        _player_history_time = player["full_history_time"]
        _corrected_time = datetime.datetime.strptime(
            _player_history_time, "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        player_xp = global_time - _corrected_time.timestamp()
    except:
        player_xp = 0

    return player_xp


def add_to_scoreboard(player, player_xp):
    if player["team_id"] not in cumulative_xp.keys():
        cumulative_xp.update({player["team_id"]: 0})
    if player["team_id"] in cumulative_xp.keys():
        _last_team_xp = cumulative_xp.get(player["team_id"])
        _calc_team_xp = _last_team_xp + player_xp
        _new_team_dict = {player["team_id"]: _calc_team_xp}
        cumulative_xp.update(_new_team_dict)
    return cumulative_xp


def sanitize_teams(cumulative_xp, req):
    _arg_n = 3

    # remove entry for team "0"
    if 0 in cumulative_xp:
        del cumulative_xp[0]

    top_teams = nlargest(_arg_n, cumulative_xp, key=cumulative_xp.get)

    _team_list = []
    for _team_id in top_teams:
        # DEBUG: print(_team_id, ":", cumulative_xp.get(_team_id))
        try:
            team_name = requests.get(uri + "/teams/" + str(_team_id)).json()
            _team_list.append(
                {
                    "team_name": team_name["name"],
                    "team_wins": team_name["wins"],
                    "team_losses": team_name["losses"],
                }
            )
            print(team_name["name"] + " processed...")
            for player in req:
                if player["team_id"] == _team_id:
                    _player_list = [
                        {
                            "persona": player["personaname"],
                            "experience": int(check_experience(player)),
                            "country": player["country_code"],
                        }
                    ]
                    _team_list.append(_player_list)
        except:
            logging.error(
                "Failed to find Team {}, output will not include this value.".format(
                    team_name["name"]
                )
            )
            logging.info("")
            pass
    try:
        with open("ranking.yml", "w+") as outfile:
            yaml.dump(_team_list, outfile, default_flow_style=False)
            logging.debug("Wrote file successfully to {}".format(outfile))
    except:
        logging.error("Failed writing output to yaml file.")

    build_objects(top_teams)


def build_objects(top_teams):
    print("done.")


if __name__ == "__main__":
    main()
