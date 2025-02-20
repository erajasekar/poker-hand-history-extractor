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
        
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze a single poker game image using OpenAI Vision."""
        prompt = """
        Objective:

        Extract poker game details and hand history from the provided image and structure the output in JSON format that strictly adheres to the given JSON schema.

        Guidelines:
            1. Data Extraction & Formatting:
            • Identify all relevant poker game details from the image, including player names, bets, community cards, and actions.
            • Structure the extracted data into the required JSON fields.
            • Ensure all extracted text is clean and free of OCR artifacts.
            2. Handling Missing or Unavailable Data:
            • If a required field is missing in the image, assign:
            • "missing" for string fields.
            • 0 for numeric fields.
            • false for boolean fields.
            • [] for empty lists.
            • Auto-generate unique IDs for player_id, game_number, and other identifier fields based on the expected data type.
            3. Data Validation:
            • Ensure the final JSON output strictly conforms to the given schema.
            • Verify all required fields are populated.
            • Validate JSON structure to avoid schema mismatches.

        Step-by-Step Extraction Guide:

        1. Extract General Game Information
            • spec_version: Assign a default version (e.g., "1.0").
            • site_name: Extract poker platform/site name.
            • network_name: Extract poker network (if present).
            • internal_version: Extract or assign "missing".
            • tournament: Determine whether it is a tournament (true/false).
            • tournament_info: If applicable, extract tournament details.
            • game_number: Auto-generate if not visible.
            • start_date_utc: Extract timestamp or assign "missing".
            • table_name and table_handle: Extract if available.
            • table_skin: Extract or set "missing".
            • game_type: Identify from the game (e.g., "Texas Hold'em").
            • bet_limit: Extract bet type (e.g., "No Limit", "Pot Limit") and set "bet_cap" to 0 if unknown.
            • table_size: Count number of seats at the table.
            • currency: Extract (e.g., "USD", "missing" if not available).
            • dealer_seat: Identify dealer position.
            • small_blind_amount and big_blind_amount: Extract from game info.
            • ante_amount: Extract or set 0 if not applicable.
            • hero_player_id: Identify the "Hero" player (if applicable).

        2. Extract Player Information
            • Identify all players in the game.
            • For each player, extract:
            • id: Assign an auto-generated unique integer.
            • seat: Identify from the image.
            • name and display: Extract player name.
            • starting_stack: Extract or assign 0 if missing.
            • player_bounty: Extract for tournaments or assign 0.
            • is_sitting_out: Determine if the player is inactive (true/false).

        3. Extract Hand Rounds and Actions
            • Identify each game round (Pre-Flop, Flop, Turn, River).
            • Extract community cards for each round.
            • Capture player actions per round, including:
            • player_id: Find player_id from Player Information by matching the player name.
            • action_type: Extract ("fold", "call", "raise", "check", "bet", "all-in").
            • amount: Extract the bet amount.
            • is_all_in: Determine if the player went all-in (true/false).

        4. Extract Pot and Winnings
            • Identify the total pot size and breakdown.
            • Extract winners and their earnings.
            • Capture their final hands, including:
            • player_id
            • amount
            • hand: List of final hole cards.
            • hand_name: Extract the name of the winning hand (e.g., "Flush").

        5. Extract Tournament-Specific Details (If Applicable)
            • If a tournament, capture:
            • Buy-in, entry fee, bounty.
            • Tournament start time, structure details.
            • Remaining players, prize pool, and payout information.

        The output should be a valid JSON object with an "ohh" root property containing all the extracted information.
        """
        
        try:
            logging.info(f"Analyzing image: {image_path}")
            
            with open(image_path, "rb") as image_file:
                # Define the JSON schema
                json_schema = {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "ohh": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "spec_version": {"type": "string"},
                                "site_name": {"type": "string"},
                                "network_name": {"type": ["string", "null"]},
                                "internal_version": {"type": ["string", "null"]},
                                "tournament": {"type": ["boolean", "null"]},
                                "tournament_info": {
                                    "type": ["object", "null"],
                                    "additionalProperties": False,
                                    "properties": {
                                        "id": {"type": "string"},
                                        "buyin": {"type": "number"},
                                        "entry_fee": {"type": "number"},
                                        "bounty": {"type": "number"},
                                        "speed": {
                                            "type": "object",
                                            "additionalProperties": False,
                                            "properties": {
                                                "type": {"type": "string"},
                                                "duration": {"type": ["integer", "null"]}
                                            },
                                            "required": ["type", "duration"]
                                        },
                                        "start_time": {"type": "string"},
                                        "table_size": {"type": "integer"},
                                        "starting_stack": {"type": "number"},
                                        "current_level": {"type": "integer"},
                                        "level_duration": {"type": "integer"},
                                        "late_reg_duration": {"type": "integer"},
                                        "rebuy_duration": {"type": "integer"},
                                        "addon_duration": {"type": "integer"},
                                        "players_remaining": {"type": "integer"},
                                        "prize_pool": {"type": "number"},
                                        "in_the_money": {"type": "boolean"}
                                    },
                                    "required": [
                                        "id", "buyin", "entry_fee", "bounty", "speed",
                                        "start_time", "table_size", "starting_stack",
                                        "current_level", "level_duration", "late_reg_duration",
                                        "rebuy_duration", "addon_duration", "players_remaining",
                                        "prize_pool", "in_the_money"
                                    ]
                                },
                                "game_number": {"type": "string"},
                                "start_date_utc": {"type": "string"},
                                "table_name": {"type": ["string", "null"]},
                                "table_handle": {"type": ["string", "null"]},
                                "table_skin": {"type": ["string", "null"]},
                                "game_type": {"type": "string"},
                                "bet_limit": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "bet_type": {"type": "string"},
                                        "bet_cap": {"type": ["number", "null"]}
                                    },
                                    "required": ["bet_type", "bet_cap"]
                                },
                                "table_size": {"type": "integer"},
                                "currency": {"type": "string"},
                                "dealer_seat": {"type": "integer"},
                                "small_blind_amount": {"type": "number"},
                                "big_blind_amount": {"type": "number"},
                                "ante_amount": {"type": ["number", "null"]},
                                "hero_player_id": {"type": ["integer", "null"]},
                                "flags": {
                                    "type": ["array", "null"],
                                    "items": {"type": "string"}
                                },
                                "players": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "additionalProperties": False,
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "seat": {"type": "integer"},
                                            "name": {"type": "string"},
                                            "display": {"type": ["string", "null"]},
                                            "starting_stack": {"type": "number"},
                                            "player_bounty": {"type": ["number", "null"]},
                                            "is_sitting_out": {"type": ["boolean", "null"]}
                                        },
                                        "required": ["id", "seat", "name", "display", "starting_stack", "player_bounty", "is_sitting_out"]
                                    }
                                },
                                "rounds": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "additionalProperties": False,
                                        "properties": {
                                            "name": {"type": ["string", "null"]},
                                            "street_cards": {
                                                "type": ["array", "null"],
                                                "items": {"type": "string"}
                                            },
                                            "actions": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "additionalProperties": False,
                                                    "properties": {
                                                        "player_id": {"type": "integer"},
                                                        "action_type": {"type": ["string", "null"]},
                                                        "amount": {"type": ["number", "null"]},
                                                        "is_all_in": {"type": ["boolean", "null"]}
                                                    },
                                                    "required": ["player_id", "action_type", "amount", "is_all_in"]
                                                }
                                            }
                                        },
                                        "required": ["name", "street_cards", "actions"]
                                    }
                                },
                                "pots": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "additionalProperties": False,
                                        "properties": {
                                            "type": {"type": ["string", "null"]},
                                            "amount": {"type": "number"},
                                            "rake": {"type": ["number", "null"]},
                                            "player_wins": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "additionalProperties": False,
                                                    "properties": {
                                                        "player_id": {"type": "integer"},
                                                        "amount": {"type": ["number", "null"]},
                                                        "hand": {
                                                            "type": ["array", "null"],
                                                            "items": {"type": "string"}
                                                        },
                                                        "hand_name": {"type": ["string", "null"]}
                                                    },
                                                    "required": ["player_id", "amount", "hand", "hand_name"]
                                                }
                                            }
                                        },
                                        "required": ["type", "amount", "rake", "player_wins"]
                                    }
                                },
                                "tournament_bounties": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "additionalProperties": False,
                                        "properties": {
                                            "player_id": {"type": "integer"},
                                            "amount": {"type": "number"}
                                        },
                                        "required": ["player_id", "amount"]
                                    }
                                }
                            },
                            "required": [
                                "spec_version", "site_name", "network_name", "internal_version",
                                "tournament", "tournament_info", "game_number", "start_date_utc",
                                "table_name", "table_handle", "table_skin", "game_type",
                                "bet_limit", "table_size", "currency", "dealer_seat",
                                "small_blind_amount", "big_blind_amount", "ante_amount",
                                "hero_player_id", "flags", "players", "rounds", "pots",
                                "tournament_bounties"
                            ]
                        }
                    },
                    "required": ["ohh"]
                }

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
                    max_tokens=4000,
                    temperature=0,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "Poker_Open_Hand_Schema",
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
        """Generate hand history from analyzed image data."""
        raise NotImplementedError("Hand history generation not implemented yet")



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
                
            #return self.generate_hand_history(image_data)
            return json.dumps(image_data, indent=2)
            
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
    process_count = 1  # Change this value to process multiple times
    
    for i in range(process_count):
        print(f"\nProcessing iteration {i+1} of {process_count}")
        generator = PokerHandHistoryGenerator(api_key)
        
        # Example usage
        directory = "screenshots/game2"  # Directory containing poker screenshots
        hand_history = generator.process_directory(directory)
        
        # Save the hand history to a file with timestamp
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"hand_history_{current_time}.txt"
        with open(output_file, "w") as f:
            f.write(hand_history)
        
        print(f"Hand history has been generated and saved to {output_file}")

if __name__ == "__main__":
    main()
