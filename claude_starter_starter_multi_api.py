#!/usr/bin/env python3

import datetime
import os
import sys
import json
import statsapi  # For fetching MLB starters
import yahoo_fantasy_api as yfa  # Yahoo Fantasy API
from yahoo_oauth import OAuth2  # For Yahoo authentication

# --- Configuration ---
YAHOO_LEAGUE_ID = "41370"  # <--- *** REPLACE THIS REQUIRED ***
league_id = "458.l.41370"
YAHOO_TEAM_ID = 2          # <--- *** VERIFY/REPLACE THIS REQUIRED (Your team's ID within the league) ***
AUTH_DIR = "C:\\Users\\eamon\\Git_Repos\\starter_starter\\starter-starter\\"
AUTH_FILE = os.path.join(AUTH_DIR, "private.json")  # OAuth2 credentials file
GAME_CODE = 'mlb'          # Game code for MLB
GAME_ID = '423'           # 2025 MLB Game ID (this can change each year)
# Roster positions considered active pitcher slots
ACTIVE_PITCHER_SLOTS = {'P', 'SP'}
BENCH_SLOT = 'BN'
# --- End Configuration ---

# --- MLB Pitcher Fetching Function ---
def get_todays_mlb_starting_pitchers():
    """
    Fetches today's MLB probable starting pitchers using mlb-statsapi.

    Returns:
        set: A set containing the full names of probable starting pitchers,
             or None if an error occurs or no games are scheduled.
    """
    
    #uncomment me
    #today = datetime.date.today()
    #today_str = today.strftime("%Y-%m-%d")

    #test code
    today = datetime.date.today()
    future_date = today + datetime.timedelta(days=2)
    today_str = future_date.strftime("%Y-%m-%d")
    
    print(f"Fetching MLB probable starters for date: {today_str}")

    try:
        schedule_data = statsapi.schedule(date=today_str)
    except Exception as e:
        print(f"Error fetching MLB schedule from statsapi: {e}")
        return None

    if not schedule_data:
        print("No MLB games found scheduled for today via statsapi.")
        return set()  # Return empty set if no games

    actual_starters_names = set()
    for game in schedule_data:
        # Extract probable pitcher names, default to None if not found
        home_pitcher = game.get("home_probable_pitcher")
        away_pitcher = game.get("away_probable_pitcher")

        if home_pitcher and home_pitcher != 'N/A':
            actual_starters_names.add(home_pitcher)
        if away_pitcher and away_pitcher != 'N/A':
            actual_starters_names.add(away_pitcher)

    if not actual_starters_names:
        print("Could not identify any probable starting pitchers from MLB schedule data.")
    else:
        print(f"Identified {len(actual_starters_names)} probable MLB starters for today.")

    return actual_starters_names

