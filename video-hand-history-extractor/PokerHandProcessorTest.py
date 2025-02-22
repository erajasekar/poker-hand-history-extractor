import os
import json
import re
from datetime import datetime
from CraftyWheelPokerHandHistory import CraftyWheelPokerHandHistory
from PokerHandProcessor import PokerHandProcessor
from poker_hand_history import PokerHandHistoryGenerator

# Input directory containing JSON files
input_dir = "export/obsidian/2024_wsop_game3_process"

# Get all JSON files from the directory
json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]

# Sort files by the number before "_analysis" in filename
def extract_number(filename):
    match = re.search(r'TABLE_(\d+)_analysis', filename)
    return int(match.group(1)) if match else float('inf')

json_files.sort(key=extract_number)

# Get OpenAI API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise Exception("OPENAI_API_KEY environment variable not set")

# Create processor and generator instances
processor = PokerHandProcessor()
generator = PokerHandHistoryGenerator(api_key=api_key, output_dir="logs")

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
        
        # Process the hand history
        processor.handle(hand_history)
        
    except Exception as e:
        print(f"Error processing {json_file}: {str(e)}")

# Get final hand history
final_history = processor.get_final_hand_history()
if final_history:
    # Print final history in JSON format
    print("\nFinal History JSON:")
    print(processor.get_final_hand_history_json())
    
    # Generate hand history in PokerStars format
    hand_history = generator.generate_hand_history(final_history)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"hand_history_{timestamp}.txt"
    output_path = os.path.join(input_dir, output_filename)
    
    # Write hand history to file
    with open(output_path, 'w') as f:
        f.write(hand_history)
    
    print(f"\nHand history written to: {output_path}")
else:
    print("\nNo valid hand history data available")
