import pandas as pd
import math

# Constants for the rating formula
K_FACTOR = 16
DIVISOR = 150

def calculate_win_probability(rating_a, rating_b):
    """
    Calculate the probability of Player A winning against Player B.
    Formula: P_a = 1 / (1 + 10 ^ ((RatingB - RatingA) / Divisor))
    """
    try:
        prob = 1 / (1 + 10 ** ((rating_b - rating_a) / DIVISOR))
        return prob
    except OverflowError:
        # If the rating difference is too extreme, probability is effectively 0 or 1
        return 0.0 if rating_b > rating_a else 1.0

def calculate_new_rating(rating_a, score_a, expected_score_a):
    """
    Calculate new rating for Player A.
    Formula: R' = R + K * (Score - ExpectedScore)
    """
    return rating_a + K_FACTOR * (score_a - expected_score_a)

def calculate_ratings(data_df, initial_ratings_df):
    """
    Recalculate ratings for the entire dataset using the new formula.
    
    :param data_df: DataFrame containing match data.
    :param initial_ratings_df: DataFrame containing initial ratings.
    :return: A copy of data_df with updated 'Rating P1' and 'Rating P2' columns.
    """
    # Create a copy to avoid modifying the original dataframe in place immediately
    # We will only keep the relevant columns from the original and overwrite ratings
    
    # Initialize player ratings from the provided initial_ratings dataframe
    player_ratings = dict(zip(initial_ratings_df['Player'].str.strip(), initial_ratings_df['Rating']))
    
    # We want to preserve all original columns but update/fill Rating P1 and Rating P2
    result_df = data_df.copy()
    
    # Ensure specific columns exist for output, initialize them if not
    if 'Rating P1' not in result_df.columns:
        result_df['Rating P1'] = 0
    if 'Rating P2' not in result_df.columns:
        result_df['Rating P2'] = 0

    for index, row in result_df.iterrows():
        player1 = str(row['Player 1']).strip()
        player2 = str(row['Player 2']).strip()
        result_str = str(row['Result'])

        # Get current ratings, default to 1200 if not found in initial list
        # (You might want to parameterize this default or strictly require initial ratings)
        rating1 = player_ratings.get(player1, 1200)
        rating2 = player_ratings.get(player2, 1200)

        # Parse result to determine score
        # Assuming format "Score1-Score2"
        try:
            parts = result_str.split('-')
            if len(parts) != 2:
                # Handle unexpected format if necessary, or skip
                continue
                
            score1_val = int(parts[0])
            score2_val = int(parts[1])
            
            # Determine Actual Score (S_A)
            # 1.0 if Win, 0.0 if Loss.
            # Draws handled as 0.5? User said: "MatchResult = 1 if won, 0 if lost"
            # What about draws? Assuming standard behavior for now: if scores equal -> 0.5
            if score1_val > score2_val:
                actual_score1 = 1.0
                actual_score2 = 0.0
            elif score2_val > score1_val:
                actual_score1 = 0.0
                actual_score2 = 1.0
            else:
                actual_score1 = 0.5
                actual_score2 = 0.5
                
        except (ValueError, IndexError):
            # Log error or skip row
            continue

        # Calculate Expected Scores / Win Probabilities
        expected1 = calculate_win_probability(rating1, rating2)
        expected2 = calculate_win_probability(rating2, rating1) # Or 1 - expected1

        # Calculate New Ratings
        new_rating1 = calculate_new_rating(rating1, actual_score1, expected1)
        new_rating2 = calculate_new_rating(rating2, actual_score2, expected2)

        # Update the DataFrame row with the *Post-Match* ratings
        # Rounding to nearest integer for display/storage clarity
        result_df.at[index, 'Rating P1'] = round(new_rating1)
        result_df.at[index, 'Rating P2'] = round(new_rating2)

        # Update current ratings dictionary for next iteration
        player_ratings[player1] = new_rating1
        player_ratings[player2] = new_rating2

    return result_df





def calculate_championship_stats(data_df):
    """
    Calculate the number of titles and runner-up finishes for each player.
    A title is awarded to the winner of the last match of the day,
    provided the match is NOT a "League" or "Clubmatch" (indicated in 'Special' column).
    """
    if data_df.empty:
        return {}, {}

    # Ensure Date is datetime
    df = data_df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Check if 'Special' column exists and filter
    if 'Special' in df.columns:
        # Filter out rows where Special contains "League" or "Clubmatch" (case insensitive)
        def is_excluded(val):
            s = str(val).lower()
            return 'league' in s or 'clubmatch' in s
            
        mask = ~df['Special'].apply(is_excluded)
        filtered_df = df[mask]
    else:
        filtered_df = df

    if filtered_df.empty:
        return {}, {}
        
    titles = {}
    runner_ups = {}
    
    # Group by Date and find the match with the maximum SL No for each date
    daily_finals = filtered_df.sort_values('SL No').groupby(filtered_df['Date'].dt.date).last()
    
    for _, row in daily_finals.iterrows():
        # Determine winner and loser
        result_str = str(row['Result'])
        p1 = str(row['Player 1']).strip()
        p2 = str(row['Player 2']).strip()
        
        try:
            parts = result_str.split('-')
            if len(parts) == 2:
                s1, s2 = int(parts[0]), int(parts[1])
                winner = None
                loser = None
                
                if s1 > s2:
                    winner = p1
                    loser = p2
                elif s2 > s1:
                    winner = p2
                    loser = p1
                
                if winner:
                    titles[winner] = titles.get(winner, 0) + 1
                if loser:
                    runner_ups[loser] = runner_ups.get(loser, 0) + 1
        except:
            pass
            
    return titles, runner_ups

