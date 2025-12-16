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

def generate_leaderboard(data_df):
    """
    Generate a leaderboard with Rank, Player Name, Last Rating, Matches Played, Won, Win Percentage.
    Assumes data_df has 'Rating P1' and 'Rating P2' populated.
    """
    stats = {}

    for _, row in data_df.iterrows():
        p1 = str(row['Player 1']).strip()
        p2 = str(row['Player 2']).strip()
        result_str = str(row['Result'])
        r1 = row['Rating P1']
        r2 = row['Rating P2']

        # Initialize stats if needed
        if p1 not in stats:
            stats[p1] = {'matches': 0, 'won': 0, 'rating': 1200}
        if p2 not in stats:
            stats[p2] = {'matches': 0, 'won': 0, 'rating': 1200}

        # Update ratings
        stats[p1]['rating'] = r1
        stats[p2]['rating'] = r2
        
        # Update match counts
        stats[p1]['matches'] += 1
        stats[p2]['matches'] += 1
        
        # Determine winner
        try:
            parts = result_str.split('-')
            if len(parts) == 2:
                s1 = int(parts[0])
                s2 = int(parts[1])
                
                if s1 > s2:
                    stats[p1]['won'] += 1
                elif s2 > s1:
                    stats[p2]['won'] += 1
        except (ValueError, IndexError):
            pass # Skip invalid results for win count?

    # Convert to list
    leaderboard_data = []
    for player, data in stats.items():
        matches = data['matches']
        won = data['won']
        win_pct = (won / matches * 100) if matches > 0 else 0.0
        leaderboard_data.append({
            'Player Name': player,
            'Last Rating': data['rating'],
            'Matches Played': matches,
            'Won': won,
            'Win Percentage': round(win_pct, 2)
        })

    # create dataframe
    df = pd.DataFrame(leaderboard_data)
    
    # Sort by Last Rating desc
    df = df.sort_values(by='Last Rating', ascending=False)
    
    # Add Rank
    df.insert(0, 'Rank', range(1, len(df) + 1))
    
    return df

