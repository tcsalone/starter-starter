#!/usr/bin/env python3

import datetime
import os
import sys
import json
import argparse
import statsapi  # For fetching MLB starters
import yahoo_fantasy_api as yfa  # Yahoo Fantasy API
from yahoo_oauth import OAuth2  # For Yahoo authentication

# --- Configuration ---
YAHOO_LEAGUE_ID = "41370"  # <--- *** REPLACE THIS REQUIRED ***
league_id = "458.l.41370"
YAHOO_TEAM_ID = 2          # <--- *** VERIFY/REPLACE THIS REQUIRED (Your team's ID within the league) ***
AUTH_FILE = "private.json"  # OAuth2 credentials file
GAME_CODE = 'mlb'          # Game code for MLB
GAME_ID = '423'           # 2025 MLB Game ID (this can change each year)
ACTIVE_PITCHER_SLOTS = {'P', 'SP'}
BENCH_SLOT = 'BN'
# --- End Configuration ---

def prompt_for_target_date():
    """
    Prompt the user to select which day to operate for.
    Returns a datetime.date object.
    Defaults to today if no input is given.
    """
    today = datetime.date.today()
    options = {
        "1": ("Today", today),
        "2": ("Tomorrow", today + datetime.timedelta(days=1)),
        "3": ("Two days from now", today + datetime.timedelta(days=2))
    }
    print("\nWhich day do you want to operate for?")
    for k, (desc, date_obj) in options.items():
        print(f"{k}: {desc} ({date_obj.strftime('%A, %Y-%m-%d')})")
    choice = input("Enter 1 (today), 2 (tomorrow), or 3 (two days from now) [default: 1]: ").strip()
    if choice not in options:
        print("No valid input detected. Defaulting to today.")
        return today
    return options[choice][1]

def parse_args():
    parser = argparse.ArgumentParser(description="Yahoo Fantasy Pitcher Auto-Starter Script")
    parser.add_argument('--date', type=str, default=None,
                        help="Date to operate for (YYYY-MM-DD). Defaults to today.")
    parser.add_argument('--prompt', action='store_true',
                        help="Prompt for which day to operate for (overrides --date if both are set).")
    return parser.parse_args()

# --- MLB Pitcher Fetching Function ---
def get_mlb_starting_pitchers_for_date(target_date):
    date_str = target_date.strftime("%Y-%m-%d")
    print(f"Fetching MLB probable starters for date: {date_str}")

    try:
        schedule_data = statsapi.schedule(date=date_str)
    except Exception as e:
        print(f"Error fetching MLB schedule from statsapi: {e}")
        return None

    if not schedule_data:
        print("No MLB games found scheduled for this date via statsapi.")
        return set()

    starters = set()
    for game in schedule_data:
        home_pitcher = game.get("home_probable_pitcher")
        away_pitcher = game.get("away_probable_pitcher")
        if home_pitcher and home_pitcher != 'N/A':
            starters.add(home_pitcher)
        if away_pitcher and away_pitcher != 'N/A':
            starters.add(away_pitcher)
    if not starters:
        print("Could not identify any probable starting pitchers from MLB schedule data.")
    else:
        print(f"Identified {len(starters)} probable MLB starters for this date.")
    return starters

# --- Yahoo Authentication Helper ---
def ensure_auth_file(auth_dir, auth_file):
    if not os.path.exists(auth_dir):
        print(f"Authentication directory not found: {auth_dir}")
        try:
            os.makedirs(auth_dir)
            print(f"Created directory: {auth_dir}")
        except OSError as e:
            print(f"Error: Could not create directory {auth_dir}. Please create it manually. Error: {e}")
            return False

    if not os.path.isfile(auth_file):
        print(f"\nError: OAuth2 authentication file not found: {auth_file}")
        print("\nPlease create 'oauth2.json' in that directory with your")
        print("Yahoo App 'consumer_key' and 'consumer_secret'. Format:")
        print("""
{
    "consumer_key": "YOUR_YAHOO_CONSUMER_KEY",
    "consumer_secret": "YOUR_YAHOO_CONSUMER_SECRET"
}
        """)
        print("You can create a Yahoo App key/secret here:")
        print("https://developer.yahoo.com/apps/create/")
        return False
    return True

