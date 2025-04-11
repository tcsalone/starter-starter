import datetime
from yahoo_fantasy_api import game, league, team
from yahoo_oauth import OAuth2  # Handles authentication

# --- Configuration ---
# Place your oauth2 credentials file (e.g., 'private.json') in this directory
# You get this file when registering your app with Yahoo Developer Network
# Ensure it has read/write permissions for Fantasy Sports
AUTH_DIR = "."  # Directory to store the authentication token

# --- Functions ---


def get_todays_starting_pitchers_on_bench(team_obj):
    """
    Fetches the team roster and identifies SPs on the bench starting today.
    Returns a list of player dictionaries.
    """
    today = datetime.date.today()
    print(f"Fetching roster for {today}...")
    try:
        roster = team_obj.roster(day=today)  # Fetch roster for the specific day
    except Exception as e:
        print(f"Error fetching roster: {e}")
        return []

    starters_on_bench = []
    for player in roster:
        is_sp = 'SP' in player.get('eligible_positions', [])
        is_on_bench = player.get('selected_position') == 'BN'
        # Crucial: Check if the player is actually starting today.
        # The API/wrapper needs to provide this info. Common keys might be
        # 'is_starting', 'status', 'probable_starter'. Inspect the player dict!
        # Example using a hypothetical 'is_starting' key (ADAPT THIS KEY):
        is_starting_today = player.get('is_starting', False)  # <-- CHECK/ADAPT THIS KEY

        # --- IMPORTANT ---
        # You MUST inspect the actual data returned for a player object
        # to find the correct key indicating they are starting today.
        # Use print(player) within the loop during testing to see all available fields.
        # It might be in 'status', or a specific 'starting_status' field, etc.
        # Example Alternative: Sometimes status might be 'P' (Probable) or 'S' (Starting)
        # is_starting_today = player.get('status') in ['P', 'S'] # Another possible check

        print(f"  Checking Player: {player.get('name', 'N/A')}, Pos: {player.get('selected_position')}, "
              f"Eligible: {player.get('eligible_positions')}, Starting Today?: {is_starting_today}")  # Debugging line

        if is_sp and is_on_bench and is_starting_today:
            print(f"    -> Found starting pitcher on bench: {player.get('name')}")
            starters_on_bench.append(player)

    return starters_on_bench


def get_available_sp_slots(team_obj):
    """
    Identifies empty 'SP' slots in the active lineup.
    Returns the number of available slots.
    """
    today = datetime.date.today()
    try:
        roster = team_obj.roster(day=today)
    except Exception as e:
        print(f"Error fetching roster for SP slots: {e}")
        return 0

    # Determine how many SP-specific slots the league allows
    league_settings = team_obj.league().settings()
    roster_positions = league_settings.get('roster_positions', {})
    sp_slot_count = roster_positions.get('SP', 0)  # Get max SP slots allowed

    current_sp_players = 0
    for player in roster:
        if player.get('selected_position') == 'SP':
            current_sp_players += 1

    available_slots = sp_slot_count - current_sp_players
    print(f"League SP Slots: {sp_slot_count}, Currently Filled: {current_sp_players}, Available: {available_slots}")
    return max(0, available_slots)  # Ensure non-negative


def set_lineup(team_obj, players_to_move):
    """
    Constructs and executes the API call to move players to SP slots.
    """
    if not players_to_move:
        print("No lineup changes needed.")
        return

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    lineup_payload = {"players": []}

    print("Preparing lineup changes...")
    for player in players_to_move:
        player_id = player.get('player_id')
        player_name = player.get('name', 'N/A')
        print(f"  Queueing move: {player_name} ({player_id}) from BN to SP")
        lineup_payload["players"].append({
            "player_key": team_obj.player_key_from_id(player_id),  # Construct player_key
            "position": "SP"  # Target position
        })

    print(f"Attempting to apply lineup for {today_str} with payload: {lineup_payload}")
    try:
        # Use team.change_roster() which seems to be the intended method in the wrapper
        team_obj.change_roster(lineup_payload, date=today_str)
        print("Lineup successfully updated!")
    except Exception as e:
        print(f"ERROR updating lineup: {e}")
        print("  Payload attempted:", lineup_payload)
        # Consider logging the full error traceback here for debugging


# --- Main Execution ---

if __name__ == "__main__":
    print("Starting Yahoo Fantasy Auto-Pitcher Setter...")
    current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Current time: {current_time_str}")

    # 1. Authenticate
    try:
        sc = OAuth2(None, None, from_file=f"{AUTH_DIR}/private.json", base_dir=AUTH_DIR)
        if not sc.token_is_valid():
            sc.refresh_access_token()
    except Exception as e:
        print(f"ERROR: Authentication failed: {e}")
        print("Ensure 'private.json' is in the correct directory and has the right permissions.")
        exit(1)

    # 2. Get Game/League/Team Objects
    try:
        # Get game object
        gm = game.Game(sc, 'mlb')  # 'mlb' is the game code for baseball
        league_ids = gm.league_ids()
        if not league_ids:
            print("ERROR: No leagues found for this account in the current MLB season.")
            exit(1)

        # Print available leagues for user selection
        print(f"Available league IDs: {league_ids}")
        league_id = input(f"Enter your League ID from the list above: ")

        if league_id not in league_ids:
            print(f"Error: League ID '{league_id}' not found in your leagues: {league_ids}")
            exit(1)

        # Get league and team objects
        lg = gm.to_league(league_id)
        team_key = lg.team_key()  # Gets your team key in that league
        tm = lg.to_team(team_key)
        
        # Now that tm is defined, debug it
        print("\n--- Debugging Team Object ---")
        print(f"Type of tm: {type(tm)}")
        print("Attributes of tm (dir):")
        print(dir(tm))  # Shows all methods and attributes
        print("--- End Debugging ---")
        
        print(f"Successfully connected to League ID: {league_id}, Team Name: {tm.team_key}")

    except Exception as e:
        print(f"ERROR: Could not connect to Yahoo Fantasy API or find league/team: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

    # 3. Identify Starters on Bench
    starters_on_bench = get_todays_starting_pitchers_on_bench(tm)

    if not starters_on_bench:
        print("No starting pitchers found on the bench for today.")
        exit(0)  # Normal exit, nothing to do

    # 4. Identify Available SP Slots
    available_slots = get_available_sp_slots(tm)

    if available_slots <= 0:
        print("No available SP slots in the active lineup.")
        exit(0)  # Normal exit, nothing to do

    # 5. Determine Players to Move (Limit by available slots)
    players_to_move = starters_on_bench[:available_slots]  # Take only as many as there are slots

    # 6. Set Lineup
    set_lineup(tm, players_to_move)

    print("Script finished.")