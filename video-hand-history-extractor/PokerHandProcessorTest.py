import os
import json
import re
from CraftyWheelPokerHandHistory import CraftyWheelPokerHandHistory

# Input directory containing JSON files
input_dir = "export/obsidian/2024_wsop_game3_process"

# Get all JSON files from the directory
json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]

# Sort files by the number before "_analysis" in filename
def extract_number(filename):
    match = re.search(r'TABLE_(\d+)_analysis', filename)
    return int(match.group(1)) if match else float('inf')

json_files.sort(key=extract_number)

# Process each file
for json_file in json_files:
    file_path = os.path.join(input_dir, json_file)
    
    try:
        # Read and parse JSON file
        with open(file_path, 'r') as f:
            json_data = json.load(f)
        
        # Create CraftyWheelPokerHandHistory object
        hand_history = CraftyWheelPokerHandHistory.from_openai_response(json_data)
        
        # Print the object and current street
        print(f"\nProcessing file: {json_file}")
        print(f"Current street: {hand_history.get_current_street()}")
        
        # Print players with cards
        players_with_cards = hand_history.get_player_with_cards()
        print("Players with cards:")
        for player in players_with_cards:
            print(f"- {player.name}: {player.cards}")
        
    except Exception as e:
        print(f"Error processing {json_file}: {str(e)}")
