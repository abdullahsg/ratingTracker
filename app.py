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

def load_stored_data():
    """Load and validate the stored CSV data"""
    try:
        # Read the CSV file from storage
        df = pd.read_csv('data.csv')
        
        # Check if required columns exist
        required_columns = ['SL No', 'Date', 'Player 1', 'Player 2', 'Rating P1', 'Rating P2']
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
        missing_check = df[['SL No', 'Player 1', 'Player 2', 'Date', 'Rating P1', 'Rating P2']].isnull()
        if missing_check.any().any():
            st.warning("Some rows contain missing values. These will be excluded from analysis.")
            df = df.dropna(subset=['SL No', 'Player 1', 'Player 2', 'Date', 'Rating P1', 'Rating P2'])
        
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
            'sl_no': row['SL No'],
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
            'sl_no': row['SL No'],
            'date': date,
            'rating': rating,
            'opponent': row['Player 1']
        })
    
    # Sort each player's data by SL No and remove duplicates
    for player in player_data:
        # Convert to DataFrame for easier manipulation
        player_df = pd.DataFrame(player_data[player])
        # Sort by SL No and remove duplicates (keeping last occurrence for same SL No)
        player_df = player_df.sort_values('sl_no').drop_duplicates(subset=['sl_no'], keep='last')
        player_data[player] = player_df.to_dict('records')
    
    return player_data

def create_rating_chart(player_name, player_matches):
    """Create an interactive Plotly chart for player rating progression"""
    if not player_matches:
        return None
    
    # Convert to DataFrame for easier plotting
    df = pd.DataFrame(player_matches)
    df = df.sort_values('sl_no')
    
    # Create a continuous x-axis using SL No but display dates on hover
    df['x_position'] = range(len(df))  # Sequential position for horizontal flow
    
    # Create the line chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['x_position'],
        y=df['rating'],
        mode='lines+markers',
        name=f'{player_name} Rating',
        line=dict(width=3, color='#1f77b4', shape='spline', smoothing=0.3),
        marker=dict(size=8, color='#1f77b4'),
        hovertemplate='<b>Match #:</b> %{customdata[0]}<br>' +
                      '<b>Date:</b> %{customdata[1]}<br>' +
                      '<b>Rating:</b> %{y}<br>' +
                      '<b>Opponent:</b> %{customdata[2]}<br>' +
                      '<extra></extra>',
        customdata=list(zip(df['sl_no'], df['date'].dt.strftime('%Y-%m-%d'), df['opponent']))
    ))
    
    fig.update_layout(
        title=f'Rating Progression for {player_name}',
        xaxis_title='Match Sequence',
        yaxis_title='Rating',
        hovermode='closest',
        showlegend=True,
        height=500,
        template='plotly_white'
    )
    
    # Customize x-axis to show match numbers
    fig.update_xaxes(
        tickmode='linear',
        tick0=0,
        dtick=max(1, len(df) // 10),  # Show reasonable number of ticks
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgray'
    )
    
    # Add grid for y-axis
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    
    return fig

def calculate_player_stats(player_matches):
    """Calculate statistics for a player"""
    if not player_matches:
        return None
    
    df = pd.DataFrame(player_matches)
    df = df.sort_values('sl_no')
    
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
    st.markdown("Analyze player rating progression over time from tournament data")
    
    # Load the stored data
    df = load_stored_data()
    
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
                    recent_matches = sorted(player_matches, key=lambda x: x['sl_no'], reverse=True)[:5]
                    
                    recent_df = pd.DataFrame(recent_matches)
                    recent_df['date'] = recent_df['date'].dt.strftime('%Y-%m-%d')
                    recent_df = recent_df.rename(columns={
                        'sl_no': 'SL No',
                        'date': 'Date',
                        'rating': 'Rating',
                        'opponent': 'Opponent'
                    })
                    # Reorder columns to show SL No first
                    recent_df = recent_df[['SL No', 'Date', 'Rating', 'Opponent']]
                    
                    st.dataframe(recent_df, hide_index=True, width='stretch')
            
            else:
                st.error("Could not create chart for the selected player.")
    
    else:
        st.error("❌ Could not load tournament data. Please check the data file.")

if __name__ == "__main__":
    main()
