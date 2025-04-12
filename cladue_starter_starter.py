import datetime
from yahoo_fantasy_api import game, league, team
from yahoo_oauth import OAuth2
import pprint

# --- Configuration remains the same ---
AUTH_DIR = "."

def detailed_player_inspection(player):
    """Print all available information about a player"""
    print(f"\n==== DETAILED PLAYER INFO: {player.get('name')} ====")
    for key, value in player.items():
        print(f"{key}: {value}")
    print("====================================\n")

def get_all_pitchers_with_details(team_obj):
    """Get all pitchers and examine their details"""
    today = datetime.date.today()
    
    try:
        # Get roster for today
        roster = team_obj.roster(day=today)
        
        # Try to get additional player details
        # The API might offer a way to get more details
        player_stats = {}
        try:
            # Attempt to get player stats which might include status
            # Note: This is an educated guess at what the API might provide
            current_week = team_obj.current_week()
            player_stats = team_obj.player_stats("week", current_week)
            print("Successfully retrieved player stats!")
        except Exception as e:
            print(f"Could not get player stats: {e}")
            
        # Try to get matchup data which might show probable pitchers
        try:
            matchups = team_obj.matchups()
            print("Matchups data retrieved!")
            pprint.pprint(list(matchups.keys())[:5])  # Show first few keys
        except Exception as e:
            print(f"Could not get matchups: {e}")
            
        print(f"Found {len(roster)} players on roster")
            
        # Examine all pitchers regardless of bench/active status
        all_pitchers = []
        for player in roster:
            positions = player.get('eligible_positions', [])
            
            # Check if player is a pitcher (SP or RP)
            is_pitcher = 'SP' in positions or 'RP' in positions
            
            if is_pitcher:
                print(f"\nFound pitcher: {player.get('name')}")
                detailed_player_inspection(player)
                
                # If we have stats data, check for this player
                if player_stats and player.get('player_id') in player_stats:
                    print("Additional player stats found:")
                    pprint.pprint(player_stats[player.get('player_id')])
                
                all_pitchers.append(player)
                
        # Print out summary
        print(f"\nFound {len(all_pitchers)} total pitchers on roster")
        print("Pitcher names and positions:")
        for p in all_pitchers:
            print(f"- {p.get('name')}: {p.get('eligible_positions')} (Currently: {p.get('selected_position')})")
            
        return all_pitchers
        
    except Exception as e:
        print(f"Error fetching roster: {e}")
        import traceback
        traceback.print_exc()
        return []

def examine_league_structure(lg_obj):
    """Examine league settings and structure"""
    try:
        # Get league settings
        settings = lg_obj.settings()
        print("\n==== LEAGUE SETTINGS ====")
        print(f"League Name: {settings.get('name', 'N/A')}")
        print(f"Season: {settings.get('season', 'N/A')}")
        
        # Print roster positions
        if 'roster_positions' in settings:
            print("\nROSTER POSITIONS:")
            for pos, count in settings['roster_positions'].items():
                print(f"- {pos}: {count}")
        
        # Get current matchup period
        try:
            current_week = lg_obj.current_week()
            print(f"\nCurrent Matchup Week: {current_week}")
        except Exception as e:
            print(f"Error getting current week: {e}")
            
        # Get today's scoreboard
        try:
            today = datetime.date.today()
            scoreboard = lg_obj.scoreboard(week=current_week)
            print("\nThis week's matchups:")
            pprint.pprint(scoreboard)
        except Exception as e:
            print(f"Error getting scoreboard: {e}")
            
        return settings
        
    except Exception as e:
        print(f"Error examining league: {e}")
        return {}

def check_player_status_options(team_obj):
    """Try different methods to get player status information"""
    print("\n==== CHECKING ADDITIONAL PLAYER DATA METHODS ====")
    
    # List of method names that might exist to get player information
    possible_methods = [
        'player_details',
        'get_player_stats',
        'get_player_status',
        'player_news',
        'get_player_news',
        'get_probable_pitchers',
        'game_details',
        'team_stats',
        'players_status'
    ]
    
    # Try calling each method to see if it exists
    for method in possible_methods:
        if hasattr(team_obj, method):
            print(f"Found method: {method}")
            try:
                # Try calling with no args first
                result = getattr(team_obj, method)()
                print(f"  Success! Sample result:")
                pprint.pprint(result[:2] if isinstance(result, list) else result)
            except Exception as e:
                print(f"  Error calling {method}: {e}")
        else:
            print(f"Method not available: {method}")
            
    # Check if there's an API method to get today's MLB probables directly
    print("\nChecking for probable pitchers through league object...")
    try:
        if hasattr(lg_obj, 'probable_pitchers'):
            probables = lg_obj.probable_pitchers()
            print("Found probable pitchers:")
            pprint.pprint(probables)
        else:
            print("No probable_pitchers method available on league object")
    except Exception as e:
        print(f"Error checking probable pitchers: {e}")
        
    print("==== END METHOD CHECKS ====\n")

# --- Main Execution ---
if __name__ == "__main__":
    print("Starting Improved Yahoo Fantasy Pitcher Analyzer...")
    
    # Authentication
    try:
        sc = OAuth2(None, None, from_file=f"{AUTH_DIR}/private.json", base_dir=AUTH_DIR)
        if not sc.token_is_valid():
            sc.refresh_access_token()
    except Exception as e:
        print(f"ERROR: Authentication failed: {e}")
        exit(1)
    
    # Game/League/Team setup
    try:
        gm = game.Game(sc, 'mlb')
        league_ids = gm.league_ids()
        if not league_ids:
            print("ERROR: No leagues found.")
            exit(1)
        
        print(f"Available league IDs: {league_ids}")
        league_id = "458.l.41370"  # Using your predefined league
        
        lg = gm.to_league(league_id)
        team_key = lg.team_key()
        tm = lg.to_team(team_key)
        
        print(f"Connected to League ID: {league_id}, Team Key: {team_key}")
        
        # Let's try to inspect available methods
        print("\nTeam object available methods:")
        team_methods = [method for method in dir(tm) if not method.startswith('_')]
        print(team_methods)
        
        # Check league structure first
        print("\nExamining league structure...")
        league_settings = examine_league_structure(lg)
        
        # Check what player status methods might be available
        print("\nChecking for player status methods...")
        check_player_status_options(tm)
        
        # Now examine all pitchers to find status indicators
        print("\nExamining all pitchers on roster...")
        all_pitchers = get_all_pitchers_with_details(tm)
        
        print("\nAnalysis Complete!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)