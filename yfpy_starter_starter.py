import datetime
import os
from yfpy.query import YahooFantasySportsQuery
from yfpy.models import Game, League, Team, Player

def analyze_pitchers_with_yfpy():
    """
    Comprehensive analysis of pitchers using the yfpy library
    """
    print("Starting YFPY Pitcher Analysis...")
    today = datetime.date.today()
    print(f"Today's date: {today}")
    
    # Define the authentication directory
    auth_dir = "."
    
    # MLB Game ID for 2025 season (458 is an estimate, may need adjustment)
    # Yahoo typically increments game_id by ~20 each year (398 in 2022, 422 in 2023)
    mlb_game_id = 458
    
    # Your league ID
    league_id = "458.l.41370"
    
    print(f"Connecting to Yahoo Fantasy API for league {league_id}...")
    
    try:
        # Initialize the query object with proper authentication
        #query = YahooFantasySportsQuery(
        #    auth_dir=auth_dir,  
        #    league_id=league_id,
        #    game_code="mlb",
        #    game_id=mlb_game_id,
        #    browser_callback=True  # Enable browser-based auth if needed
        #)
        
        query = YahooFantasySportsQuery(
            league_id="league_id",
            game_code="mlb",
            game_id=458,
            yahoo_access_token_json={
                "access_token": "<YAHOO_ACCESS_TOKEN>",
                "consumer_key": "<YAHOO_CONSUMER_KEY>",
                "consumer_secret": "<YAHOO_CONSUMER_SECRET>",
                "guid": "<YAHOO_TOKEN_GUID>",
                "refresh_token": "<YAHOO_REFRESH_TOKEN>",
                "token_time": 1234567890.123456,
                "token_type": "bearer"
            }
        )
        
        
        
        print("Successfully connected to Yahoo Fantasy API")
        
        # Get basic game info to confirm connection
        game_info = query.get_game_info()
        print(f"Game Info: {game_info.name} {game_info.season}")
        
        # Get league info
        league = query.get_league_info()
        print(f"League: {league.name}")
        
        # Get team info
        team = query.get_team_by_league()
        print(f"Team: {team.name} (ID: {team.team_id})")
        
        # Get all teams in league to verify
        all_teams = query.get_league_teams()
        print(f"Number of teams in league: {len(all_teams)}")
        
        # Get current week
        current_week = league.current_week
        print(f"Current Week: {current_week}")
        
        print("\n--- Getting roster with detailed player information ---")
        
        # Get team roster with full player details
        roster = query.get_team_roster_by_week(team.team_key)
        
        if not roster or not roster.players:
            print("No roster data found!")
            return
            
        print(f"Found {len(roster.players)} players on roster")
        
        # Examine each player and look for pitchers
        pitchers = []
        
        print("\n--- EXAMINING ALL PITCHERS ---")
        for player in roster.players:
            # Check if player is a pitcher
            eligible_positions = [pos.position for pos in player.eligible_positions]
            is_pitcher = "SP" in eligible_positions or "RP" in eligible_positions
            
            if is_pitcher:
                pitchers.append(player)
                print(f"\nPITCHER: {player.name} (ID: {player.player_id})")
                print(f"Selected Position: {player.selected_position.position}")
                print(f"Eligible Positions: {eligible_positions}")
                
                # Check all attributes that might indicate starting status
                print("--- DETAILED ATTRIBUTES ---")
                
                # Loop through all attributes of the player object
                for attr_name in dir(player):
                    # Skip internal attributes and methods
                    if attr_name.startswith('_') or callable(getattr(player, attr_name)):
                        continue
                    
                    # Get attribute value
                    try:
                        attr_value = getattr(player, attr_name)
                        
                        # Filter for attributes that might indicate starting status
                        status_indicators = ['status', 'note', 'news', 'start', 'pitch', 'prob', 'game']
                        if any(indicator in attr_name.lower() for indicator in status_indicators):
                            print(f"{attr_name}: {attr_value}")
                    except Exception as e:
                        pass  # Skip attributes that cause errors
                
                # Try to get additional player details
                try:
                    player_details = query.get_player_by_id(player.player_id)
                    if player_details:
                        print("--- ADDITIONAL PLAYER DETAILS ---")
                        # Check for player notes
                        if hasattr(player_details, 'notes'):
                            print(f"Notes: {player_details.notes}")
                        # Check for player status
                        if hasattr(player_details, 'status_full'):
                            print(f"Status Full: {player_details.status_full}")
                except Exception as e:
                    print(f"Could not retrieve additional details: {str(e)}")
        
        # Check for additional methods that could provide starting info
        try:
            print("\n--- CHECKING LEAGUE SCOREBOARD FOR TODAY ---")
            # Get today's scoreboard which may include probable pitchers
            scoreboard = query.get_league_scoreboard_by_week(current_week)
            if scoreboard and hasattr(scoreboard, 'matchups'):
                print(f"Found {len(scoreboard.matchups)} matchups for current week")
        except Exception as e:
            print(f"Error retrieving scoreboard: {str(e)}")
            
        # Try to get player stats, which sometimes includes game info
        try:
            print("\n--- CHECKING PLAYER STATS FOR TODAY ---")
            # Get today's stats for the first pitcher as an example
            if pitchers:
                today_str = today.strftime("%Y-%m-%d")
                pitcher_stats = query.get_player_stats_by_date(
                    player_key=pitchers[0].player_id,
                    date=today_str
                )
                if pitcher_stats:
                    print(f"Today's stats for {pitchers[0].name}:")
                    for stat in pitcher_stats:
                        print(f"{stat.display_name}: {stat.value}")
        except Exception as e:
            print(f"Error retrieving player stats: {str(e)}")
            
        # Try to find any probable pitchers from available API endpoints
        try:
            print("\n--- CHECKING FOR PROBABLE PITCHERS DATA ---")
            # This method might not exist but worth trying
            if hasattr(query, 'get_probable_pitchers'):
                probable_pitchers = query.get_probable_pitchers()
                print(f"Probable pitchers: {probable_pitchers}")
        except Exception as e:
            print(f"No direct probable pitchers method available: {str(e)}")
            
        print("\n--- CHECKING FOR STARTING PITCHERS ON BENCH ---")
        bench_pitchers = [p for p in pitchers if p.selected_position.position == "BN" 
                         and "SP" in [pos.position for pos in p.eligible_positions]]
        
        print(f"Found {len(bench_pitchers)} SP-eligible pitchers on bench")
        for p in bench_pitchers:
            print(f"- {p.name}")
            # Look for any status indicators for this player
            status_found = False
            for attr_name in dir(p):
                if (not attr_name.startswith('_') and not callable(getattr(p, attr_name)) 
                        and ('status' in attr_name.lower() or 'note' in attr_name.lower())):
                    try:
                        attr_value = getattr(p, attr_name)
                        if attr_value:  # Only print if value exists
                            print(f"  {attr_name}: {attr_value}")
                            status_found = True
                    except:
                        pass
            if not status_found:
                print("  No status information found")
                
        print("\nAnalysis complete!")
        return pitchers
            
    except Exception as e:
        print(f"Error during YFPY analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    analyze_pitchers_with_yfpy()