#!/usr/bin/env python3

import datetime
import os
import sys
from yfpy import YahooFantasySportsQuery # Make sure yfpy is installed

YAHOO_LEAGUE_ID = "41370" # <--- *** REPLACE THIS REQUIRED ***
AUTH_DIR = "C:\\Users\\eamon\\Git_Repos\\starter_starter\\starter-starter\\yfpy\\" # <--- *** ADJUST IF 'private.json' IS ELSEWHERE ***
GAME_CODE = 'mlb'

def ensure_auth_dir_and_private_json(auth_dir):
    """Checks if auth directory and private.json exist, providing guidance."""
    private_json_path = os.path.join(auth_dir, "private.json")

    if not os.path.exists(auth_dir):
        print(f"Error: Authentication directory not found: {auth_dir}")
        print("Please create this directory.")
        return False

    if not os.path.isfile(private_json_path):
        print(f"Error: 'private.json' not found in directory: {auth_dir}")
        print("\nPlease create 'private.json' in that directory with your")
        print("Yahoo App 'consumer_key' and 'consumer_secret'. Format:")
        print("""
{
    "consumer_key": "YOUR_YAHOO_CONSUMER_KEY",
    "consumer_secret": "YOUR_YAHOO_CONSUMER_SECRET"
}
        """)
        return False
    return True

def get_starting_pitchers(league_id, game_code, auth_dir):
    """
    Authenticates with Yahoo, fetches the user's team roster for today,
    and identifies which Starting Pitchers (SP) are scheduled to start.
    """
    if league_id == "YOUR_LEAGUE_ID":
        print("*"*60)
        print("ERROR: Please update the 'YAHOO_LEAGUE_ID' variable in the script")
        print("       with your actual Yahoo Fantasy Baseball League ID.")
        print("*"*60)
        sys.exit(1) # Exit the script

    if not ensure_auth_dir_and_private_json(auth_dir):
        sys.exit(1) # Exit if auth setup is missing


    print("Attempting to authenticate with Yahoo Fantasy Sports...")
    try:
        #yfs = YahooFantasySportsQuery(auth_dir, game_code, league_id, yahoo_consumer_key="dj0yJmk9WVhKSVk2Vm5HNVBFJmQ9WVdrOVEwRklWbGhyUjBNbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PWJh", yahoo_consumer_secret="00bc06f768688f8aab80164babc32117e5a69d96")
        yfs = YahooFantasySportsQuery(YAHOO_LEAGUE_ID, AUTH_DIR, GAME_CODE, yahoo_consumer_key="dj0yJmk9WVhKSVk2Vm5HNVBFJmQ9WVdrOVEwRklWbGhyUjBNbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PWJh", yahoo_consumer_secret="00bc06f768688f8aab80164babc32117e5a69d96")
        print("Authentication successful (or cached token used).")

    except Exception as e:
        print(f"\nError during authentication or initialization: {e}")
        print("\nTroubleshooting:")
        print(f"- Ensure '{os.path.join(auth_dir, 'private.json')}' exists and is correctly formatted.")
        print("- Ensure the consumer key/secret in 'private.json' are valid.")
        print("- If prompted for browser authentication, ensure you complete the steps correctly.")
        print("- Check your internet connection.")
        sys.exit(1)

    try:
        # Get the user's default team object for the specified league
        print(f"Accessing your team in league {league_id}...")
        team = yfs.get_team_info(2)
        if not team:
             print(f"Error: Could not retrieve your team for league ID {league_id}.")
             print("Is the LEAGUE_ID correct? Do you have a team in that league?")
             sys.exit(1)

        #print(f"Successfully accessed team: {team.team_name}")

        # Get today's date for the roster query
        today = datetime.date.today()
        today = today + datetime.timedelta(days=1)
        print(f"Checking roster and pitcher status for: {today.strftime('%Y-%m-%d')}")

        # Fetch the roster for today
        #roster = yfs.get_roster(2, day=today)
        #roster = yfs.get_team_roster_player_info_by_date(day=today)
        
        #this works...
        # #roster = yfs.get_team_roster_by_week(2, chosen_week='current')

        roster = yfs.get_team_roster_player_info_by_date(2, )
       

        print("\n--- Verifying all players by name ---")
        count = 0
        for player in roster:
            count += 1
            player_name = player.name.full if hasattr(player, 'name') and hasattr(player.name, 'full') else "Unknown Name"
            print(f"{count}. {player_name}")
        #print(roster)
        starting_pitchers_today = []
        other_sps_on_roster = []

        print("\n--- Analyzing Roster ---")
        for player in roster:
            print(player)
            player_name = player.name.full
            is_sp = any(pos.position == 'SP' for pos in player.eligible_positions)

            if is_sp:
                # Check the 'starting_status' attribute provided by the Yahoo API
                # '1' typically means starting today for fantasy purposes
                # '0' means not starting today
                # Note: This reflects probable starters for the *current day's games*.
                is_starting_today = hasattr(player, 'starting_status') and player.starting_status == '1'

                if is_starting_today:
                    starting_pitchers_today.append(player_name)
                    print(f"[STARTING TODAY] {player_name}")
                else:
                    # Add extra info if available (like Injured List status)
                    status_detail = f" (Status: {player.status})" if hasattr(player, 'status') and player.status else ""
                    other_sps_on_roster.append(f"{player_name}{status_detail}")
                    print(f"[ On Roster - Not Starting ] {player_name}{status_detail}")

        print("\n--- Summary ---")
        if starting_pitchers_today:
            print("✅ Starting Pitchers scheduled to pitch today:")
            for name in starting_pitchers_today:
                print(f"   - {name}")
        else:
            print("ℹ️ No Starting Pitchers from your roster are scheduled to start today.")

    except Exception as e:
        print(f"\nAn error occurred while fetching or processing fantasy data: {e}")
        print("\nPossible causes:")
        print("- Invalid YAHOO_LEAGUE_ID or GAME_CODE.")
        print("- Network connection issues.")
        print("- Temporary issues with the Yahoo Fantasy API.")
        print("- Changes in the API data structure.")
        sys.exit(1)

# --- Run the main function ---
if __name__ == "__main__":
    get_starting_pitchers(YAHOO_LEAGUE_ID, GAME_CODE, AUTH_DIR)
