#!/usr/bin/env python3

import datetime
import os
import sys
import statsapi # For fetching MLB starters
from yfpy import YahooFantasySportsQuery # For Yahoo Fantasy interaction

# --- Configuration ---
YAHOO_LEAGUE_ID = "41370"  # <--- *** REPLACE THIS REQUIRED ***
YAHOO_TEAM_ID = 2                   # <--- *** VERIFY/REPLACE THIS REQUIRED (Your team's ID within the league) ***
#AUTH_DIR = os.path.expanduser("~/yfpy_auth") # <--- *** ADJUST THIS PATH TO YOUR PREFERRED AUTH DIRECTORY ***
AUTH_DIR = "C:\\Users\\eamon\\Git_Repos\\starter_starter\\starter-starter\\starter_starter_multi_call\\"
GAME_CODE = 'mlb'                   # Game code for MLB
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
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")
    today = datetime.date.today()
    tomorrow_date = today + datetime.timedelta(days=1)
    today_str = tomorrow_date.strftime("%Y-%m-%d")
    print(f"Fetching MLB probable starters for date: {today_str}")

    try:
        schedule_data = statsapi.schedule(date=today_str)
    except Exception as e:
        print(f"Error fetching MLB schedule from statsapi: {e}")
        return None

    if not schedule_data:
        print("No MLB games found scheduled for today via statsapi.")
        return set() # Return empty set if no games

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
        # print("Debug - Actual Starters:", actual_starters_names) # Uncomment for debugging

    return actual_starters_names

