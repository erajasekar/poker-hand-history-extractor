import os
import json
import re
import base64
import logging
from typing import List, Dict, Any
from openai import OpenAI
from datetime import datetime
from pathlib import Path
from CraftyWheelPokerHandHistory import CraftyWheelPokerHandHistory;

class PokerHandHistoryGenerator:
    def __init__(self, api_key: str, output_dir: str , log_dir: str = "logs"):
        self.client = OpenAI(api_key=api_key)
        self.output_dir = output_dir
        self.log_dir = log_dir
        
        # Create output and logs directories if they don't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Set up logging with timestamp in filename
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f'poker_analysis_{current_time}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, log_filename)),
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
        
    def analyze_image(self, image_path: str, export_markdown: bool = False) -> Dict[str, Any]:
        """Analyze a single poker game image using OpenAI Vision."""
        prompt = """
        Extract the following poker game details from the provided image and output the information in a structured JSON format.

        1. TOURNAMENT INFORMATION
        - Look at the top of the screen for tournament name, event name, and stage
        - Check bottom of screen for blind levels (shown as "BLINDS X/Y/Z")

        2. PLAYER INFORMATION
        For each player visible:
        - Extract name and nationality (shown by country flag)
        - Note current stack size (shown in millions, e.g., "194 M")
        - Record hole cards when visible
        - Format cards as: [rank][suite] where:
          * rank is 2-9, T, J, Q, K, or A
          * suite is 's' for spades, 'h' for hearts, 'd' for diamonds, 'c' for clubs
          Example: "Kc" for King of clubs, "Th" for Ten of hearts

        3. ACTIONS
        For each street (preflop, flop, turn, river):
        - Watch for action indicators:
          * "Check" text
          * "Call" with amount
          * "Bet" with amount
          * "Raise" with amount
        - Record amounts when shown (in millions)

        4. BOARD CARDS
        - Record community cards as they appear
        - Use same card formatting as hole cards
        - Group by street: flop (3 cards), turn (1 card), river (1 card)

        5. POT SIZE
        - Look for total pot amount shown on screen

        6. WINNER IDENTIFICATION
        Look for visual cues:
        - Green checkmark (✓) under player name
        - Plus sign (+) with amount
        - Stack size increasing
        - Any highlighting or emphasis on a player
        The player with these indicators should have:
          * isWinner: true
          * amountWon: [amount shown with + sign]
        Other players should have:
          * isWinner: false
          * amountWon: 0

        OUTPUT FORMAT:
        Generate JSON confirming to provide json schema

        IMPORTANT NOTES:
        - Convert all monetary values to actual numbers (multiply M by 1,000,000)
        - Record all actions in chronological order
        - Include amount field only for bet/raise/call actions
        - Ensure card notation is consistent (Kc, Th, etc.)
        - Watch for hand progression through multiple screenshots
        - Always check winner indicators carefully

        Example card translations:
        K♣ → "Kc"
        T♥ → "Th"
        A♦ → "Ad"
        2♠ → "2s"
        """
        
        try:
            logging.info(f"Analyzing image: {image_path}")
            
            with open(image_path, "rb") as image_file:
                # Define the JSON schema
                json_schema = {
                  "$schema": "http://json-schema.org/draft-07/schema#",
                  "title": "Poker Hand History",
                  "type": "object",
                  "definitions": {
                    "actionArray": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                          "type": {
                            "type": "string",
                            "enum": ["fold", "check", "call", "bet", "raise"]
                          },
                          "amount": { "type": "number" }
                        },
                        "required": ["type", "amount"]
                      }
                    }
                  },
                  "additionalProperties": False,
                  "properties": {
                    "gameInfo": {
                      "type": "object",
                      "additionalProperties": False,
                      "properties": {
                        "tournamentName": { "type": "string" },
                        "eventName": { "type": "string" },
                        "stage": { "type": "string" },
                        "blinds": {
                          "type": "object",
                          "additionalProperties": False,
                          "properties": {
                            "smallBlind": { "type": "number" },
                            "bigBlind": { "type": "number" }
                          },
                          "required": ["smallBlind", "bigBlind"]
                        }
                      },
                      "required": ["tournamentName", "eventName", "stage", "blinds"]
                    },
                    "players": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                          "name": { "type": "string" },
                          "nationality": { "type": "string" },
                          "stack": { "type": "number" },
                          "cards": {
                            "type": "array",
                            "items": { "type": "string" }
                          },
                          "actions": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                              "preflop": { "$ref": "#/definitions/actionArray" },
                              "flop": { "$ref": "#/definitions/actionArray" },
                              "turn": { "$ref": "#/definitions/actionArray" },
                              "river": { "$ref": "#/definitions/actionArray" }
                            },
                            "required": ["preflop", "flop", "turn", "river"]
                          },
                          "isWinner": { "type": "boolean" },
                          "amountWon": { "type": "number" }
                        },
                        "required": ["name", "nationality", "stack", "cards", "actions", "isWinner", "amountWon"]
                      }
                    },
                    "board": {
                      "type": "object",
                      "additionalProperties": False,
                      "properties": {
                        "flop": {
                          "type": "array",
                          "items": { "type": "string" }
                        },
                        "turn": { "type": "string" },
                        "river": { "type": "string" }
                      },
                      "required": ["flop", "turn", "river"]
                    },
                    "pot": { "type": "number" }
                  },
                  "required": ["gameInfo", "players", "board", "pot"]
                }

                response = self.client.beta.chat.completions.parse(
                    model="gpt-4o",
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
                    max_tokens=4000,
                    temperature=0,
                    response_format=CraftyWheelPokerHandHistory
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
                
                # Save analysis output to a JSON file with timestamp
                current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                analysis_filename = f"{base_name}_analysis_{current_time}.json"
                analysis_path = os.path.join(self.output_dir, analysis_filename)
                with open(analysis_path, 'w') as f:
                    json.dump(result, f, indent=2)
                logging.info(f"Saved analysis to: {analysis_path}")
                
                # If markdown export is enabled, append to markdown file
                if export_markdown:
                    # Get parent directory name for markdown file name
                    parent_dir = os.path.basename(os.path.dirname(image_path))
                    markdown_path = os.path.join(self.output_dir, f"{parent_dir}.md")
                    
                    # Extract image filename from path
                    image_filename = os.path.basename(image_path)
                    
                    # Append image and analysis to markdown file
                    with open(markdown_path, 'a') as f:
                        f.write(f"\n![{parent_dir}]({image_filename})\n\n")
                        f.write("```json\n")
                        json.dump(result, f, indent=2)
                        f.write("\n```\n")

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

        Card Suite Format:
        Use the following single character representations for card suites:
        - Hearts: h (e.g., "Ah" for Ace of Hearts)
        - Clubs: c (e.g., "Kc" for King of Clubs)
        - Diamonds: d (e.g., "Qd" for Queen of Diamonds)
        - Spades: s (e.g., "Js" for Jack of Spades)

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
                temperature=0,  # Lower temperature for more consistent output
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


    def process_directory(self, directory: str, export_markdown: bool = False) -> str:
        """Process all images in a directory and generate complete hand history."""
        try:
            image_files = self._get_sorted_images(directory)
            image_data = []
            
            logging.info(f"Processing directory: {directory}")
            logging.info(f"Found {len(image_files)} images to process")
            
            for image_file in image_files:
                image_path = os.path.join(directory, image_file)
                logging.info(f"Processing image: {image_file}")
                analysis = self.analyze_image(image_path, export_markdown)
                
                if 'error' in analysis:
                    logging.error(f"Error in analysis for {image_file}: {analysis['error']}")
                    continue
                    
                image_data.append(analysis)
            
            if not image_data:
                raise Exception("No valid image analysis data available")
                
            #hand_history = self.generate_hand_history(image_data)
            hand_history = json.dumps(image_data, indent=4)
            
            # If markdown export is enabled, append hand history to markdown file
            if export_markdown:
                parent_dir = os.path.basename(directory)
                markdown_path = os.path.join(self.output_dir, f"{parent_dir}.md")
                with open(markdown_path, 'a') as f:
                    f.write("\n## Hand History\n\n")
                    f.write("```\n")
                    f.write(hand_history)
                    f.write("\n```\n")
            
            return hand_history
            
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
    
    # Number of times to process the directory
    process_count = 1 # Change this value to process multiple times
    
    # Default output directory
    #output_dir = "export/obsidian/2024_wsop_game2"
    output_dir = "logs"
    export_markdown = False
    
    for i in range(process_count):
        print(f"\nProcessing iteration {i+1} of {process_count}")
        generator = PokerHandHistoryGenerator(api_key, output_dir=output_dir)
        
        # Example usage
        directory = "screenshots/game21"  # Directory containing poker screenshots
        # Enable markdown export
        hand_history = generator.process_directory(directory, export_markdown)
        
        # Save the hand history to a file with timestamp in output directory
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"hand_history_{current_time}.txt")
        with open(output_file, "w") as f:
            f.write(hand_history)
        
        print(f"Hand history has been generated and saved to {output_file}")

if __name__ == "__main__":
    main()
