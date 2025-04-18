#!/usr/bin/env python3

import datetime
import os
import sys
from yfpy import YahooFantasySportsQuery # Make sure yfpy is installed

# --- Configuration ---

# 1. SET YOUR LEAGUE ID HERE:
#    Find this in the URL of your Yahoo Fantasy Baseball league page.
#    Example: If URL is https://baseball.fantasysports.yahoo.com/b1/123456, ID is "123456"
YAHOO_LEAGUE_ID = "41370" # <--- *** REPLACE THIS REQUIRED ***

# 2. SET THE PATH TO YOUR AUTHENTICATION DIRECTORY:
#    This is the directory where your 'private.json' file is located.
#    Use '.' for the current directory, or provide a full path like '/path/to/your/auth'.
#    Recommendation: Keep this directory separate from your script for security.
AUTH_DIR = "C:\\Users\\eamon\\Git_Repos\\starter_starter\\starter-starter\\yfpy\\" # <--- *** ADJUST IF 'private.json' IS ELSEWHERE ***

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
       

            # --- Debugging Loop for Specific Player by Name ---

        target_name = "Kris Bubic"  # <--- Set the player name you want to find

        print("\n" + "="*60)
        print(f"DEBUG: Searching Roster for Player: '{target_name}'")
        print("="*60)

        player_found_flag = False
        player_index = -1 # To keep track of the player's position in the original list

        # Assuming 'roster' is the list of player objects from team.get_roster(day=today)
        if not roster:
            print("Roster data is empty or not loaded.")
        else:
            for player in roster:
                player_index += 1 # Increment index for each player processed

                # Basic check: Ensure player object exists and has the necessary name attributes
                if not player or not hasattr(player, 'name') or not hasattr(player.name, 'full'):
                    print(f"\nSkipping item at index {player_index}: Not a valid player object or missing 'name.full' attribute.")
                    continue

                current_player_name = player.name.full

                # Check if the current player's full name matches the target name
                if current_player_name == target_name:
                    player_found_flag = True
                    print(f"\n--- Found Player: {target_name} ---")
                    print(f"Located at index in roster list: {player_index}")

                    # Print the standard object representation first (provided by yfpy)
                    print("\nStandard Object Representation:")
                    try:
                        print(player)
                    except Exception as e:
                        print(f"  - Error printing standard representation: {e}")


                    # Print all attributes using vars() for detailed inspection
                    print("\nAll Object Attributes (using vars()):")
                    try:
                        # vars(player) returns the __dict__ attribute (attributes and values)
                        attributes = vars(player)
                        if attributes: # Check if the dictionary is not empty
                            for key, value in attributes.items():
                                # Basic formatting for readability
                                value_str = repr(value) # Use repr() for unambiguous representation
                                if len(value_str) > 150: # Truncate very long values
                                    value_str = value_str[:147] + "..."
                                print(f"  - {key}: {value_str}")
                        else:
                            print("  - No attributes found via vars().")
                    except TypeError:
                        print("  - Could not retrieve attributes using vars() for this object (TypeError).")
                    except Exception as e:
                        print(f"  - An error occurred retrieving attributes: {e}")


                    print("-" * 50) # Separator for readability

                    # If you only expect one player with this name and want to stop
                    # after finding the first match, uncomment the next line:
                    # break

            # Summary message after checking the entire roster
            print("\n" + "="*60)
            if player_found_flag:
                print(f"Finished searching roster. Found '{target_name}'.")
            else:
                # If the player wasn't found, it might be helpful to list the names that WERE found
                print(f"Finished searching roster. Player '{target_name}' was NOT found.")
                print("\nNames found in the roster:")
                names_in_roster = [p.name.full for p in roster if hasattr(p, 'name') and hasattr(p.name, 'full')]
                if names_in_roster:
                    for i, name in enumerate(names_in_roster):
                        print(f"  {i+1}. {name}")
                else:
                    print("  - Could not extract any names from the roster data.")

            print("="*60)
        # --- End Debugging Loop ---




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