# --- Main Fantasy Roster Management Function ---
def manage_fantasy_pitchers(league_id, team_id, game_code, auth_file, target_date):
    """
    Main function to manage fantasy baseball pitchers.
    Fetches starters, analyzes the roster, and submits changes.
    """
    actual_starters_set = get_mlb_starting_pitchers_for_date(target_date)
    if actual_starters_set is None:
        print("Exiting due to error fetching MLB starters.")
        sys.exit(1)
    if not actual_starters_set:
        print("No probable MLB starters identified for this date. No roster changes needed.")
        sys.exit(0)

    if league_id == "YOUR_LEAGUE_ID":
        print("*"*60)
        print("ERROR: Please update the 'YAHOO_LEAGUE_ID' variable at the top")
        print("       of the script with your actual Yahoo League ID.")
        print("*"*60)
        sys.exit(1)

    print("\nAttempting to authenticate with Yahoo Fantasy Sports...")
    try:
        sc = OAuth2(None, None, from_file=auth_file)
        if not sc.token_is_valid():
            print("Token expired or missing, re-authenticating...")
            sc.refresh_access_token()
        gm = yfa.Game(sc, game_code)
        # Using a fixed league_id as per original script's logic
        lg = gm.to_league(f"{gm.game_id()}.l.{league_id}")
        tm = lg.to_team(f"{gm.game_id()}.l.{league_id}.t.{team_id}")
        print("Authentication and API initialization successful.")
    except Exception as e:
        print(f"\nError initializing Yahoo Fantasy API: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    try:
        date_str = target_date.strftime("%Y-%m-%d")
        print(f"Fetching your Yahoo! Fantasy Baseball team roster for: {date_str}")
        roster = tm.roster(day=target_date)
        if not roster:
            print("Error: Could not fetch roster data.")
            sys.exit(1)
        print(f"Successfully fetched roster with {len(roster)} players.")
    except Exception as e:
        print(f"\nAn error occurred while fetching fantasy team data: {e}")
        sys.exit(1)

    players_to_start = []
    players_to_bench = []

    print("\n--- Roster Analysis ---")
    for player in roster:
        player_name = player['name']
        current_position = player['selected_position']
        eligible_positions = player['eligible_positions']

        # Skip non-pitchers and players on IL/NA etc. from this logic
        is_eligible_pitcher = any(pos in ACTIVE_PITCHER_SLOTS for pos in eligible_positions)
        if not is_eligible_pitcher or current_position in ['IL', 'NA', 'G', 'DTD']:
            continue
        
        is_starting_today = player_name in actual_starters_set
        status_detail = f" (Status: {player['status']})" if player.get('status') else ""
        elig_pos_str = "/".join(eligible_positions)
        
        print(f"Processing: {player_name:<25} | Eligible: {elig_pos_str:<7} | Current Pos: {current_position:<3} | MLB Start Today? {is_starting_today}{status_detail}")

        if current_position in ACTIVE_PITCHER_SLOTS:
            if not is_starting_today:
                players_to_bench.append(player)
                print(f"    -> Candidate to BENCH (Currently Active, Not starting today)")
        elif current_position == BENCH_SLOT:
            if is_starting_today:
                # Double check player isn't on an injury list status from Yahoo's perspective
                if player.get('status') in ['IL', 'DTD', 'NA', 'IL60']:
                     print(f"    -> On Bench & MLB Starter, BUT INJURED ({player.get('status')}). Skipping activation.")
                else:
                    players_to_start.append(player)
                    print(f"    -> Candidate to START (Currently on Bench, Starting today)")
    
    print("\n--- Determining Roster Changes ---")
    roster_changes = {} # Use a dict to track final state: {player_id: new_position}
    
    # Pool of players that can be benched. We will remove from this pool as we use their slots.
    benchable_player_pool = list(players_to_bench)
    
    print(f"Starters needing activation: {[p['name'] for p in players_to_start]}")
    print(f"Active players to be benched: {[p['name'] for p in players_to_bench]}")
    
    for player_to_activate in players_to_start:
        activated = False
        # Find a player to swap with from our pool of benchable players
        for player_to_deactivate in benchable_player_pool:
            open_slot = player_to_deactivate['selected_position']
            
            # Check if the player to activate is eligible for the open slot
            if open_slot in player_to_activate['eligible_positions']:
                print(f"Action: Move {player_to_activate['name']} (BN) to {open_slot}, "
                      f"Move {player_to_deactivate['name']} ({open_slot}) to BN")
                
                # Assign the activating player to the newly opened slot
                roster_changes[player_to_activate['player_id']] = open_slot
                # Assign the deactivating player to the bench
                roster_changes[player_to_deactivate['player_id']] = BENCH_SLOT
                
                # Remove the benched player from the pool so we don't use their slot again
                benchable_player_pool.remove(player_to_deactivate)
                activated = True
                break # Move to the next player_to_activate

        if not activated:
            print(f"Could not activate {player_to_activate['name']}: No suitable active P/SP slot was available to swap into.")

    if not roster_changes:
        print("\nNo lineup changes required or possible based on today's starters.")
        sys.exit(0)

    print("\n--- Submitting Roster Changes ---")
    try:
        # The API requires the full lineup, so start with the current one
        current_lineup = {p['player_id']: p['selected_position'] for p in roster}
        
        # Update the lineup with our calculated changes
        for player_id, new_position in roster_changes.items():
            # Find player name for logging
            player_name = next((p['name'] for p in roster if p['player_id'] == player_id), "Unknown")
            print(f"  - Setting {player_name} (ID: {player_id}) to position {new_position}")
            current_lineup[player_id] = new_position
        
        # Format for the API: list of dicts
        final_lineup_submission = [{'player_id': pid, 'selected_position': pos} for pid, pos in current_lineup.items()]
        
        print(f"\nSubmitting lineup changes for date: {target_date}")
        tm.change_positions(target_date, final_lineup_submission)
        print("\nSUCCESS: Roster changes submitted to Yahoo! ✅")

    except Exception as e:
        print(f"\nERROR: Failed to submit roster changes to Yahoo: {e}")
        print(f"Error Type: {type(e).__name__}")
        print("\nNo changes were made.")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# --- Run the main function ---
if __name__ == "__main__":
    print("="*60)
    print("Starting Yahoo Fantasy Pitcher Auto-Starter Script")
    print(f"Time: {datetime.datetime.now()}")
    print("="*60)
    print(f"Using League ID: {YAHOO_LEAGUE_ID}")
    print(f"Using Team ID:   {YAHOO_TEAM_ID}")
    print(f"Using Auth File: {AUTH_FILE}")
    print("\nWARNING: This script WILL attempt to modify your live Yahoo Fantasy lineup.")
    print("Review the logic and configuration carefully before proceeding.")

    args = parse_args()

    if args.prompt:
        target_date = prompt_for_target_date()
    elif args.date:
        try:
            target_date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD. Defaulting to today.")
            target_date = datetime.date.today()
    else:
        target_date = datetime.date.today()

    manage_fantasy_pitchers(YAHOO_LEAGUE_ID, YAHOO_TEAM_ID, GAME_CODE, AUTH_FILE, target_date)

    print("\nScript execution finished.")