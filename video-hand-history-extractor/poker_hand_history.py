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

        Fields to Extract:
        1. Tournament Details:
           • tournament_name: Name of the tournament.
           • blind_levels: Current blinds (small blind, big blind) with full amounts (e.g., "$1,000" not "$1K").
        2. Player Information:
           • players: List of players with their chip stacks.
             - Use Title Case for player names (e.g., "Phil Ivey" not "phil ivey")
             - Write chip stacks in full with commas (e.g., "$1,000,000" not "$1M")
           • button_seat: Seat number of the dealer button.
        3. Pre-Flop Action:
           • pre_flop: List of actions with player name (in Title Case), action type, and full amount.
             Example: {"player_name": "Daniel Negreanu", "action_type": "raises", "amount": "$25,000"}
        4. Post-Flop Actions:
           • flop_cards: Three community cards.
           • flop_action: List of actions with player name (in Title Case) and full amounts.
        5. Turn Actions:
           • turn_card: Fourth community card.
           • turn_action: List of actions with player name (in Title Case) and full amounts.
        6. River Actions:
           • river_card: Fifth community card.
           • river_action: List of actions with player name (in Title Case) and full amounts.
        7. Showdown:
           • showdown: Players (in Title Case) who revealed their hands and the winner.
        8. Summary:
           • summary: Final pot size (in full amount with commas) and board cards.
        
        Formatting Rules:
        • Always use Title Case for player names (e.g., "Tom Dwan" not "tom dwan")
        • Write all amounts in full with commas (e.g., "$1,000,000" not "$1M" or "$1000000")
        • Include dollar signs for all amounts
        • For card suites, use the following single character representations:
          - Hearts: h (e.g., "Ah" for Ace of Hearts)
          - Clubs: c (e.g., "Kc" for King of Clubs)
          - Diamonds: d (e.g., "Qd" for Queen of Diamonds)
          - Spades: s (e.g., "Js" for Jack of Spades)
        
        Note: If any information is unclear in the image, include a "missing_details" field with an explanation.
        """
        
        try:
            logging.info(f"Analyzing image: {image_path}")
            
            with open(image_path, "rb") as image_file:
                # Define the JSON schema
                json_schema = {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                      "tournament_details": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                          "tournament_name": { "type": "string" },
                          "blind_levels": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                              "small_blind": { "type": "string" },
                              "big_blind": { "type": "string" }
                            },
                            "required": ["small_blind", "big_blind"]
                          }
                        },
                        "required": ["tournament_name", "blind_levels"]
                      },
                      "player_information": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                          "players": {
                            "type": "array",
                            "items": {
                              "type": "object",
                              "additionalProperties": False,
                              "properties": {
                                "name": { "type": "string" },
                                "chip_stack": { "type": "string" }
                              },
                              "required": ["name", "chip_stack"]
                            }
                          },
                          "button_seat": { "anyOf": [{ "type": "string" }, { "type": "null" }] }
                        },
                        "required": ["players", "button_seat"]
                      },
                      "pre_flop": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "additionalProperties": False,
                          "properties": {
                            "player_name": { "type": "string" },
                            "action_type": { "type": "string" },
                            "amount": { "anyOf": [{ "type": "string" }, { "type": "null" }] }
                          },
                          "required": ["player_name", "action_type", "amount"]
                        }
                      },
                      "post_flop": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                          "flop_cards": { "anyOf": [{ "type": "array", "items": { "type": "string" } }, { "type": "string" }, { "type": "null" }] },
                          "flop_action": { 
                            "type": "array",
                            "items": {
                              "type": "object",
                              "additionalProperties": False,
                              "properties": {
                                "player_name": { "type": "string" },
                                "action_type": { "type": "string" },
                                "amount": { "anyOf": [{ "type": "string" }, { "type": "null" }] }
                              },
                              "required": ["player_name", "action_type", "amount"]
                            }
                          }
                        },
                        "required": ["flop_cards", "flop_action"]
                      },
                      "turn_actions": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                          "turn_card": { "anyOf": [{ "type": "string" }, { "type": "null" }] },
                          "turn_action": {
                            "type": "array",
                            "items": {
                              "type": "object",
                              "additionalProperties": False,
                              "properties": {
                                "player_name": { "type": "string" },
                                "action_type": { "type": "string" },
                                "amount": { "anyOf": [{ "type": "string" }, { "type": "null" }] }
                              },
                              "required": ["player_name", "action_type", "amount"]
                            }
                          }
                        },
                        "required": ["turn_card", "turn_action"]
                      },
                      "river_actions": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                          "river_card": { "anyOf": [{ "type": "string" }, { "type": "null" }] },
                          "river_action": {
                            "type": "array",
                            "items": {
                              "type": "object",
                              "additionalProperties": False,
                              "properties": {
                                "player_name": { "type": "string" },
                                "action_type": { "type": "string" },
                                "amount": { "anyOf": [{ "type": "string" }, { "type": "null" }] }
                              },
                              "required": ["player_name", "action_type", "amount"]
                            }
                          }
                        },
                        "required": ["river_card", "river_action"]
                      },
                      "showdown": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                          "players": {
                            "type": "array",
                            "items": {
                              "type": "object",
                              "additionalProperties": False,
                              "properties": {
                                "name": { "type": "string" },
                                "hand": { "type": "string" }
                              },
                              "required": ["name", "hand"]
                            }
                          },
                          "winner": { "anyOf": [{ "type": "string" }, { "type": "null" }] }
                        },
                        "required": ["players", "winner"]
                      },
                      "summary": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                          "summary": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                              "final_pot_size": { "type": "string" },
                              "board_cards": { "anyOf": [{ "type": "array", "items": { "type": "string" } }, { "type": "string" }, { "type": "null" }] }
                            },
                            "required": ["final_pot_size", "board_cards"]
                          }
                        },
                        "required": ["summary"]
                      },
                      "missing_details": { "type": "string" }
                    },
                    "required": ["tournament_details", "player_information", "pre_flop", "post_flop", "turn_actions", "river_actions", "showdown", "summary", "missing_details"]
                  }

                response = self.client.chat.completions.create(
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
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "Crafty_Wheel_Hand_Schema",
                            "strict": True,
                            "schema": json_schema
                        }
                    }
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
                
            hand_history = self.generate_hand_history(image_data)
            
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
    output_dir = "export/obsidian/2024_wsop_game3"
    export_markdown = True
    
    for i in range(process_count):
        print(f"\nProcessing iteration {i+1} of {process_count}")
        generator = PokerHandHistoryGenerator(api_key, output_dir=output_dir)
        
        # Example usage
        directory = "screenshots/game3"  # Directory containing poker screenshots
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
