import streamlit as st
import pandas as pd
import random
import time
import uuid
import os

# Set page config
st.set_page_config(
    page_title="Cricket Auction Simulator",
    page_icon="🏏",
    layout="wide"
)

# Initialize session state variables if they don't exist
if 'app_stage' not in st.session_state:
    st.session_state.app_stage = 'setup'
if 'teams' not in st.session_state:
    st.session_state.teams = []
if 'players' not in st.session_state:
    st.session_state.players = []
if 'current_player' not in st.session_state:
    st.session_state.current_player = None
if 'current_bid' not in st.session_state:
    st.session_state.current_bid = 0
if 'current_team' not in st.session_state:
    st.session_state.current_team = None
if 'auction_complete' not in st.session_state:
    st.session_state.auction_complete = False
if 'remaining_players' not in st.session_state:
    st.session_state.remaining_players = []

# Sample player data (you could load this from a CSV or database)
def generate_sample_players():
    player_roles = ['Batsman', 'Bowler', 'All-rounder', 'Wicket-keeper']
    player_countries = ['India', 'Australia', 'England', 'New Zealand', 'South Africa', 'West Indies', 'Pakistan', 'Sri Lanka']
    
    players = []
    # Generate sample player data
    for i in range(100):
        player = {
            'id': str(uuid.uuid4()),
            'name': f"Player {i+1}",
            'role': random.choice(player_roles),
            'country': random.choice(player_countries),
            'base_price': random.choice([0.5, 0.75, 1.0, 1.5, 2.0]),  # Base price in crores
            'stats': {
                'batting_avg': round(random.uniform(20, 60), 1),
                'bowling_avg': round(random.uniform(18, 40), 1),
                'matches_played': random.randint(10, 200)
            },
            'status': 'unsold'
        }
        players.append(player)
    return players

# Initialize or change app stage
def set_stage(stage):
    st.session_state.app_stage = stage

def setup_teams():
    st.title("🏏 Cricket Player Auction Simulator")
    
    st.markdown("""
    ## Setup Teams
    Enter the number of teams participating in the auction and their details.
    Each team will have a purse amount to spend on players.
    """)
    
    num_teams = st.number_input("Number of Teams", min_value=2, max_value=10, value=3, step=1)
    default_purse = st.number_input("Default Purse Amount per Team (in crores)", min_value=5.0, max_value=100.0, value=90.0, step=0.5)
    
    with st.form("team_setup_form"):
        teams = []
        cols = st.columns(2)
        
        for i in range(num_teams):
            with cols[i % 2]:
                st.subheader(f"Team {i+1}")
                name = st.text_input(f"Team Name", value=f"Team {i+1}", key=f"team_name_{i}")
                purse = st.number_input(f"Purse Amount (in crores)", min_value=5.0, max_value=100.0, value=default_purse, step=0.5, key=f"team_purse_{i}")
                
                team = {
                    'id': str(uuid.uuid4()),
                    'name': name,
                    'purse': purse,
                    'original_purse': purse,
                    'players': [],
                    'can_bid': True
                }
                teams.append(team)
        
        max_squad_size = st.number_input("Maximum Squad Size per Team", min_value=11, max_value=25, value=15, step=1)
        
        submit_button = st.form_submit_button("Start Auction")
        
        if submit_button:
            st.session_state.teams = teams
            st.session_state.max_squad_size = max_squad_size
            st.session_state.players = generate_sample_players()
            st.session_state.remaining_players = st.session_state.players.copy()
            set_stage('auction')
            st.experimental_rerun()

def check_auction_complete():
    # Check if auction is complete (all teams have max players or can't bid)
    eligible_teams = [t for t in st.session_state.teams if t['can_bid']]
    if not eligible_teams or not st.session_state.remaining_players:
        st.session_state.auction_complete = True
        set_stage('results')

def view_team_players(team):
    players = team['players']
    if not players:
        st.info(f"{team['name']} hasn't acquired any players yet.")
        return
    
    player_data = []
    for p in players:
        player_data.append({
            'Name': p['name'],
            'Role': p['role'],
            'Country': p['country'],
            'Price': f"₹{p.get('sold_price', 0)} crores",
            'Batting Avg': p['stats']['batting_avg'],
            'Bowling Avg': p['stats']['bowling_avg']
        })
    
    st.dataframe(pd.DataFrame(player_data), use_container_width=True)