# --- Yahoo Authentication Helper ---
def ensure_auth_file(auth_dir, auth_file):
    """
    Ensures authentication directory exists and checks for oauth2.json file.
    If not found, provides guidance on how to create it.
    """
    # Create auth directory if it doesn't exist
    if not os.path.exists(auth_dir):
        print(f"Authentication directory not found: {auth_dir}")
        try:
            os.makedirs(auth_dir)
            print(f"Created directory: {auth_dir}")
        except OSError as e:
            print(f"Error: Could not create directory {auth_dir}. Please create it manually. Error: {e}")
            return False

    # Check for auth file
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
def manage_fantasy_pitchers(league_id, team_id, game_code, auth_file):
    """
    Main function to fetch starters, get roster, compare, and modify lineup.
    """
    # --- Step 1: Get Today's MLB Starters ---
    actual_starters_set = get_todays_mlb_starting_pitchers()
    if actual_starters_set is None:
        print("Exiting due to error fetching MLB starters.")
        sys.exit(1)
    if not actual_starters_set:
        print("No probable MLB starters identified today. No roster changes needed based on this.")
        sys.exit(0)

    # --- Step 2: Authenticate and Setup Yahoo Query ---
    if league_id == "YOUR_LEAGUE_ID":
        print("*"*60)
        print("ERROR: Please update the 'YAHOO_LEAGUE_ID' variable at the top")
        print("       of the script with your actual Yahoo League ID.")
        print("*"*60)
        sys.exit(1)

    if not ensure_auth_file(AUTH_DIR, auth_file):
        sys.exit(1)  # Exit if auth setup is missing

    print("\nAttempting to authenticate with Yahoo Fantasy Sports...")
    try:
        # Initialize OAuth2 with your auth file
        sc = OAuth2(None, None, from_file=auth_file)
        
        # Check if token is valid, refresh if needed
        if not sc.token_is_valid():
            print("Token expired or missing, initiating browser auth...")
            sc.refresh_access_token()  # This will trigger the browser auth flow if needed
            
        # Get the game object
        gm = yfa.Game(sc, game_code)
        
        # Get the league ID for current year if not specified
        if not league_id.isdigit():  # If league_id is not a simple number
            league_id = gm.league_ids(year=datetime.date.today().year)[0]
            print(f"Using league ID: {league_id}")
        league_id = "458.l.41370"    
        # Get the league using the authenticated game object
        lg = gm.to_league(league_id)
        print(lg)
        # Get the team using the league object
        tm = lg.to_team("458.l.41370.t.2")
        
        print("Authentication and API initialization successful.")
    except Exception as e:
        print(f"\nError initializing Yahoo Fantasy API: {e}")
        print(f"Error details: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # --- Step 3: Get Fantasy Team Roster ---
    try:
        # Get tomorrow's date for roster planning
        #today = datetime.date.today()
        #today_str = today.strftime("%Y-%m-%d")

        #testing code for Wed        
        today = datetime.date.today()
        future_date = today + datetime.timedelta(days=2)
        today_str = future_date.strftime("%Y-%m-%d")

        print(f"Fetching your Yahoo! Fantasy Baseball team roster for: {today_str}")
        
        # Fetch current roster
        roster = tm.roster()
        
        if not roster:
            print("Error: Could not fetch roster data.")
            sys.exit(1)
            
        print(f"Successfully fetched roster with {len(roster)} players.")
    except Exception as e:
        print(f"\nAn error occurred while fetching fantasy team data: {e}")
        print("\nPossible causes:")
        print("- Invalid YAHOO_LEAGUE_ID or YAHOO_TEAM_ID.")
        print("- Network connection issues or temporary Yahoo API issues.")
        sys.exit(1)
    
    # --- Step 4 & 5: Analyze Roster and Identify Swaps ---
    players_to_start = []  # Players who ARE starting today but are on BENCH
    players_to_bench = []  # Players who are NOT starting today but are ACTIVE (P/SP)
    active_pitcher_slots = {}  # Dict of active pitcher slots
    bench_pitchers = []  # List of pitchers on bench

    # Get all player details keyed by player_id for quick lookup
    player_details = {}
    for player in roster:
        player_details[player['player_id']] = player
    
    # Classify players on the roster
    for player in roster:
        player_name = player['name']
        player_id = player['player_id']
        current_position = player['selected_position']
        eligible_positions = player['eligible_positions']
        
        # Check if player is a pitcher eligible for active slots
        is_eligible_pitcher = any(pos in ACTIVE_PITCHER_SLOTS for pos in eligible_positions)
        
        # Skip non-pitchers or players with unknown positions
        if not is_eligible_pitcher or not current_position:
            continue
            
        is_starting_today = player_name in actual_starters_set
        status_detail = f" (Status: {player['status']})" if 'status' in player and player['status'] else ""
        elig_pos = "/".join(eligible_positions)
        
        print(f"Processing: {player_name:<25} | Eligible: {elig_pos:<5} | Current Pos: {current_position:<3} | MLB Start Today? {is_starting_today} {status_detail}")
        
        if current_position in ACTIVE_PITCHER_SLOTS:
            active_pitcher_slots[current_position] = player
            if not is_starting_today:
                players_to_bench.append(player)
                print(f"    -> Candidate to BENCH (Currently Active: {current_position}, Not starting today)")
                
        elif current_position == BENCH_SLOT:
            bench_pitchers.append(player)
            if is_starting_today:
                # Add injury check - don't try to start injured players
                if 'status' in player and player['status'] in ['IL', 'DTD', 'NA']:
                    print(f"    -> On Bench & MLB Starter, BUT INJURED ({player['status']}). Skipping activation.")
                else:
                    players_to_start.append(player)
                    print(f"    -> Candidate to START (Currently Bench, Starting today)")
    
    # --- Step 6: Determine Roster Changes ---
    print("\n--- Determining Roster Changes ---")
    roster_changes = []  # List of moves to make
    
    # Try to move starters from Bench to Active slots
    available_active_slots = list(ACTIVE_PITCHER_SLOTS)  # Start with all possible slots
    
    # Remove slots occupied by starters who are already active and are starting today
    active_keepers = []
    for position, player in active_pitcher_slots.items():
        if player['name'] in actual_starters_set:
            print(f"Keeping {player['name']} in active slot {position} (already starting).")
            if position in available_active_slots:
                available_active_slots.remove(position)
            active_keepers.append(player)
            
    print(f"Available Active Pitcher Slots for swaps: {available_active_slots}")
    print(f"Starters needing activation from bench: {[p['name'] for p in players_to_start]}")
    print(f"Active players needing benching: {[p['name'] for p in players_to_bench]}")
    
    # Prioritize starting the players who should be starting
    for player_to_activate in players_to_start:
        if not available_active_slots:
            print(f"Cannot activate {player_to_activate['name']}: No suitable active P/SP slots remaining.")
            break  # Stop trying to activate if no slots left
            
        # Find an active non-starter to bench
        player_to_deactivate = None
        for p in players_to_bench:
            # Check if this player hasn't already been marked for a swap
            if not any(change['player_id'] == p['player_id'] for change in roster_changes):
                player_to_deactivate = p
                break  # Found someone to bench
                
        if player_to_deactivate:
            target_slot = player_to_deactivate['selected_position']  # Take the slot being vacated
            if target_slot not in available_active_slots:
                print(f"Warning: Slot {target_slot} needed for {player_to_activate['name']} but wasn't listed as available. Trying next.")
                continue
                
            print(f"Action: Move {player_to_activate['name']} (BN) to {target_slot}, Move {player_to_deactivate['name']} ({target_slot}) to BN")
            
            # Add changes to the list
            roster_changes.append({
                'player_id': player_to_activate['player_id'],
                'name': player_to_activate['name'],
                'current_position': player_to_activate['selected_position'],
                'target_position': target_slot
            })
            roster_changes.append({
                'player_id': player_to_deactivate['player_id'],
                'name': player_to_deactivate['name'],
                'current_position': player_to_deactivate['selected_position'],
                'target_position': BENCH_SLOT
            })
            
            # Update state for next iteration
            available_active_slots.remove(target_slot)
            players_to_bench.remove(player_to_deactivate)  # Don't bench this player again
            
        else:
            print(f"Cannot activate {player_to_activate['name']}: No non-starting players found in active P/SP slots to swap out.")
    
    if not roster_changes:
        print("\nNo lineup changes required or possible based on today's starters.")
        sys.exit(0)
        
    # --- Step 7: Execute Lineup Changes ---
    # --- Step 7: Execute Lineup Changes ---
    print("\n--- Submitting Roster Changes ---")

    success = True
    try:
        # We need to create a list of position changes in the format the API expects
        # The format should be: [{'player_id': 12345, 'selected_position': 'SP'}, {'player_id': 67890, 'selected_position': 'BN'}]
        position_changes = []
        
        # First, record all players' current positions
        for player in roster:
            # Create a simplified player dict with only the fields needed
            position_changes.append({
                'player_id': player['player_id'],  # Use numeric ID, not the full key
                'selected_position': player['selected_position']  # IMPORTANT: Use 'selected_position', not 'position'
            })
        
        # Now apply the changes
        print("Applying position changes:")
        for change in roster_changes:
            player_id = change['player_id']
            new_position = change['target_position']
            
            # Find and update the player in position_changes
            for player_change in position_changes:
                if player_change['player_id'] == player_id:
                    player_change['selected_position'] = new_position  # Use 'selected_position', not 'position'
                    print(f"  - Setting {change['name']} (ID: {player_id}) to position {new_position}")
                    break
        
        # Get today's date as a datetime.date object
        today = datetime.date.today()

        today = today + datetime.timedelta(days=2)
        today_str = future_date.strftime("%Y-%m-%d")
        
        # Print our complete position changes before making the API call
        print("\nFull position changes to be submitted:")
        for change in position_changes:
            # Find player name for better logging
            player_name = "Unknown"
            for player in roster:
                if player['player_id'] == change['player_id']:
                    player_name = player['name']
                    break
            print(f"  Player: {player_name} (ID: {change['player_id']}) - Position: {change['selected_position']}")
        
        # Try to make the API call with the correct format
        print(f"\nSubmitting lineup changes for date: {today}")
        try:
            result = tm.change_positions(today, position_changes)
            print(f"Edit lineup API result: {result}")
            success = True
        except Exception as e:
            print(f"API call failed: {e}")
            print("Checking the first entry in position_changes:")
            if position_changes and len(position_changes) > 0:
                print(f"First entry keys: {position_changes[0].keys()}")
            raise

    except Exception as e:
        print(f"\nERROR: Failed to submit roster changes to Yahoo: {e}")
        print(f"Error Type: {type(e).__name__}") # Print error type
        print("\nPotential Reasons:")
        print("- Yahoo Fantasy API expects a different format for player IDs or position dictionary.")
        print("- API Error from Yahoo (e.g., invalid move, locked roster, game started).")
        print("- Permissions issues with your Yahoo App credentials.")
        print("\nNo changes were made.")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    if success:
        print("\nSUCCESS: Roster changes submitted to Yahoo!")
    else:
        print("\nWARNING: Roster changes submission might have failed or had issues.")

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
    # input("Press Enter to continue or Ctrl+C to cancel...")  # Optional safety prompt

    manage_fantasy_pitchers(YAHOO_LEAGUE_ID, YAHOO_TEAM_ID, GAME_CODE, AUTH_FILE)

    print("\nScript execution finished.")