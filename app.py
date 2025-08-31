import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# Set page configuration
st.set_page_config(
    page_title="Player Rating Progression Analyzer",
    page_icon="📈",
    layout="wide"
)

def parse_csv_data(uploaded_file):
    """Parse and validate the uploaded CSV file"""
    try:
        # Read the CSV file
        df = pd.read_csv(uploaded_file)
        
        # Check if required columns exist
        required_columns = ['Player 1', 'Player 2', 'Date', 'Rating P1', 'Rating P2']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Missing required columns: {', '.join(missing_columns)}")
            st.info(f"Required columns: {', '.join(required_columns)}")
            st.info(f"Found columns: {', '.join(df.columns.tolist())}")
            return None
        
        # Parse dates
        try:
            df['Date'] = pd.to_datetime(df['Date'])
        except Exception as e:
            st.error(f"Error parsing dates: {str(e)}")
            st.info("Please ensure dates are in a recognizable format (e.g., YYYY-MM-DD, MM/DD/YYYY)")
            return None
        
        # Validate numeric ratings
        try:
            df['Rating P1'] = pd.to_numeric(df['Rating P1'], errors='coerce')
            df['Rating P2'] = pd.to_numeric(df['Rating P2'], errors='coerce')
        except Exception as e:
            st.error(f"Error parsing ratings: {str(e)}")
            return None
        
        # Check for missing values in critical columns
        if df[['Player 1', 'Player 2', 'Date', 'Rating P1', 'Rating P2']].isnull().any(axis=1).any():
            st.warning("Some rows contain missing values. These will be excluded from analysis.")
            df = df.dropna(subset=['Player 1', 'Player 2', 'Date', 'Rating P1', 'Rating P2'])
        
        if df.empty:
            st.error("No valid data remaining after cleaning.")
            return None
        
        return df
        
    except Exception as e:
        st.error(f"Error reading CSV file: {str(e)}")
        return None

def extract_player_data(df):
    """Extract all unique players and their rating progression"""
    player_data = {}
    
    # Process player1 ratings
    for _, row in df.iterrows():
        player = row['Player 1']
        date = row['Date']
        rating = row['Rating P1']
        
        if player not in player_data:
            player_data[player] = []
        
        player_data[player].append({
            'date': date,
            'rating': rating,
            'opponent': row['Player 2']
        })
    
    # Process player2 ratings
    for _, row in df.iterrows():
        player = row['Player 2']
        date = row['Date']
        rating = row['Rating P2']
        
        if player not in player_data:
            player_data[player] = []
        
        player_data[player].append({
            'date': date,
            'rating': rating,
            'opponent': row['Player 1']
        })
    
    # Sort each player's data by date and remove duplicates
    for player in player_data:
        # Convert to DataFrame for easier manipulation
        player_df = pd.DataFrame(player_data[player])
        # Sort by date and remove duplicates (keeping last occurrence for same date)
        player_df = player_df.sort_values('date').drop_duplicates(subset=['date'], keep='last')
        player_data[player] = player_df.to_dict('records')
    
    return player_data

def create_rating_chart(player_name, player_matches):
    """Create an interactive Plotly chart for player rating progression"""
    if not player_matches:
        return None
    
    # Convert to DataFrame for easier plotting
    df = pd.DataFrame(player_matches)
    df = df.sort_values('date')
    
    # Create the line chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['rating'],
        mode='lines+markers',
        name=f'{player_name} Rating',
        line=dict(width=3, color='#1f77b4'),
        marker=dict(size=8, color='#1f77b4'),
        hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br>' +
                      '<b>Rating:</b> %{y}<br>' +
                      '<b>Opponent:</b> %{text}<br>' +
                      '<extra></extra>',
        text=df['opponent']
    ))
    
    fig.update_layout(
        title=f'Rating Progression for {player_name}',
        xaxis_title='Date',
        yaxis_title='Rating',
        hovermode='closest',
        showlegend=True,
        height=500,
        template='plotly_white'
    )
    
    # Add grid
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    
    return fig