# --- Yahoo Authentication Helper ---
def ensure_auth_dir_and_private_json(auth_dir):
    """Checks if auth directory and private.json exist, providing guidance."""
    private_json_path = os.path.join(auth_dir, "private.json")

    # Create auth directory if it doesn't exist
    if not os.path.exists(auth_dir):
        print(f"Authentication directory not found: {auth_dir}")
        try:
            os.makedirs(auth_dir)
            print(f"Created directory: {auth_dir}")
        except OSError as e:
            print(f"Error: Could not create directory {auth_dir}. Please create it manually. Error: {e}")
            return False

    # Check for private.json
    if not os.path.isfile(private_json_path):
        print(f"\nError: 'private.json' not found in directory: {auth_dir}")
        print("\nPlease create 'private.json' in that directory with your")
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
def manage_fantasy_pitchers(league_id, team_id, game_code, auth_dir):
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
        # Decide if you want to exit or continue to potentially bench non-starters
        # For now, we'll exit as the primary goal is to start the starters.
        sys.exit(0)


    # --- Step 2: Authenticate and Setup Yahoo Query ---
    if league_id == "YOUR_LEAGUE_ID":
        print("*"*60)
        print("ERROR: Please update the 'YAHOO_LEAGUE_ID' variable at the top")
        print("       of the script with your actual Yahoo League ID.")
        print("*"*60)
        sys.exit(1)

    if not ensure_auth_dir_and_private_json(auth_dir):
        sys.exit(1) # Exit if auth setup is missing

    print("\nAttempting to authenticate with Yahoo Fantasy Sports...")
    try:
        # Instantiate yfpy - it will read private.json from auth_dir
        # Note: Constructor arguments might vary slightly based on yfpy version.
        # Common signature: YahooFantasySportsQuery(auth_dir, league_id, game_id=game_code)
        # Check yfpy docs if needed. Adjusting based on user's previous script:
        #>>this was original yfs = YahooFantasySportsQuery(auth_dir=auth_dir, league_id=league_id, game_id=game_code)
        # yfs = YahooFantasySportsQuery(league_id, auth_dir=auth_dir, game_code=game_code) # Alternative if above fails
        yfs = YahooFantasySportsQuery(YAHOO_LEAGUE_ID, AUTH_DIR, GAME_CODE, yahoo_consumer_key="dj0yJmk9WVhKSVk2Vm5HNVBFJmQ9WVdrOVEwRklWbGhyUjBNbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PWJh", yahoo_consumer_secret="00bc06f768688f8aab80164babc32117e5a69d96")

        # Accessing a property forces authentication if token expired/missing
        #_ = yfs.league().settings()
        print("Authentication successful (or cached token used).")

    except Exception as e:
        print(f"\nError during Yahoo authentication or initialization: {e}")
        print(f"Auth Directory used: {auth_dir}")
        print("\nTroubleshooting:")
        print(f"- Ensure '{os.path.join(auth_dir, 'private.json')}' exists and is correctly formatted.")
        print("- Ensure the consumer key/secret in 'private.json' are valid and match your Yahoo App.")
        print("- If prompted for browser authentication (first time), ensure you complete the steps.")
        print("- Check your internet connection.")
        sys.exit(1)

    # --- Step 3: Get Fantasy Team Roster ---
    try:
        today = datetime.date.today()
        tomorrow_date = today + datetime.timedelta(days=1)
        today_str = tomorrow_date.strftime("%Y-%m-%d")
        print(f"Fetching your Yahoo! Fantasy Baseball team as for: {today_str}")
        
        print(f"\nAccessing your team (ID: {team_id}) in league {league_id}...")
        # Get the team object first (needed for some yfpy operations)
        ##team = yfs.get_team_info(f"{yfs.league_key()}.t.{team_id}")
        #team = yfs.get_team_info(2)
        roster = yfs.get_team_roster_player_info_by_date(2, today_str)
        #print(roster)
        '''
        if not team:
             print(f"Error: Could not retrieve team object for Team ID {team_id} in league {league_id}.")
             print("Is the LEAGUE_ID and TEAM_ID correct? Do you own this team?")
             sys.exit(1)

        print(f"Successfully accessed team: {team.name()}") # Use team.name() method

        # Get today's date for the roster query
        today = datetime.date.today()
        today_str = today.strftime('%Y-%m-%d')
        print(f"Fetching roster for date: {today_str}")

        # Fetch the roster for today using the team object
        roster = team.roster(day=today) # Fetches player info for that date

        if not roster:
            print("Error: Could not fetch roster for today.")
            sys.exit(1)

        print(f"Successfully fetched roster with {len(roster)} players.")
        '''

    except Exception as e:
        print(f"\nAn error occurred while fetching fantasy team data: {e}")
        print("\nPossible causes:")
        print("- Invalid YAHOO_LEAGUE_ID or YAHOO_TEAM_ID.")
        print("- Network connection issues or temporary Yahoo API issues.")
        print("- Changes in the yfpy library or Yahoo API structure.")
        sys.exit(1)
        


    # --- Step 4 & 5: Analyze Roster and Identify Swaps ---
    print("\n--- Analyzing Roster vs MLB Starters ---")
    players_to_start = [] # List of player objects (from roster) who ARE starting today but are on BENCH
    players_to_bench = [] # List of player objects (from roster) who are NOT starting today but are ACTIVE (P/SP)
    active_pitcher_players = {} # Dict {position: player_object} for players currently in P/SP slots
    bench_pitcher_players = {} # Dict {player_key: player_object} for pitchers currently on BN

    # Classify players on the roster
    for player in roster:
        player_name = player.name.full
        print("player name", player_name)
        player_key = player.player_key # Needed for roster updates
        print("player key", player_key)
        current_position = player.selected_position.position
        print("current position", current_position)
        #is_eligible_pitcher = any(pos.position in ACTIVE_PITCHER_SLOTS for pos in player.eligible_positions) # Check if SP or P eligible
        is_eligible_pitcher = any(pos in ACTIVE_PITCHER_SLOTS for pos in player.eligible_positions) # Check if SP or P eligible


        # Skip non-pitchers or players with unknown positions
        if not is_eligible_pitcher or not current_position:
            # print(f"Skipping {player_name} (Not eligible pitcher or no current position)")
            continue

        is_starting_today = player_name in actual_starters_set
        status_detail = f" (Status: {player.status})" if hasattr(player, 'status') and player.status else ""
        #elig_pos = "/".join(p.position for p in player.eligible_positions)
        elig_pos = "/".join(player.eligible_positions)

        print(f"Processing: {player_name:<25} | Eligible: {elig_pos:<5} | Current Pos: {current_position:<3} | MLB Start Today? {is_starting_today} {status_detail}")

        if current_position in ACTIVE_PITCHER_SLOTS:
            active_pitcher_players[current_position] = player # Store player object by current position
            if not is_starting_today:
                players_to_bench.append(player)
                print(f"    -> Candidate to BENCH (Currently Active: {current_position}, Not starting today)")

        elif current_position == BENCH_SLOT:
            bench_pitcher_players[player_key] = player # Store by key for easy lookup
            if is_starting_today:
                # Add injury check - don't try to start injured players
                if hasattr(player, 'status') and player.status in ['IL', 'DTD', 'NA']:
                     print(f"    -> On Bench & MLB Starter, BUT INJURED ({player.status}). Skipping activation.")
                else:
                    players_to_start.append(player)
                    print(f"    -> Candidate to START (Currently Bench, Starting today)")


    # --- Step 6: Determine and Execute Roster Changes ---
    print("\n--- Determining Roster Changes ---")
    lineup_changes = {} # Key: player_key, Value: target_position

    # Try to move starters from Bench to Active slots
    available_active_slots = list(ACTIVE_PITCHER_SLOTS) # Start with all possible slots

    # Remove slots occupied by starters who are *already* active and *are* starting today
    active_keepers = []
    for position, player in active_pitcher_players.items():
        if player.name.full in actual_starters_set:
            print(f"Keeping {player.name.full} in active slot {position} (already starting).")
            if position in available_active_slots:
                available_active_slots.remove(position)
            active_keepers.append(player)

    print(f"Available Active Pitcher Slots for swaps: {available_active_slots}")
    print(f"Starters needing activation from bench: {[p.name.full for p in players_to_start]}")
    print(f"Active players needing benching: {[p.name.full for p in players_to_bench]}")


    # Prioritize starting the players who should be starting
    for player_to_activate in players_to_start:
        if not available_active_slots:
            print(f"Cannot activate {player_to_activate.name.full}: No suitable active P/SP slots remaining or available to free up.")
            break # Stop trying to activate if no slots left

        # Option 1: Use an empty slot if available (less common, usually requires finding someone to bench)
        # Need yfpy feature to check for empty slots, complex. Focusing on swaps.

        # Option 2: Find an active non-starter to bench
        player_to_deactivate = None
        for p in players_to_bench:
             # Check if this player hasn't already been marked for a swap
             if p.player_key not in lineup_changes:
                player_to_deactivate = p
                break # Found someone to bench

        if player_to_deactivate:
            target_slot = player_to_deactivate.selected_position.position # Take the slot being vacated
            if target_slot not in available_active_slots:
                # This shouldn't happen based on logic, but safety check
                print(f"Warning: Slot {target_slot} needed for {player_to_activate.name.full} but wasn't listed as available. Trying next.")
                continue

            print(f"Action: Move {player_to_activate.name.full} (BN) to {target_slot}, Move {player_to_deactivate.name.full} ({target_slot}) to BN")

            # Add changes to the list
            lineup_changes[player_to_activate.player_key] = target_slot
            lineup_changes[player_to_deactivate.player_key] = BENCH_SLOT

            # Update state for next iteration
            available_active_slots.remove(target_slot)
            players_to_bench.remove(player_to_deactivate) # Don't bench this player again

        else:
            # This happens if we have starters on bench, but everyone currently active is *also* starting today
            print(f"Cannot activate {player_to_activate.name.full}: No non-starting players found in active P/SP slots to swap out.")
            # Optional: Could check for empty slots here if yfpy supports it easily

    if not lineup_changes:
        print("\nNo lineup changes required or possible based on today's starters.")
        sys.exit(0)

    # --- Step 7: Execute Lineup Change via yfpy ---
    print("\n--- Submitting Roster Changes ---")
    print("Changes to submit:")
    # Convert to the list format expected by set_daily_roster
    roster_update_payload = []
    for player_key, target_pos in lineup_changes.items():
        print(f"  - Player Key: {player_key} -> Position: {target_pos}")
        roster_update_payload.append({'player_key': player_key, 'position': target_pos})

    # Add players NOT involved in the swap back into the payload with their CURRENT position
    # This is often required by Yahoo API - you must submit the *entire* target roster state
    print("Adding players whose positions are unchanged...")
    all_player_keys_in_update = set(lineup_changes.keys())

    for player in roster:
        if player.player_key not in all_player_keys_in_update:
             # Only add players with a current position (avoids issues with empty/invalid states)
            if hasattr(player, 'selected_position') and player.selected_position.position:
                print(f"  - Keeping Player Key: {player.player_key} at Position: {player.selected_position.position}")
                roster_update_payload.append({'player_key': player.player_key, 'position': player.selected_position.position})
            # else: # Uncomment for debug
            #     print(f"  - Skipping player {player.name.full} (Key: {player.player_key}) - No current position found in roster data.")


    if not roster_update_payload:
         print("Error: Roster update payload is empty. Cannot submit changes.")
         sys.exit(1)

    print(f"\nAttempting to set roster for date: {today_str}")
    try:
        # *** THIS IS THE CRITICAL API CALL - VERIFY METHOD AND PARAMETERS WITH yfpy DOCUMENTATION ***
        # Assuming team object has set_daily_roster method: team.set_daily_roster(players, date)
        # where players is a list of {'player_key': key, 'position': pos} dicts
        #team.set_daily_roster(roster_update_payload, today)
        roster.set_daily_roster(roster_update_payload, today)
        print("\nSUCCESS: Roster changes submitted to Yahoo!")

    except Exception as e:
        print(f"\nERROR: Failed to submit roster changes to Yahoo: {e}")
        print("\nPotential Reasons:")
        print("- API Error from Yahoo (e.g., invalid move, locked roster, game started).")
        print("- Incorrectly formatted roster_update_payload.")
        print("- Issues with yfpy library method or parameters.")
        print("- Permissions issues with your Yahoo App Key.")
        print("\nNo changes were made.")
        sys.exit(1)

# --- Run the main function ---
if __name__ == "__main__":
    print("="*60)
    print("Starting Yahoo Fantasy Pitcher Auto-Starter Script")
    print(f"Time: {datetime.datetime.now()}")
    print("="*60)
    print(f"Using League ID: {YAHOO_LEAGUE_ID}")
    print(f"Using Team ID:   {YAHOO_TEAM_ID}")
    print(f"Using Auth Dir:  {AUTH_DIR}")
    print("\nWARNING: This script WILL attempt to modify your live Yahoo Fantasy lineup.")
    print("Review the logic and configuration carefully before proceeding.")
    # input("Press Enter to continue or Ctrl+C to cancel...") # Optional safety prompt

    manage_fantasy_pitchers(YAHOO_LEAGUE_ID, YAHOO_TEAM_ID, GAME_CODE, AUTH_DIR)

    print("\nScript execution finished.")