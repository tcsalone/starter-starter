import json 
import datetime 
from yahoo_fantasy_api import game, league, team
from yahoo_oauth import OAuth2  # Handles authentication

# OAuth setup
# Create an OAuth2 session - either with credentials file or directly
# Option 1: Using credentials file (recommended)
sc = OAuth2(consumer_key=None, consumer_secret=None, refresh_token=None, filename="private_prob_starter.json")

# Option 2: Direct credentials
#sc = OAuth2(
#    consumer_key="dj0yJmk9WVhKSVk2Vm5HNVBFJmQ9WVdrOVEwRklWbGhyUjBNbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PWJh",
#    consumer_secret="00bc06f768688f8aab80164babc32117e5a69d96et",
#    refresh_token="ABOo.GcpNAIjDCr4A9XQaSCRIZjH~001~_8rZeH.n8D_OFalVJv6_iG4."
# )

# Get game object (2024 for current MLB season)
gm = game.Game(sc, 'mlb')

# Get the league ID you're interested in
league_ids = gm.league_ids()
if not league_ids:
    print("No leagues found. Make sure your authentication is correct.")
    exit(1)
    
league_id = league_ids[0]  # Use the first league or specify a specific one
print(f"Using league ID: {league_id}")

# Create league object
lg = gm.to_league(league_id)

# Create team object
team_key = lg.team_key()  # Your team key
print(f"Using team key: {team_key}")
tm = lg.to_team(team_key)

# Get all starting pitchers with status information
def get_sp_probable_starters():
    """Get all starting pitchers with their status"""
    # Get all players from your team's roster
    players = tm.roster()
    
    # Alternative: Use this to get free agents who are SPs
    # free_agents = lg.free_agents('SP')
    
    sp_probables = []
    
    # Loop through players looking for SPs
    for player in players:
        # Check if player is an SP
        if 'SP' in player['eligible_positions']:
            # Get player status
            player_id = player['player_id']
            player_name = player['name']
            
            # Get player status - need to check if the player is in the starting lineup
            # Yahoo Fantasy API doesn't have a direct method to get probable starters
            # We need to check the player metadata and status

            # Get player stats and metadata
            player_stats = tm.player_stats([player_id])
            
            # Check if we have status info
            status = player.get('status', 'Unknown')
            start_date = None
            opponent = None
            
            # Try to get matchup information from weekly stats
            try:
                # Get current matchup details
                matchup = lg.matchup_stats(team_key)
                for matchup_player in matchup:
                    if str(matchup_player.get('player_id')) == str(player_id):
                        # Found player in matchup data
                        start_date = matchup_player.get('start_date')
                        opponent = matchup_player.get('opponent')
                        break
            except Exception as e:
                print(f"Error getting matchup data for {player_name}: {e}")
            
            # Add player to probable starters if status indicates they're starting
            # Note: Yahoo doesn't always label SPs as "Probable" - look for keywords
            probable_keywords = ['Probable', 'Starting', 'Start']
            is_probable = any(keyword.lower() in status.lower() for keyword in probable_keywords) if status else False
            
            # If we have status info or matchup data, include the player
            if is_probable or start_date:
                sp_probables.append({
                    'name': player_name,
                    'status': status,
                    'team': player.get('editorial_team_abbr', ''),
                    'opponent': opponent,
                    'start_date': start_date,
                    'player_id': player_id,
                    'position': player['eligible_positions'],
                    'stats': player_stats.get(player_id, {})
                })
    
    # Try getting starting pitchers from league status
    try:
        # Get all players with "Starting" status from league
        league_status = lg.status()
        for status_player in league_status:
            player_id = status_player.get('player_id')
            # Skip players we've already added
            if any(p['player_id'] == player_id for p in sp_probables):
                continue
                
            # Check if this is an SP with starting status
            player_details = lg.player_details(player_id)
            if 'SP' in player_details.get('eligible_positions', []):
                sp_probables.append({
                    'name': player_details.get('name'),
                    'status': status_player.get('status', 'Unknown'),
                    'team': player_details.get('editorial_team_abbr', ''),
                    'opponent': status_player.get('opponent'),
                    'start_date': status_player.get('start_date'),
                    'player_id': player_id,
                    'position': player_details.get('eligible_positions', []),
                    'is_from_league_status': True
                })
    except Exception as e:
        print(f"Error getting league status: {e}")
    
    return sp_probables

# Main execution
if __name__ == "__main__":
    # Get and display SP probable starters
    print("Fetching probable SP starters...")
    probable_starters = get_sp_probable_starters()
    
    print(f"\nFound {len(probable_starters)} probable SP starters:")
    for pitcher in probable_starters:
        opponent_info = f"vs {pitcher['opponent']}" if pitcher['opponent'] else ""
        date_info = f"on {pitcher['start_date']}" if pitcher['start_date'] else ""
        print(f"{pitcher['name']} ({pitcher['team']}) - {pitcher['status']} {opponent_info} {date_info}")
    
    # Example of how to extract all available information for a player:
    if probable_starters:
        sample_player = probable_starters[0]
        print("\nSample player details:")
        for key, value in sample_player.items():
            if key != 'stats':  # Skip stats for cleaner output
                print(f"{key}: {value}")
        
        print("\nAvailable stats keys:")
        if 'stats' in sample_player and sample_player['stats']:
            for stat_key in sample_player['stats'].keys():
                print(f"- {stat_key}")