def auction_screen():
    st.title("🏏 Cricket Player Auction")
    
    # Display teams and their status
    cols = st.columns(len(st.session_state.teams))
    for i, team in enumerate(st.session_state.teams):
        with cols[i]:
            st.subheader(team['name'])
            st.metric("Remaining Purse", f"₹{team['purse']} crores")
            st.metric("Players", len(team['players']))
            
            # Add dropdown to view current squad
            if st.expander(f"View {team['name']} Squad"):
                view_team_players(team)
            
            # Disable bidding if team has reached max squad size
            if len(team['players']) >= st.session_state.max_squad_size:
                team['can_bid'] = False
                st.warning("Squad Full")
            
            # Disable bidding if team has insufficient funds for minimum bid
            if team['purse'] < 0.5:  # Assuming 0.5 crore is the minimum bid possible
                team['can_bid'] = False
                st.warning("Insufficient Funds")
    
    # Check if auction is complete
    check_auction_complete()
    if st.session_state.auction_complete:
        st.experimental_rerun()
    
    # Player selection
    if st.session_state.current_player is None and st.session_state.remaining_players:
        # Get a new player for auction
        # Sort remaining players by base price for more interesting auction experience
        sorted_players = sorted(st.session_state.remaining_players, key=lambda x: x['base_price'], reverse=True)
        player_index = random.randint(0, min(9, len(sorted_players)-1))  # Pick from top 10 players
        st.session_state.current_player = sorted_players[player_index]
        st.session_state.current_bid = st.session_state.current_player['base_price']
        st.session_state.current_team = None
        
        # Remove this player from remaining players
        st.session_state.remaining_players = [p for p in st.session_state.remaining_players 
                                              if p['id'] != st.session_state.current_player['id']]
    
    # Display current player for auction
    if st.session_state.current_player:
        st.markdown("---")
        player = st.session_state.current_player
    
        # Make the auctioning panel bigger
        auction_col, bid_col = st.columns([3, 1])  # Make auction details take more space
    
        with auction_col:
            st.markdown(f"<h2 style='text-align: center; color: #ff4b4b;'>🎯 Now Auctioning: {player['name']}</h2>", unsafe_allow_html=True)
            st.markdown(f"<h4 style='text-align: center;'>Role: {player['role']} | Country: {player['country']}</h4>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center; color: #007bff;'>Base Price: ₹{player['base_price']} crores</h3>", unsafe_allow_html=True)
    
            # Stats table
            stats_df = pd.DataFrame({
                'Stat': ['Batting Average', 'Bowling Average', 'Matches Played'],
                'Value': [player['stats']['batting_avg'], player['stats']['bowling_avg'], player['stats']['matches_played']]
            })
            st.table(stats_df)
    
        with bid_col:
            st.markdown("<h2 style='text-align: center;'>Current Bid</h2>", unsafe_allow_html=True)
            st.markdown(f"<h1 style='text-align: center; color: #28a745;'>₹{st.session_state.current_bid} crores</h1>", unsafe_allow_html=True)
            
            if st.session_state.current_team:
                team = next((t for t in st.session_state.teams if t['id'] == st.session_state.current_team), None)
                if team:
                    st.markdown(f"<h3 style='text-align: center; color: #ff9800;'>Current Bidder: {team['name']}</h3>", unsafe_allow_html=True)
    
        st.markdown("---")

        
        # Bidding interface
        cols = st.columns(len(st.session_state.teams) + 1)  # +1 for the unsold button
        
        # Calculate minimum bid increment
        if st.session_state.current_bid < 1:
            increment = 0.05
        elif st.session_state.current_bid < 2:
            increment = 0.1
        elif st.session_state.current_bid < 5:
            increment = 0.2
        else:
            increment = 0.25
        
        # Create a bid button for each team
        for i, team in enumerate(st.session_state.teams):
            with cols[i]:
                new_bid = round(st.session_state.current_bid + increment, 2)
                can_bid = team['can_bid'] and team['purse'] >= new_bid
                
                if can_bid:
                    bid_button = st.button(f"{team['name']}\n₹{new_bid} crores", key=f"bid_{team['id']}")
                    if bid_button:
                        st.session_state.current_bid = new_bid
                        st.session_state.current_team = team['id']
                        st.experimental_rerun()
                else:
                    st.button(f"{team['name']}\nCannot Bid", disabled=True)
        
        # Add the "Sold!" button in the last column
        with cols[-1]:
            if st.session_state.current_team:  # Only enable if someone has bid
                sold_button = st.button("SOLD! ⚡", key="sold_button")
                if sold_button:
                    # Add player to the team that won the bid
                    team = next((t for t in st.session_state.teams if t['id'] == st.session_state.current_team), None)
                    if team:
                        player['status'] = 'sold'
                        player['sold_to'] = team['name']
                        player['sold_price'] = st.session_state.current_bid
                        team['players'].append(player)
                        team['purse'] -= st.session_state.current_bid
                        
                        st.success(f"{player['name']} sold to {team['name']} for ₹{st.session_state.current_bid} crores!")
                        time.sleep(1)  # Pause briefly to show the success message
                        
                        # Reset for next player
                        st.session_state.current_player = None
                        st.session_state.current_bid = 0
                        st.session_state.current_team = None
                        st.experimental_rerun()
            else:
                st.button("SOLD! ⚡", disabled=True)
        
        # Add "Unsold" button
        unsold_button = st.button("Unsold ❌", key="unsold_button")
        if unsold_button:
            player['status'] = 'unsold'
            st.info(f"{player['name']} remains unsold.")
            time.sleep(1)  # Pause briefly to show the info message
            
            # Reset for next player
            st.session_state.current_player = None
            st.session_state.current_bid = 0
            st.session_state.current_team = None
            st.experimental_rerun()
    
    # Show auction progress
    st.markdown("---")
    st.subheader("Auction Progress")
    
    sold_players = [p for p in st.session_state.players if p['status'] == 'sold']
    unsold_players = [p for p in st.session_state.players if p['status'] == 'unsold']
    remaining_players = st.session_state.remaining_players
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Players Sold", len(sold_players))
    with col2:
        st.metric("Players Unsold", len(unsold_players))
    with col3:
        st.metric("Players Remaining", len(remaining_players))
    
    # Option to view transaction log
    if st.checkbox("Show Transaction Log"):
        if sold_players:
            transactions = []
            for p in sold_players:
                transactions.append({
                    'Player': p['name'],
                    'Role': p['role'],
                    'Team': p.get('sold_to', ''),
                    'Price': f"₹{p.get('sold_price', 0)} crores"
                })
            st.table(pd.DataFrame(transactions))
        else:
            st.info("No transactions yet.")

