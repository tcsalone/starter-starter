#!/usr/bin/env python3

import datetime
import os
import sys
import inspect
from yfpy import YahooFantasySportsQuery # Make sure yfpy is installed


YAHOO_LEAGUE_ID = "41370" # <--- *** REPLACE THIS REQUIRED ***
AUTH_DIR = "C:\\Users\\eamon\\Git_Repos\\starter_starter\\starter-starter\\yfpy\\" # <--- *** ADJUST IF 'private.json' IS ELSEWHERE ***
GAME_CODE = 'mlb'


def fetch_league_teams(yfs):
    teams = yfs.get_league_teams()
    
    print("\n--- Teams in Your League ---")
    for team in teams:
        print(f"Team Name: {team.team_name}, Team ID: {team.team_id}")

    return teams

if __name__ == "__main__":
    #yfs = YahooFantasySportsQuery(YAHOO_LEAGUE_ID, AUTH_DIR, GAME_CODE)
    yfs = YahooFantasySportsQuery(YAHOO_LEAGUE_ID, AUTH_DIR, GAME_CODE, yahoo_consumer_key="dj0yJmk9WVhKSVk2Vm5HNVBFJmQ9WVdrOVEwRklWbGhyUjBNbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PWJh", yahoo_consumer_secret="00bc06f768688f8aab80164babc32117e5a69d96")
    print(inspect.getmembers(yfs, predicate=inspect.ismethod))
    
    fetch_league_teams(yfs)

