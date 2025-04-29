#!/usr/bin/env python3
"""
Script to automatically manage Yahoo Fantasy Baseball pitcher lineups based on
MLB probable starters for the current day. It moves starting pitchers from the
bench to active slots (P/SP) and benches active pitchers who are not starting.
"""

import datetime
import os
import sys
import logging # Using logging for better output control
import statsapi # For fetching MLB starters
import yahoo_fantasy_api as yfa # Yahoo Fantasy API
from yahoo_oauth import OAuth2 # For Yahoo authentication

# --- Configuration ---
# ---> REQUIRED: Replace with your Yahoo League ID (numeric part) <---
YAHOO_LEAGUE_ID = "41370"
# ---> REQUIRED: Replace with your Yahoo Team ID (numeric part) <---
YAHOO_TEAM_ID = 2

# --- Optional Configuration ---
# Directory containing the 'private.json' credentials file
AUTH_DIR = "C:\\Users\\eamon\\Git_Repos\\starter_starter\\starter-starter\\"
AUTH_FILE = os.path.join(AUTH_DIR, "private.json") # OAuth2 credentials file

GAME_CODE = 'mlb' # Game code for MLB (usually 'mlb')
# Define which roster positions count as active pitcher slots
ACTIVE_PITCHER_SLOTS = {'P', 'SP'}
BENCH_SLOT = 'BN'
# Set the date for which to fetch starters and set the lineup.
# Default is today. Change timedelta(days=X) for testing future dates.
TARGET_DATE = datetime.date.today() # + datetime.timedelta(days=2) # Uncomment/modify for testing

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# --- End Configuration ---


def get_mlb_starting_pitchers(target_date: datetime.date) -> set[str] | None:
    """
    Fetches probable starting pitchers for the target date using mlb-statsapi.

    Args:
        target_date: The date for which to fetch starters.

    Returns:
        A set containing the full names of probable starting pitchers,
        or None if a critical error occurs fetching the schedule.
        Returns an empty set if no games or starters are found.
    """
    target_date_str = target_date.strftime("%Y-%m-%d")
    logging.info(f"Fetching MLB probable starters for date: {target_date_str}")

    try:
        schedule_data = statsapi.schedule(date=target_date_str)
    except Exception as e:
        logging.error(f"Error fetching MLB schedule from statsapi: {e}", exc_info=True)
        return None # Indicates a critical failure

    if not schedule_data:
        logging.warning(f"No MLB games found scheduled for {target_date_str} via statsapi.")
        return set() # No games, return empty set

    # Use a set comprehension for concise extraction
    probable_starters = {
        pitcher
        for game in schedule_data
        for key in ["home_probable_pitcher", "away_probable_pitcher"]
        if (pitcher := game.get(key)) and pitcher not in [None, 'N/A', '']
    }

    if not probable_starters:
        logging.warning("Could not identify any probable starting pitchers from MLB schedule data.")
    else:
        logging.info(f"Identified {len(probable_starters)} probable MLB starters.")
        # logging.debug(f"Starters: {', '.join(sorted(probable_starters))}") # Uncomment for debugging

    return probable_starters


def ensure_auth_file(auth_dir: str, auth_file: str) -> bool:
    """
    Ensures authentication directory exists and the auth file is present.
    Provides guidance if the file is missing.

    Args:
        auth_dir: Path to the directory for authentication files.
        auth_file: Path to the specific OAuth2 credentials file (e.g., 'private.json').

    Returns:
        True if the auth file exists, False otherwise.
    """
    if not os.path.exists(auth_dir):
        logging.warning(f"Authentication directory not found: {auth_dir}")
        try:
            os.makedirs(auth_dir)
            logging.info(f"Created directory: {auth_dir}")
        except OSError as e:
            logging.error(f"Could not create directory {auth_dir}. Please create it manually. Error: {e}")
            return False

    if not os.path.isfile(auth_file):
        logging.error(f"OAuth2 authentication file not found: {auth_file}")
        logging.error("Please create this file (e.g., 'private.json') in the directory.")
        logging.error("It should contain your Yahoo App 'consumer_key' and 'consumer_secret'.")
        logging.error("Format:\n{\n  \"consumer_key\": \"YOUR_KEY\",\n  \"consumer_secret\": \"YOUR_SECRET\"\n}")
        logging.error("Create Yahoo App credentials at: https://developer.yahoo.com/apps/create/")
        return False
    return True


def authenticate_yahoo(auth_file: str, game_code: str) -> yfa.Game | None:
    """
    Authenticates with Yahoo Fantasy Sports API using OAuth2.

    Args:
        auth_file: Path to the OAuth2 credentials file.
        game_code: The game code (e.g., 'mlb').

    Returns:
        An authenticated yahoo_fantasy_api.Game object, or None if authentication fails.
    """
    logging.info("Attempting to authenticate with Yahoo Fantasy Sports...")
    try:
        sc = OAuth2(None, None, from_file=auth_file)
        if not sc.token_is_valid():
            logging.info("Yahoo token expired or invalid, attempting refresh (may require browser auth)...")
            sc.refresh_access_token()

        gm = yfa.Game(sc, game_code)
        logging.info("Yahoo authentication successful.")
        return gm
    except Exception as e:
        logging.error(f"Error during Yahoo Fantasy API authentication: {e}", exc_info=True)
        return None