def save_team_to_csv(team):
    """Save individual team data to a CSV file"""
    if not os.path.exists('team_data'):
        os.makedirs('team_data')
        
    if not team['players']:
        return False
        
    player_data = []
    for p in team['players']:
        player_data.append({
            'Name': p['name'],
            'Role': p['role'],
            'Country': p['country'],
            'Price (crores)': p.get('sold_price', 0),
            'Batting Avg': p['stats']['batting_avg'],
            'Bowling Avg': p['stats']['bowling_avg'],
            'Matches': p['stats']['matches_played']
        })
    
    df = pd.DataFrame(player_data)
    
    # Add team summary at the bottom
    summary_df = pd.DataFrame([{
        'Name': f"TEAM SUMMARY: {team['name']}",
        'Role': '',
        'Country': '',
        'Price (crores)': team['original_purse'] - team['purse'],
        'Batting Avg': '',
        'Bowling Avg': '',
        'Matches': ''
    }])
    
    result_df = pd.concat([df, summary_df])
    
    # Replace invalid characters in team name for filename
    filename = team['name'].replace(" ", "_").replace("/", "_").replace("\\", "_")
    filepath = f"team_data/{filename}.csv"
    result_df.to_csv(filepath, index=False)
    return filepath

def results_screen():
    st.title("🏆 Auction Results")
    
    st.markdown("""
    ## Auction Completed!
    View the final team compositions and statistics below.
    """)
    
    # Summary statistics
    total_spent = sum(team['original_purse'] - team['purse'] for team in st.session_state.teams)
    avg_player_price = round(total_spent / sum(len(team['players']) for team in st.session_state.teams), 2) if sum(len(team['players']) for team in st.session_state.teams) > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Amount Spent", f"₹{total_spent} crores")
    with col2:
        st.metric("Avg. Player Price", f"₹{avg_player_price} crores")
    with col3:
        sold_players = [p for p in st.session_state.players if p['status'] == 'sold']
        if sold_players:
            highest_paid = max(sold_players, key=lambda x: x.get('sold_price', 0))
            st.metric("Highest Paid Player", f"{highest_paid['name']} (₹{highest_paid.get('sold_price', 0)} crores)")
        else:
            st.metric("Highest Paid Player", "None")
    
    # Team tabs
    team_tabs = st.tabs([team['name'] for team in st.session_state.teams])
    
    team_files = []
    for i, tab in enumerate(team_tabs):
        with tab:
            team = st.session_state.teams[i]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Players Acquired", len(team['players']))
            with col2:
                st.metric("Purse Spent", f"₹{team['original_purse'] - team['purse']} crores")
            with col3:
                st.metric("Purse Remaining", f"₹{team['purse']} crores")
            
            # Team composition by role
            roles = {}
            for player in team['players']:
                role = player['role']
                if role in roles:
                    roles[role] += 1
                else:
                    roles[role] = 1
            
            if roles:
                st.subheader("Team Composition")
                composition_df = pd.DataFrame({
                    'Role': list(roles.keys()),
                    'Count': list(roles.values())
                })
                st.bar_chart(composition_df.set_index('Role'))
            
            # Player details
            st.subheader("Player List")
            if team['players']:
                player_data = []
                for p in team['players']:
                    player_data.append({
                        'Name': p['name'],
                        'Role': p['role'],
                        'Country': p['country'],
                        'Price': f"₹{p.get('sold_price', 0)} crores",
                        'Batting Avg': p['stats']['batting_avg'],
                        'Bowling Avg': p['stats']['bowling_avg'],
                        'Matches': p['stats']['matches_played']
                    })
                st.dataframe(pd.DataFrame(player_data), use_container_width=True)
                
                # Save team data to CSV
                filepath = save_team_to_csv(team)
                if filepath:
                    team_files.append((team['name'], filepath))
                    
                    # Provide download button for this team's CSV
                    team_df = pd.read_csv(filepath)
                    csv = team_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label=f"Download {team['name']} Squad",
                        data=csv,
                        file_name=f"{team['name']}_squad.csv",
                        mime="text/csv",
                    )
            else:
                st.info("No players acquired.")
    
    # Download all results
    if st.button("Download Complete Auction Results"):
        results = []
        for team in st.session_state.teams:
            for player in team['players']:
                results.append({
                    'Team': team['name'],
                    'Player': player['name'],
                    'Role': player['role'],
                    'Country': player['country'],
                    'Price (crores)': player.get('sold_price', 0),
                    'Batting Avg': player['stats']['batting_avg'],
                    'Bowling Avg': player['stats']['bowling_avg'],
                    'Matches': player['stats']['matches_played']
                })
        
        results_df = pd.DataFrame(results)
        
        # Convert dataframe to CSV
        csv = results_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Complete Auction CSV",
            data=csv,
            file_name="cricket_auction_results.csv",
            mime="text/csv",
        )
    
    # Display information about saved files
    if team_files:
        st.markdown("---")
        st.subheader("Team Files Saved")
        st.write("Each team's data has been saved to a separate CSV file with their respective name.")
        for team_name, filepath in team_files:
            st.success(f"{team_name}: {filepath}")
    
    # Reset auction
    if st.button("Start New Auction"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.experimental_rerun()

# Main app logic
def main():
    if st.session_state.app_stage == 'setup':
        setup_teams()
    elif st.session_state.app_stage == 'auction':
        auction_screen()
    elif st.session_state.app_stage == 'results':
        results_screen()

if __name__ == "__main__":
    main()