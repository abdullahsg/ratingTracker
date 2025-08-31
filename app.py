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
    
    # Use SL No for x-axis positioning but show dates
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['sl_no'],  # Use SL No for proper sequential spacing
        y=df['rating'],
        mode='lines+markers',
        name=f'{player_name} Rating',
        line=dict(width=3, color='#1f77b4', shape='spline', smoothing=0.3),
        marker=dict(size=8, color='#1f77b4'),
        hovertemplate='<b>Match #:</b> %{x}<br>' +
                      '<b>Date:</b> %{customdata[0]}<br>' +
                      '<b>Rating:</b> %{y}<br>' +
                      '<b>Opponent:</b> %{customdata[1]}<br>' +
                      '<extra></extra>',
        customdata=list(zip(df['date'].dt.strftime('%Y-%m-%d'), df['opponent']))
    ))
    
    fig.update_layout(
        title=f'Rating Progression for {player_name}',
        xaxis_title='Match Number (Tournament Sequence)',
        yaxis_title='Rating',
        hovermode='closest',
        showlegend=True,
        height=500,
        template='plotly_white'
    )
    
    # Create custom tick labels showing dates at key points
    tick_interval = max(1, len(df) // 8)  # Show about 8 date labels
    tick_vals = []
    tick_texts = []
    
    for i in range(0, len(df), tick_interval):
        tick_vals.append(df.iloc[i]['sl_no'])
        tick_texts.append(df.iloc[i]['date'].strftime('%b %d'))
    
    # Add the last point if not already included
    if len(df) > 0 and (len(tick_vals) == 0 or tick_vals[-1] != df.iloc[-1]['sl_no']):
        tick_vals.append(df.iloc[-1]['sl_no'])
        tick_texts.append(df.iloc[-1]['date'].strftime('%b %d'))
    
    # Customize x-axis to show dates at key matches
    fig.update_xaxes(
        tickmode='array',
        tickvals=tick_vals,
        ticktext=tick_texts,
        showgrid=True,
        gridwidth=0.5,
        gridcolor='rgba(128,128,128,0.2)'
    )
    
    # Add subtle grid for y-axis
    fig.update_yaxes(
        showgrid=True, 
        gridwidth=0.5, 
        gridcolor='rgba(128,128,128,0.2)'
    )
    
    return fig

def create_comparison_chart(selected_players, player_data):
    """Create an interactive Plotly chart comparing multiple players"""
    if not selected_players:
        return None
    
    # Create the comparison chart
    fig = go.Figure()
    
    # Define colors for different players
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    for i, player_name in enumerate(selected_players):
        player_matches = player_data.get(player_name, [])
        if not player_matches:
            continue
            
        # Convert to DataFrame for easier plotting
        df = pd.DataFrame(player_matches)
        df = df.sort_values('sl_no')
        
        # Use SL No as x-axis for proper chronological ordering
        color = colors[i % len(colors)]
        
        fig.add_trace(go.Scatter(
            x=df['sl_no'],
            y=df['rating'],
            mode='lines+markers',
            name=f'{player_name}',
            line=dict(width=3, color=color, shape='spline', smoothing=0.3),
            marker=dict(size=6, color=color),
            hovertemplate='<b>Player:</b> ' + player_name + '<br>' +
                          '<b>Match #:</b> %{x}<br>' +
                          '<b>Rating:</b> %{y}<br>' +
                          '<b>Date:</b> %{customdata[0]}<br>' +
                          '<b>Opponent:</b> %{customdata[1]}<br>' +
                          '<extra></extra>',
            customdata=list(zip(df['date'].dt.strftime('%Y-%m-%d'), df['opponent']))
        ))
    
    # Get all unique dates and SL numbers for custom x-axis labels
    all_matches = []
    for player_name in selected_players:
        player_matches = player_data.get(player_name, [])
        if player_matches:
            df_temp = pd.DataFrame(player_matches)
            df_temp = df_temp.sort_values('sl_no')
            all_matches.extend(zip(df_temp['sl_no'], df_temp['date']))
    
    # Remove duplicates and sort by SL No
    unique_matches = list(set(all_matches))
    unique_matches.sort(key=lambda x: x[0])  # Sort by SL No
    
    # Create tick labels showing dates at key match numbers
    if unique_matches:
        tick_interval = max(1, len(unique_matches) // 10)  # Show about 10 date labels
        tick_vals = []
        tick_texts = []
        
        for i in range(0, len(unique_matches), tick_interval):
            sl_no, date = unique_matches[i]
            tick_vals.append(sl_no)
            tick_texts.append(date.strftime('%b %d'))
        
        # Add the last point if not already included
        if len(unique_matches) > 0 and (len(tick_vals) == 0 or tick_vals[-1] != unique_matches[-1][0]):
            sl_no, date = unique_matches[-1]
            tick_vals.append(sl_no)
            tick_texts.append(date.strftime('%b %d'))
    else:
        tick_vals = []
        tick_texts = []
    
    fig.update_layout(
        title=f'Rating Progression Comparison - {len(selected_players)} Players',
        xaxis_title='Tournament Progress (Match Sequence)',
        yaxis_title='Rating',
        hovermode='closest',
        showlegend=True,
        height=600,
        template='plotly_white'
    )
    
    # Customize x-axis to show dates
    if tick_vals:
        fig.update_xaxes(
            tickmode='array',
            tickvals=tick_vals,
            ticktext=tick_texts,
            showgrid=True,
            gridwidth=0.5,
            gridcolor='rgba(128,128,128,0.2)'
        )
    else:
        fig.update_xaxes(
            showgrid=True, 
            gridwidth=0.5, 
            gridcolor='rgba(128,128,128,0.2)'
        )
    
    # Add subtle grid for y-axis
    fig.update_yaxes(
        showgrid=True, 
        gridwidth=0.5, 
        gridcolor='rgba(128,128,128,0.2)'
    )
    
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
        
        # Create tabs for single player and comparison views
        tab1, tab2 = st.tabs(["📊 Single Player Analysis", "📈 Player Comparison"])
        
        with tab1:
            # Player selection dropdown
            selected_player = st.selectbox(
                "Select a player to view their rating progression:",
                options=all_players,
                index=None,
                key="single_player_select"
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
        
        with tab2:
            # Multi-player selection
            st.markdown("**Select multiple players to compare their rating progressions:**")
            selected_players = st.multiselect(
                "Choose players for comparison:",
                options=all_players,
                default=[],
                key="multi_player_select"
            )
            
            if selected_players:
                if len(selected_players) > 10:
                    st.warning("⚠️ Showing more than 10 players may make the chart hard to read. Consider selecting fewer players.")
                
                # Create and display comparison chart
                comparison_fig = create_comparison_chart(selected_players, player_data)
                
                if comparison_fig:
                    st.plotly_chart(comparison_fig, use_container_width=True)
                    
                    # Show comparison statistics
                    st.subheader("📊 Comparison Statistics")
                    
                    comparison_stats = []
                    for player_name in selected_players:
                        player_matches = player_data[player_name]
                        stats = calculate_player_stats(player_matches)
                        
                        if stats:
                            comparison_stats.append({
                                'Player': player_name,
                                'First Rating': f"{stats['first_rating']:.1f}",
                                'Latest Rating': f"{stats['latest_rating']:.1f}",
                                'Rating Change': f"{stats['rating_change']:+.1f}",
                                'Total Matches': stats['num_matches'],
                                'Period': f"{stats['first_date'].strftime('%b %Y')} - {stats['latest_date'].strftime('%b %Y')}"
                            })
                    
                    if comparison_stats:
                        comparison_df = pd.DataFrame(comparison_stats)
                        st.dataframe(comparison_df, hide_index=True, width='stretch')
                        
                        # Show top performers
                        st.markdown("---")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            # Highest current rating
                            highest_current = max(comparison_stats, key=lambda x: float(x['Latest Rating']))
                            st.metric(
                                "🏆 Highest Current Rating",
                                value=highest_current['Latest Rating']
                            )
                            st.caption(highest_current['Player'])
                        
                        with col2:
                            # Biggest improvement
                            biggest_gain = max(comparison_stats, key=lambda x: float(x['Rating Change'].replace('+', '')))
                            st.metric(
                                "📈 Biggest Rating Gain",
                                value=biggest_gain['Rating Change']
                            )
                            st.caption(biggest_gain['Player'])
                        
                        with col3:
                            # Most active
                            most_active = max(comparison_stats, key=lambda x: x['Total Matches'])
                            st.metric(
                                "🎯 Most Active Player",
                                value=f"{most_active['Total Matches']} matches"
                            )
                            st.caption(most_active['Player'])
                
                else:
                    st.error("Could not create comparison chart.")
            
            else:
                st.info("👆 Select at least 2 players to see a comparison chart")
    
    else:
        st.error("❌ Could not load tournament data. Please check the data file.")

if __name__ == "__main__":
    main()