def get_fantasy_team(gm: yfa.Game, league_id: str, team_id: int) -> yfa.Team | None:
    """
    Retrieves the specific fantasy team object.

    Args:
        gm: Authenticated yahoo_fantasy_api.Game object.
        league_id: The numeric Yahoo Fantasy League ID.
        team_id: The numeric Yahoo Fantasy Team ID within the league.

    Returns:
        An authenticated yahoo_fantasy_api.Team object, or None if retrieval fails.
    """
    try:
        # Construct the full league key (e.g., '458.l.41370')
        # Assumes current year if league_id is just the number
        full_league_id = f"{gm.game_id()}.l.{league_id}"
        lg = gm.to_league(full_league_id)
        logging.info(f"Accessing Yahoo League: {full_league_id}")

        # Construct the full team key (e.g., '458.l.41370.t.2')
        full_team_key = f"{full_league_id}.t.{team_id}"
        tm = lg.to_team(full_team_key)
        logging.info(f"Accessing Yahoo Team: {tm.team_name} ({full_team_key})")
        return tm
    except Exception as e:
        logging.error(f"Error accessing Yahoo league/team (LID: {league_id}, TID: {team_id}): {e}", exc_info=True)
        logging.error("Verify YAHOO_LEAGUE_ID and YAHOO_TEAM_ID are correct.")
        return None


