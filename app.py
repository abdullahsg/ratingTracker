import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import rating_engine


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
        result = row['Result']  # Result from Player 1's perspective
        
        if player not in player_data:
            player_data[player] = []
        
        player_data[player].append({
            'sl_no': row['SL No'],
            'date': date,
            'rating': rating,
            'opponent': row['Player 2'],
            'result': result
        })
    
    # Process player2 ratings
    for _, row in df.iterrows():
        player = row['Player 2']
        date = row['Date']
        rating = row['Rating P2']
        # Flip the result for Player 2 (e.g., "2-0" becomes "0-2")
        original_result = row['Result']
        if '-' in original_result:
            parts = original_result.split('-')
            flipped_result = f"{parts[1]}-{parts[0]}"
        else:
            flipped_result = original_result
        
        if player not in player_data:
            player_data[player] = []
        
        player_data[player].append({
            'sl_no': row['SL No'],
            'date': date,
            'rating': rating,
            'opponent': row['Player 1'],
            'result': flipped_result
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
                      '<b>Result:</b> %{customdata[2]}<br>' +
                      '<b>Opponent:</b> %{customdata[1]}<br>' +
                      '<extra></extra>',
        customdata=list(zip(df['date'].dt.strftime('%Y-%m-%d'), df['opponent'], df['result']))
    ))
    
    fig.update_layout(
        title=f'Rating Progression for {player_name}',
        hovermode='closest',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
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
                          '<b>Result:</b> %{customdata[2]}<br>' +
                          '<b>Date:</b> %{customdata[0]}<br>' +
                          '<b>Opponent:</b> %{customdata[1]}<br>' +
                          '<extra></extra>',
            customdata=list(zip(df['date'].dt.strftime('%Y-%m-%d'), df['opponent'], df['result']))
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
        hovermode='closest',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
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
    # Remove top padding/margin
    st.markdown("""
        <style>
        .main .block-container {
            padding-top: 0rem;
            padding-bottom: 0rem;
            margin-top: 0rem;
        }
        .stApp > header {
            height: 0px;
        }
        </style>
        """, unsafe_allow_html=True)
    
    
    # Load the stored data
    df = load_stored_data()
    
    if df is not None:
        # Extract player data
        player_data = extract_player_data(df)
        
        if not player_data:
            st.error("No player data could be extracted from the file.")
            return
        
        # Get all unique players
        all_players = sorted(list(player_data.keys()))
        
        # Create tabs
        tab1, tab3, tab4, tab2 = st.tabs([
            "📊 Single Player Analysis", 
            "🏆 Leaderboard", 
            "📅 Match List",
            "📈 Player Comparison"
        ])
        
        with tab1:
            # Player selection dropdown
            selected_player = st.selectbox(
                "Select a player to view their rating progression:",
                options=all_players,
                index=None,
                key="single_player_select"
            )
            
            show_single_chart = False
            if selected_player:
                show_single_chart = st.button("📊 Show Player Analysis", key="show_single_btn")
            
            if selected_player and show_single_chart:
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
            
            show_comparison_chart = False
            if selected_players:
                show_comparison_chart = st.button("📈 Compare Players", key="show_comparison_btn")
            
            if selected_players and show_comparison_chart:
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

        with tab3:
            st.header("🏆 Leaderboard")
            
            # Generate leaderboard with changes
            leaderboard_df = rating_engine.generate_leaderboard_with_changes(df)
            
            if not leaderboard_df.empty:
                # Function to apply styles
                def highlight_change(row):
                    change = row['Rating Change']
                    is_new = row['Is New']
                    
                    bg_color = ''
                    if is_new:
                        bg_color = 'background-color: #7dc0ff' # Light Blue
                    elif change > 0:
                        bg_color = 'background-color: #90ee90' # Light Green
                    elif change < 0:
                        bg_color = 'background-color: #ffcccb' # Light Red
                        
                    return [bg_color if col == 'Rating Change' else '' for col in row.index]

                # Format columns
                display_df = leaderboard_df.copy()
                
                # Format Rating Change for display to handle "New" text
                display_df['Rating Change Display'] = display_df.apply(
                    lambda x: "New" if x['Is New'] else f"{x['Rating Change']:+.0f}", axis=1
                )
                
                # Drop technical columns for display
                display_cols = ['Rank', 'Player Name', 'Last Rating', 'Matches Played', 'Won', 'Win Percentage', 'Rating Change Display']
                final_df = display_df[display_cols].rename(columns={'Rating Change Display': 'Rating Change'})
                
                # Apply styling to the original dataframe logic, but map to display df
                # Streamlit dataframe styling is a bit tricky with hidden columns. 
                # Let's try to style the specific column 'Rating Change' based on the underlying data.
                # Actually, simpler approach: Just style the dataframe directly.
                
                # Re-create dataframe for styling to ensure columns align
                # We need to preserve the logic for styling
                
                def style_specific_cell(x):
                    # This function sees the whole dataframe
                    df1 = pd.DataFrame('', index=x.index, columns=x.columns)
                    
                    # Logic relies on 'Is New' which is not in final_df. 
                    # So we must compute style before dropping, OR keep 'Is New' and hide it? 
                    # st.dataframe column_config can hide columns.
                    
                    return df1

                # Better Approach: Add a pure data column for styling
                leaderboard_df['Change Text'] = leaderboard_df.apply(
                    lambda x: "New" if x['Is New'] else f"{x['Rating Change']:+.0f}", axis=1
                )
                
                final_view = leaderboard_df[['Rank', 'Player Name', 'Last Rating', 'Matches Played', 'Won', 'Win Percentage', 'Change Text']]
                final_view = final_view.rename(columns={'Change Text': 'Rating Change'})

                def color_rating_change(val):
                    # This receives the value of the cell.
                    # Problem: "New" vs "+5" vs "-5"
                    if val == "New":
                        return 'background-color: #7dc0ff; color: black'
                    try:
                        f_val = float(val)
                        if f_val > 0:
                            return 'background-color: #90ee90; color: black'
                        elif f_val < 0:
                            return 'background-color: #ffcccb; color: black'
                    except:
                        pass
                    return ''

                try:
                    st.dataframe(
                        final_view.style.map(color_rating_change, subset=['Rating Change'])
                                  .format({'Win Percentage': '{:.2%}', 'Last Rating': '{:.0f}'}),
                        use_container_width=True,
                        hide_index=True
                    )
                except Exception as e:
                    st.error(f"Error displaying leaderboard: {e}")
                    st.dataframe(final_view)
            else:
                st.info("No data available for leaderboard.")

        with tab4:
            st.header("📅 Match List")
            
            # Filter by player
            col1, col2 = st.columns([1, 2])
            with col1:
                player_filter = st.multiselect(
                    "Filter by Player:",
                    options=all_players,
                    key="match_list_filter"
                )
            
            # Prepare match data
            # We want all matches, sorted by Date desc
            matches_df = df.copy()
            matches_df['Date'] = pd.to_datetime(matches_df['Date'])
            
            if player_filter:
                # Filter rows where P1 or P2 is in the list
                mask = matches_df['Player 1'].isin(player_filter) | matches_df['Player 2'].isin(player_filter)
                matches_df = matches_df[mask]
            
            # Sort
            matches_df = matches_df.sort_values(by=['Date', 'SL No'], ascending=[False, False])
            
            # Format Date
            matches_df['Date'] = matches_df['Date'].dt.strftime('%Y-%m-%d')
            
            # Display
            st.dataframe(
                matches_df[['SL No', 'Date', 'Player 1', 'Player 2', 'Result', 'Rating P1', 'Rating P2']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rating P1": st.column_config.NumberColumn("Rating P1", format="%d"),
                    "Rating P2": st.column_config.NumberColumn("Rating P2", format="%d"),
                }
            )
    
    else:
        st.error("❌ Could not load tournament data. Please check the data file.")

    # Rating Administration Section (Sidebar or Main Area)
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Rating Administration")
    
    if st.sidebar.button("🔄 Recalculate Ratings"):
        with st.spinner("Recalculating ratings..."):
            try:
                # Load current data
                current_df = pd.read_csv('data.csv')
                # Load initial ratings
                initial_ratings_df = pd.read_csv('initial_ratings.csv')
                
                # Perform recalculation
                new_df = rating_engine.calculate_ratings(current_df, initial_ratings_df)
                
                # Show preview
                st.subheader("📝 Recalculation Preview")
                st.info("Ratings have been recalculated using the new formula (K=16, Divisor=150).")
                st.dataframe(new_df.head(), use_container_width=True)
                
                # Convert to CSV for download
                csv_buffer = io.StringIO()
                new_df.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()
                
                st.download_button(
                    label="💾 Download Updated Ratings CSV",
                    data=csv_data,
                    file_name="updated_ratings.csv",
                    mime="text/csv",
                    key="download_new_ratings"
                )
                
                st.success("Calculation complete! Download the file above.")
                
            except Exception as e:
                st.error(f"Error during recalculation: {str(e)}")



if __name__ == "__main__":
    main()
