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
    # I don't love the open file handle left around by argparse's builtin file handler
    # so I modified this to just be a string I can use to open it cleanly later.
    parser.add_argument("output", nargs="?", default=stdout)
    parser.add_argument(
        "-n", "--numteams", type=int, default=5, help="number of teams in output"
    )
    parser.add_argument(
        "-l",
        "--loglevel",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        default="WARNING",
        help="Only output log messages of this severity or above. Writes to stderr. (default: %(default)s)",
    )
    return parser.parse_args()


# A few convenient constants
cumulative_xp = {}
uri = "https://api.opendota.com/api"
static_time = time.time()


def main():
    """
    Parse arguments and setup logging, get players
    """
    args = parse_args()
    logging.debug("Log level set to {}", args.loglevel)

    get_proplayers(args)


def get_proplayers(args):
    """
    Retrieve players from OpenDota
    """
    req = requests.get(uri + "/proPlayers").json()
    for player in req:
        player_xp = check_experience(player)
        cumulative_xp = add_to_scoreboard(player, player_xp)

    score_teams(cumulative_xp, req, args)


def check_experience(player):
    """
    Calculate player experience in a standardized format (diff of Unix timestamp
    from the global_time.)
    """
    try:
        _player_history_time = player["full_history_time"]
        _corrected_time = datetime.datetime.strptime(
            _player_history_time, "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        player_xp = static_time - _corrected_time.timestamp()
        logging.info("Player {} gets {} XP.", player["name"], player_xp)
    except:
        logging.debug(
            "Failed to calculate score for {}, setting to zero".format(player["name"])
        )
        player_xp = 0
        pass

    return player_xp


def add_to_scoreboard(player, player_xp):
    """
    Summate the collective player's score into a dictionary with keys = team_id,
    value = cumulative_score.
    """
    if player["team_id"] not in cumulative_xp.keys():
        cumulative_xp.update({player["team_id"]: 0})
    if player["team_id"] in cumulative_xp.keys():
        _last_team_xp = cumulative_xp.get(player["team_id"])
        _calc_team_xp = _last_team_xp + player_xp
        _new_team_dict = {player["team_id"]: _calc_team_xp}
        cumulative_xp.update(_new_team_dict)
    return cumulative_xp


def score_teams(cumulative_xp, req, args):
    """
    Sort the top n teams, write data to YAML file.

    Tradeoff Notes:
    The YAML library here doesn't support Unicode, unlike the latest PyYAML, but
    it does retain sort order for the yaml.dump() function, which is - for IMHO
    kind of esoteric reasons - not fixed in the current PyYAML.

    I'm also not sure what I'm missing with the all the dashes in the output here.
    Possibly I need to use simpler data structures/a better library (or just
    write line by line with proper indentation). Maybe just because I don't write
    out YAML much...
    """

    _arg_n = args.numteams

    # remove entry for team "0"
    if 0 in cumulative_xp:
        del cumulative_xp[0]

    top_teams = nlargest(_arg_n, cumulative_xp, key=cumulative_xp.get)

    _team_list = []
    _player_list = []
    for _team_id in top_teams:
        try:
            team_name = requests.get(uri + "/teams/" + str(_team_id)).json()
            _team_list.append(
                {
                    "team_name": team_name["name"],
                    "team_wins": team_name["wins"],
                    "team_losses": team_name["losses"],
                }
            )
            logging.debug("Added {} to team list.".format(team_name["name"]))
        except:
            logging.error(
                "Team {} could not be found, skipping.".format(team_name["name"])
            )
            logging.info("Could not find team {} ".format(team_name["name"]))
            pass

        _player_list = []
        for player in req:
            if player["team_id"] == _team_id:
                _player_list.append(
                    {
                        "persona": player["personaname"],
                        "experience": int(check_experience(player)),
                        "country": player["country_code"],
                    }
                )
        _team_list.append(_player_list)

    try:
        if args.output == stdout:
            print(yaml.dump(_team_list, default_flow_style=False))
        else:
            with open(args.output, "w+") as outfile:
                yaml.safe_dump(_team_list, outfile, default_flow_style=False)
                logging.debug("Wrote file successfully to {}".format(outfile))
    except:
        logging.error("Failed writing output to yaml file.")


if __name__ == "__main__":
    main()
