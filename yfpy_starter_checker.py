#!/usr/bin/env python3

import datetime
import os
import sys
from yfpy import YahooFantasySports # Make sure yfpy is installed

# --- Configuration ---

# 1. SET YOUR LEAGUE ID HERE:
#    Find this in the URL of your Yahoo Fantasy Baseball league page.
#    Example: If URL is https://baseball.fantasysports.yahoo.com/b1/123456, ID is "123456"
YAHOO_LEAGUE_ID = "YOUR_LEAGUE_ID" # <--- *** REPLACE THIS REQUIRED ***

# 2. SET THE PATH TO YOUR AUTHENTICATION DIRECTORY:
#    This is the directory where your 'private.json' file is located.
#    Use '.' for the current directory, or provide a full path like '/path/to/your/auth'.
#    Recommendation: Keep this directory separate from your script for security.
AUTH_DIR = "." # <--- *** ADJUST IF 'private.json' IS ELSEWHERE ***

# 3. SET THE GAME CODE (usually 'mlb' for baseball)
GAME_CODE = 'mlb'

# --- End Configuration ---

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
        # Initialize the YFPY client.
        # This handles the OAuth2 flow. It looks for 'private.json' in auth_dir.
        # If tokens are missing or expired, it will print a URL.
        # You MUST open that URL in a browser, log in to Yahoo, grant access,
        # and paste the resulting verification code back into the terminal.
        # This only needs to be done once initially or if the token expires.
        yfs = YahooFantasySports(auth_dir, league_id, game_code=game_code)
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
        team = yfs.get_team()
        if not team:
             print(f"Error: Could not retrieve your team for league ID {league_id}.")
             print("Is the LEAGUE_ID correct? Do you have a team in that league?")
             sys.exit(1)

        print(f"Successfully accessed team: {team.team_name}")

        # Get today's date for the roster query
        today = datetime.date.today()
        print(f"Checking roster and pitcher status for: {today.strftime('%Y-%m-%d')}")

        # Fetch the roster for today
        roster = team.get_roster(day=today)

        starting_pitchers_today = []
        other_sps_on_roster = []

        print("\n--- Analyzing Roster ---")
        for player in roster:
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

        # Optional: List other SPs for context
        # if other_sps_on_roster:
        #     print("\nOther SPs on your roster (not starting today):")
        #     for info in other_sps_on_roster:
        #         print(f"   - {info}")

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