def calculate_player_stats(player_matches):
    """Calculate statistics for a player"""
    if not player_matches:
        return None
    
    df = pd.DataFrame(player_matches)
    df = df.sort_values('date')
    
    first_rating = df.iloc[0]['rating']
    latest_rating = df.iloc[-1]['rating']
    num_matches = len(df)
    rating_change = latest_rating - first_rating
    
    return {
        'first_rating': first_rating,
        'latest_rating': latest_rating,
        'num_matches': num_matches,
        'rating_change': rating_change,
        'first_date': df.iloc[0]['date'],
        'latest_date': df.iloc[-1]['date']
    }

# Main application
def main():
    st.title("📈 Player Rating Progression Analyzer")
    st.markdown("Upload a CSV file to analyze player rating progression over time")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv",
        help="CSV file should contain columns: Player 1, Player 2, Date, Rating P1, Rating P2"
    )
    
    if uploaded_file is not None:
        # Parse the CSV data
        df = parse_csv_data(uploaded_file)
        
        if df is not None:
            # Show basic info about the dataset
            st.success(f"✅ Successfully loaded {len(df)} matches")
            
            # Extract player data
            player_data = extract_player_data(df)
            
            if not player_data:
                st.error("No player data could be extracted from the file.")
                return
            
            # Get all unique players
            all_players = sorted(list(player_data.keys()))
            
            st.info(f"Found {len(all_players)} unique players")
            
            # Player selection dropdown
            selected_player = st.selectbox(
                "Select a player to view their rating progression:",
                options=all_players,
                index=0 if all_players else None
            )
            
            if selected_player:
                player_matches = player_data[selected_player]
                
                # Create and display the chart
                fig = create_rating_chart(selected_player, player_matches)
                
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Calculate and display statistics
                    stats = calculate_player_stats(player_matches)
                    
                    if stats:
                        st.subheader(f"📊 Statistics for {selected_player}")
                        
                        # Create columns for statistics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric(
                                label="First Rating",
                                value=f"{stats['first_rating']:.1f}",
                                help=f"Rating on {stats['first_date'].strftime('%Y-%m-%d')}"
                            )
                        
                        with col2:
                            st.metric(
                                label="Latest Rating",
                                value=f"{stats['latest_rating']:.1f}",
                                help=f"Rating on {stats['latest_date'].strftime('%Y-%m-%d')}"
                            )
                        
                        with col3:
                            st.metric(
                                label="Number of Matches",
                                value=stats['num_matches']
                            )
                        
                        with col4:
                            delta_color = "normal"
                            if stats['rating_change'] > 0:
                                delta_color = "normal"
                            elif stats['rating_change'] < 0:
                                delta_color = "inverse"
                            
                            st.metric(
                                label="Rating Change",
                                value=f"{stats['rating_change']:+.1f}",
                                delta=f"{stats['rating_change']:+.1f}",
                                help="Total change from first to latest rating"
                            )
                        
                        # Additional details
                        st.markdown("---")
                        st.markdown("**Period:** {} to {}".format(
                            stats['first_date'].strftime('%B %d, %Y'),
                            stats['latest_date'].strftime('%B %d, %Y')
                        ))
                        
                        # Show recent matches
                        st.subheader("🕐 Recent Matches")
                        recent_matches = sorted(player_matches, key=lambda x: x['date'], reverse=True)[:5]
                        
                        recent_df = pd.DataFrame(recent_matches)
                        recent_df['date'] = recent_df['date'].dt.strftime('%Y-%m-%d')
                        recent_df = recent_df.rename(columns={
                            'date': 'Date',
                            'rating': 'Rating',
                            'opponent': 'Opponent'
                        })
                        
                        st.dataframe(recent_df, hide_index=True, width='stretch')
                
                else:
                    st.error("Could not create chart for the selected player.")
    
    else:
        # Show instructions when no file is uploaded
        st.info("👆 Please upload a CSV file to get started")
        
        st.markdown("### Required CSV Format")
        st.markdown("Your CSV file should contain the following columns:")
        
        example_data = {
            'Player 1': ['Alice', 'Bob', 'Charlie'],
            'Player 2': ['Bob', 'Charlie', 'Alice'],
            'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'Rating P1': [1200, 1250, 1180],
            'Rating P2': [1180, 1200, 1220]
        }
        
        example_df = pd.DataFrame(example_data)
        st.dataframe(example_df, hide_index=True, width='stretch')

if __name__ == "__main__":
    main()