def generate_leaderboard_with_changes(data_df):
    """
    Generate leaderboard with Rank, Player Name, Last Rating, Matches Played, Won, Win Percentage, Rating Change, and Titles.
    Rating Change = Current Rating - Previous Day's Rating (relative to the latest match date in the dataset).
    """
    if data_df.empty:
        return pd.DataFrame()

    # Ensure Date is datetime
    data_df['Date'] = pd.to_datetime(data_df['Date'])
    
    # Calculate Titles
    # Calculate Titles
    player_titles, _ = calculate_championship_stats(data_df)
    
    # Identify the latest date in the dataset
    latest_date = data_df['Date'].max()
    previous_date_limit = latest_date - pd.Timedelta(days=1)
    
    # Get the latest stats (Current State)
    # We can reuse extraction logic or do it manually here for precision
    player_latest_status = {}
    
    # Sort by date, then SL No to ensure we process in order
    sorted_df = data_df.sort_values(by=['Date', 'SL No'])
    
    player_ratings_history = {} # player -> list of (date, rating)

    for _, row in sorted_df.iterrows():
        p1 = str(row['Player 1']).strip()
        p2 = str(row['Player 2']).strip()
        date = row['Date']
        r1 = row['Rating P1']
        r2 = row['Rating P2']
        
        # Track history
        if p1 not in player_ratings_history: player_ratings_history[p1] = []
        player_ratings_history[p1].append({'date': date, 'rating': r1})
        
        if p2 not in player_ratings_history: player_ratings_history[p2] = []
        player_ratings_history[p2].append({'date': date, 'rating': r2})

    # Calculate Leaderboard Data
    leaderboard_data = []
    
    # We can use the logic from generate_leaderboard for the basic stats, 
    # but let's just re-compute to include the change logic cleanly.
    
    # Basic Stats Accumulation
    stats = {}
    for _, row in sorted_df.iterrows():
        p1 = str(row['Player 1']).strip()
        p2 = str(row['Player 2']).strip()
        # Ensure stats exist
        if p1 not in stats: stats[p1] = {'matches': 0, 'won': 0}
        if p2 not in stats: stats[p2] = {'matches': 0, 'won': 0}
        
        stats[p1]['matches'] += 1
        stats[p2]['matches'] += 1
        
        # Wins
        result_str = str(row['Result'])
        try:
            parts = result_str.split('-')
            if len(parts) == 2:
                s1, s2 = int(parts[0]), int(parts[1])
                if s1 > s2: stats[p1]['won'] += 1
                elif s2 > s1: stats[p2]['won'] += 1
        except: pass

    for player, history in player_ratings_history.items():
        current_rating = history[-1]['rating']
        
        # Find rating as of previous_date_limit (end of that day)
        # We want the last rating where date <= previous_date_limit
        prev_rating_val = None
        
        # Iterate backwards to find the last rating on or before the cutoff date
        relevant_history = [h for h in history if h['date'] <= previous_date_limit]
        
        is_new = False
        rating_change = 0
        
        if not relevant_history:
            # No games before today (or before the latest date's previous day)
            is_new = True
            rating_change = 0 # Or current_rating - 1200? Usually "New" implies we just show "New"
        else:
            prev_rating_val = relevant_history[-1]['rating']
            rating_change = current_rating - prev_rating_val
            
        matches = stats[player]['matches']
        won = stats[player]['won']
        win_pct = (won / matches) if matches > 0 else 0.0
        
        # Get Titles
        titles_count = player_titles.get(player, 0)
        
        leaderboard_data.append({
            'Player Name': player,
            'Last Rating': current_rating,
            'Matches Played': matches,
            'Won': won,
            'Win Percentage': round(win_pct, 2),
            'Rating Change': rating_change,
            'Is New': is_new,
            'Titles': titles_count
        })
        
    df = pd.DataFrame(leaderboard_data)
    if not df.empty:
        # Sort by Last Rating (primary) and Titles (secondary - just in case?) 
        # Usually sorting by Rating is enough.
        df = df.sort_values(by='Last Rating', ascending=False)
        df.insert(0, 'Rank', range(1, len(df) + 1))
        
    return df
