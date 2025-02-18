import os
import json
import re
import base64
import logging
from typing import List, Dict, Any
from openai import OpenAI
from datetime import datetime
from pathlib import Path

class PokerHandHistoryGenerator:
    def __init__(self, api_key: str, log_dir: str = "logs"):
        self.client = OpenAI(api_key=api_key)
        self.log_dir = log_dir
        
        # Create logs directory if it doesn't exist
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'poker_analysis.log')),
                logging.StreamHandler()
            ]
        )
        
    def _extract_image_number(self, filename: str) -> int:
        """Extract the last number from filename."""
        numbers = re.findall(r'\d+', filename)
        return int(numbers[-1]) if numbers else 0
        
    def _get_sorted_images(self, directory: str) -> List[str]:
        """Get list of image files sorted by their number."""
        image_files = [f for f in os.listdir(directory) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        return sorted(image_files, key=self._extract_image_number)
        
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze a single poker game image using OpenAI Vision."""
        prompt = """
        Extract the following poker game details from the provided image and output the information in a structured JSON format.

        Fields to Extract:
        1. Tournament Details:
           • tournament_name: Name of the tournament.
           • blind_levels: Current blinds (small blind, big blind).
        2. Player Information:
           • players: List of players with their chip stacks.
           • button_seat: Seat number of the dealer button.
        3. Pre-Flop Action:
           • pre_flop: List of actions with player name, action type, and amount.
        4. Post-Flop Actions:
           • flop_cards: Three community cards.
           • flop_action: List of actions taken on the flop.
        5. Turn Actions:
           • turn_card: Fourth community card.
           • turn_action: List of actions taken on the turn.
        6. River Actions:
           • river_card: Fifth community card.
           • river_action: List of actions taken on the river.
        7. Showdown:
           • showdown: Players who revealed their hands and the winner.
        8. Summary:
           • summary: Final pot size and board cards.
        
        Note: If any information is unclear in the image, include a "missing_details" field with an explanation.
        """
        
        try:
            logging.info(f"Analyzing image: {image_path}")
            
            with open(image_path, "rb") as image_file:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64.b64encode(image_file.read()).decode()}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=4000
                )
                
                # Extract and parse JSON from response
                content = response.choices[0].message.content
                try:
                    result = json.loads(content)
                except json.JSONDecodeError:
                    # If the response isn't pure JSON, try to extract JSON portion
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                    else:
                        raise Exception("Failed to parse JSON from response")
                
                # Save analysis output to a JSON file 
                analysis_filename = os.path.splitext(os.path.basename(image_path))[0] + "_analysis.json"
                analysis_path = os.path.join(self.log_dir, analysis_filename)
                with open(analysis_path, 'w') as f:
                    json.dump(result, f, indent=2)
                logging.info(f"Saved analysis to: {analysis_path}")
                
                return result
                    
        except Exception as e:
            error_msg = f"Error analyzing image {image_path}: {str(e)}"
            logging.error(error_msg)
            return {"error": error_msg}

    def _generate_hand_history_prompt(self, image_data: List[Dict[str, Any]]) -> str:
        """Generate the prompt for LLM to create hand history."""
        prompt = """
        Using multiple structured outputs from previous extractions, generate a complete poker hand history in the following format:

        ```
        PokerStars Hand #[Hand ID]: Tournament #[Tournament ID], [Tournament Name] - [Blind Levels] - [Date & Time]
        Table '[Table Name]' [Max Players]-max Seat #[Button Seat] is the button

        Seat 1: [Player1] ([Chip Stack]) 
        Seat 2: [Player2] ([Chip Stack]) 
        ...
        Seat N: [PlayerN] ([Chip Stack])

        [Player Actions: Posting Blinds & Antes]

        *** HOLE CARDS ***
        Dealt to [Hero] [Hole Cards]

        [Pre-Flop Actions]

        *** FLOP *** [Flop Cards]
        [Flop Actions]

        *** TURN *** [Flop Cards] [Turn Card]
        [Turn Actions]

        *** RIVER *** [Flop Cards] [Turn Card] [River Card]
        [River Actions]

        *** SHOW DOWN ***
        [Showdown Details]

        [Winner Announcement]

        *** SUMMARY ***
        Total pot [Pot Amount] | Rake [Rake Amount]
        Board [Board Cards]
        [Seat-wise Results]
        ```

        Processing Logic:
            1. Extract Tournament Details: Retrieve tournament name, blind levels, and timestamp.
            2. Reconstruct Player Seating: Arrange players in the correct order with chip stacks.
            3. Combine Actions Across Images: Merge all betting actions in the correct sequence.
            4. Identify Community Cards: Ensure the flop, turn, and river are correctly assigned.
            5. Determine the Winner: Identify the final showdown results.
            6. Format the Summary Section: List pot details, board cards, and final player results.

        Here is the JSON data from the analyzed images:
        """
        
        # Add the image data as JSON
        prompt += "\n" + json.dumps(image_data, indent=2)
        
        return prompt

    def generate_hand_history(self, image_data: List[Dict[str, Any]]) -> str:
        """Generate PokerStars format hand history using LLM."""
        
        # Generate the prompt for the LLM
        prompt = self._generate_hand_history_prompt(image_data)
        
        try:
            # Call OpenAI API to generate the hand history
            response = self.client.chat.completions.create(
                model="gpt-4",  # Using GPT-4 for better structured output
                messages=[
                    {"role": "system", "content": "You are a poker hand history generator that creates detailed, accurate hand histories in PokerStars format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Lower temperature for more consistent output
                max_tokens=2000
            )
            
            # Extract the hand history from the response
            hand_history = response.choices[0].message.content
            
            # Clean up the response - remove any markdown code blocks if present
            hand_history = re.sub(r'```[^\n]*\n', '', hand_history)
            hand_history = hand_history.replace('```', '')
            hand_history = hand_history.strip()
            
            return hand_history
            
        except Exception as e:
            error_msg = f"Error generating hand history: {str(e)}"
            logging.error(error_msg)
            raise Exception(error_msg)



    def process_directory(self, directory: str) -> str:
        """Process all images in a directory and generate complete hand history."""
        try:
            image_files = self._get_sorted_images(directory)
            image_data = []
            
            logging.info(f"Processing directory: {directory}")
            logging.info(f"Found {len(image_files)} images to process")
            
            for image_file in image_files:
                image_path = os.path.join(directory, image_file)
                logging.info(f"Processing image: {image_file}")
                analysis = self.analyze_image(image_path)
                
                if 'error' in analysis:
                    logging.error(f"Error in analysis for {image_file}: {analysis['error']}")
                    continue
                    
                image_data.append(analysis)
            
            if not image_data:
                raise Exception("No valid image analysis data available")
                
            return self.generate_hand_history(image_data)
            
        except Exception as e:
            error_msg = f"Error processing directory {directory}: {str(e)}"
            logging.error(error_msg)
            raise Exception(error_msg)

def main():
    """Main function to demonstrate usage."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return
    
    generator = PokerHandHistoryGenerator(api_key)
    
    # Example usage
    directory = "screenshots/game2"  # Directory containing poker screenshots
    hand_history = generator.process_directory(directory)
    
    # Save the hand history to a file
    output_file = "hand_history.txt"
    with open(output_file, "w") as f:
        f.write(hand_history)
    
    print(f"Hand history has been generated and saved to {output_file}")

if __name__ == "__main__":
    main()
