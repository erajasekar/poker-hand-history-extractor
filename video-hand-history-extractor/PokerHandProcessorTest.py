import os
import json
import re
from datetime import datetime
from CraftyWheelPokerHandHistory import CraftyWheelPokerHandHistory
from PokerHandProcessor import PokerHandProcessor
from poker_hand_history import PokerHandHistoryGenerator

# Input directory containing JSON files
input_dir = "export/obsidian/2024_wsop_game3_process"

# Configuration flags
generate_hand_history = True  # Set to False to skip hand history text generation

# Get all JSON files from the directory (excluding final_history files)
json_files = [f for f in os.listdir(input_dir) if f.endswith('.json') and not f.startswith('final_history')]

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
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save final history to JSON file
    json_filename = f"final_history_{timestamp}.json"
    json_path = os.path.join(input_dir, json_filename)
    with open(json_path, 'w') as f:
        json.dump(final_history.model_dump(), f, indent=2)
    print(f"\nFinal history JSON written to: {json_path}")
    
    # Generate and save hand history text if flag is enabled
    if generate_hand_history:
        # Generate hand history in PokerStars format
        hand_history = generator.generate_hand_history(final_history)
        
        # Save hand history to text file
        output_filename = f"hand_history_{timestamp}.txt"
        output_path = os.path.join(input_dir, output_filename)
        with open(output_path, 'w') as f:
            f.write(hand_history)
        
        print(f"\nHand history written to: {output_path}")
else:
    print("\nNo valid hand history data available")