def manage_fantasy_pitchers(
    league_id_num: str,
    team_id_num: int,
    game_code: str,
    auth_file: str,
    target_date: datetime.date
):
    """
    Main function to fetch starters, get roster, compare, and modify lineup.
    """
    # --- Step 1: Get Today's MLB Starters ---
    actual_starters_set = get_mlb_starting_pitchers(target_date)
    if actual_starters_set is None:
        logging.error("Exiting due to critical error fetching MLB starters.")
        sys.exit(1)
    if not actual_starters_set:
        logging.info("No probable MLB starters identified for today. No roster changes needed based on this.")
        sys.exit(0)

    # --- Step 2: Authenticate and Get Team ---
    if not ensure_auth_file(AUTH_DIR, auth_file):
        sys.exit(1)

    gm = authenticate_yahoo(auth_file, game_code)
    if not gm:
        sys.exit(1)

    tm = get_fantasy_team(gm, league_id_num, team_id_num)
    if not tm:
        sys.exit(1)

    # --- Step 3: Get Fantasy Team Roster ---
    try:
        target_date_str = target_date.strftime("%Y-%m-%d")
        logging.info(f"Fetching fantasy roster for team '{tm.team_name}' for date: {target_date_str}")
        # Fetch roster for the target date
        roster = tm.roster(day=target_date)
        if not roster:
            logging.error("Could not fetch roster data. The roster might be empty or an API error occurred.")
            sys.exit(1)
        logging.info(f"Successfully fetched roster with {len(roster)} players.")
    except Exception as e:
        logging.error(f"An error occurred while fetching the fantasy team roster: {e}", exc_info=True)
        sys.exit(1)

    # --- Step 4: Analyze Roster and Identify Potential Swaps ---
    logging.info("Analyzing roster against today's MLB starters...")
    pitchers_to_activate = [] # Pitchers on Bench who ARE starting today (and healthy)
    pitchers_to_bench = []    # Pitchers in Active slots (P/SP) who are NOT starting today
    current_lineup = {}       # Stores the target position for each player_id

    for player in roster:
        player_id = player['player_id']
        player_name = player['name']
        current_position = player['selected_position']
        eligible_positions = player['eligible_positions'] # List like ['SP', 'P', 'BN']
        is_pitcher = any(pos in ACTIVE_PITCHER_SLOTS for pos in eligible_positions)
        player_status = player.get('status', '') # e.g., 'IL', 'DTD', ''

        # Initialize current lineup state
        current_lineup[player_id] = current_position

        # Skip non-pitchers or players without a current position
        if not is_pitcher or not current_position:
            continue

        is_starting_today = player_name in actual_starters_set
        is_healthy = player_status not in ['IL', 'NA', 'DTD'] # Consider DTD benchable? Your choice.

        logging.debug(
            f"Processing: {player_name:<20} | Pos: {current_position:<3} | "
            f"Elig: {','.join(eligible_positions):<8} | MLB Start? {is_starting_today} | "
            f"Status: {player_status or 'OK'}"
        )

        # Identify pitchers needing activation (Bench -> Active)
        if current_position == BENCH_SLOT and is_starting_today:
            if is_healthy:
                pitchers_to_activate.append(player)
                logging.info(f"  -> Candidate to ACTIVATE: {player_name} (from BN)")
            else:
                logging.warning(f"  -> Skipping activation for {player_name}: Status is {player_status}")

        # Identify pitchers needing benching (Active -> Bench)
        elif current_position in ACTIVE_PITCHER_SLOTS and not is_starting_today:
            pitchers_to_bench.append(player)
            logging.info(f"  -> Candidate to BENCH: {player_name} (from {current_position})")

    # --- Step 5: Determine Actual Roster Changes ---
    logging.info("\n--- Determining Roster Changes ---")
    target_lineup = current_lineup.copy() # Start with current state
    moves_made_count = 0

    # Prioritize activating starters by swapping them with bench candidates
    # Create iterators to safely modify lists while looping
    bench_candidates_iter = iter(pitchers_to_bench)

    for player_to_activate in pitchers_to_activate:
        try:
            # Find the next available player to move to the bench
            player_to_deactivate = next(bench_candidates_iter)

            # Determine the target active slot (prefer SP if eligible, else P)
            target_slot = 'SP' if 'SP' in player_to_activate['eligible_positions'] else 'P'
            if target_slot not in ACTIVE_PITCHER_SLOTS: # Fallback if only P is somehow allowed
                 target_slot = list(ACTIVE_PITCHER_SLOTS)[0]

            # Log the planned swap
            logging.info(
                f"Action: Move {player_to_activate['name']} (BN) -> {target_slot}, "
                f"Move {player_to_deactivate['name']} ({player_to_deactivate['selected_position']}) -> BN"
            )

            # Update the target lineup dictionary
            target_lineup[player_to_activate['player_id']] = target_slot
            target_lineup[player_to_deactivate['player_id']] = BENCH_SLOT
            moves_made_count += 1

        except StopIteration:
            # No more players left to bench
            logging.warning(f"Cannot activate {player_to_activate['name']}: No available non-starting active pitchers to swap out.")
            break # Stop trying to activate if no bench candidates remain

    if moves_made_count == 0:
        logging.info("No lineup changes required or possible based on today's starters and current roster.")
        sys.exit(0)

    # --- Step 6: Execute Lineup Changes ---
    logging.info("\n--- Submitting Roster Changes to Yahoo ---")

    # Filter target_lineup to only include actual changes (optional, API takes full state)
    final_position_changes = {
        pid: pos for pid, pos in target_lineup.items() if current_lineup[pid] != pos
    }
    logging.info(f"Attempting {len(final_position_changes)//2} swap(s):") # Each swap involves 2 players
    for pid, pos in final_position_changes.items():
         # Find player name for logging
         player_name = next((p['name'] for p in roster if p['player_id'] == pid), f"ID {pid}")
         logging.info(f"  - Set {player_name} to position {pos}")


    try:
        # The API expects the full desired state for the date
        logging.info(f"Submitting full target lineup state for {target_date_str}...")
        # Use the target_lineup dictionary which contains the desired state for all players
        tm.change_positions(target_date, target_lineup)
        logging.info("SUCCESS: Roster changes submitted to Yahoo!")

    except Exception as e:
        logging.error(f"ERROR: Failed to submit roster changes to Yahoo: {e}", exc_info=True)
        logging.error("Potential Reasons:")
        logging.error("- Yahoo API Error (e.g., invalid move, locked roster, game started).")
        logging.error("- Permissions issues with your Yahoo App credentials.")
        logging.error("- Incorrect data format sent to the API.")
        logging.error("No changes were likely made.")
        sys.exit(1)


# --- Run the main function ---
if __name__ == "__main__":
    print("="*60)
    print(" Starting Yahoo Fantasy Pitcher Auto-Starter Script")
    print(f" Run Time: {datetime.datetime.now()}")
    print("="*60)
    logging.info(f"Target Date for Lineup: {TARGET_DATE.strftime('%Y-%m-%d')}")
    logging.info(f"Using League ID: {YAHOO_LEAGUE_ID}")
    logging.info(f"Using Team ID:   {YAHOO_TEAM_ID}")
    logging.info(f"Using Auth File: {AUTH_FILE}")
    logging.warning("This script WILL attempt to modify your live Yahoo Fantasy lineup.")
    # Optional: Add confirmation prompt here if desired
    # input("Press Enter to continue or Ctrl+C to cancel...")

    # Basic validation for required config
    if "YOUR_LEAGUE_ID" in YAHOO_LEAGUE_ID or not YAHOO_LEAGUE_ID.isdigit():
        logging.error("FATAL: YAHOO_LEAGUE_ID is not set correctly. Please update the script.")
        sys.exit(1)
    if not isinstance(YAHOO_TEAM_ID, int) or YAHOO_TEAM_ID <= 0:
         logging.error("FATAL: YAHOO_TEAM_ID is not set correctly. Please update the script.")
         sys.exit(1)


    manage_fantasy_pitchers(
        league_id_num=YAHOO_LEAGUE_ID,
        team_id_num=YAHOO_TEAM_ID,
        game_code=GAME_CODE,
        auth_file=AUTH_FILE,
        target_date=TARGET_DATE
    )

    logging.info("\nScript execution finished.")