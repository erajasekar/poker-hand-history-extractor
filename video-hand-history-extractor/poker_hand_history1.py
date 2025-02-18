import os
import json
import re
import base64
import logging
from typing import List, Dict, Any, Union
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

    def _format_cards(self, cards: Union[List[str], None]) -> str:
        """Format a list of cards or return a placeholder if None."""
        if not cards:
            return "[?? ?? ??]"
        return f"[{' '.join(cards)}]"

    def generate_hand_history(self, image_data: List[Dict[str, Any]]) -> str:
        """Generate PokerStars format hand history from analyzed image data."""
        # Combine data from all images
        combined_data = self._combine_hand_data(image_data)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S ET")
        
        # Format hand history
        history = []
        
        # Header
        history.append(
            f"PokerStars Hand #{combined_data.get('hand_id', '123456789')}: "
            f"Tournament #{combined_data.get('tournament_id', '1234567')}, "
            f"{combined_data.get('tournament_name', 'Tournament')} - "
            f"Level {combined_data.get('blind_levels', '???/???')} - {timestamp}"
        )
        
        # Table info
        history.append(
            f"Table '{combined_data.get('table_name', 'Table 1')}' "
            f"9-max Seat #{combined_data.get('button_seat', 1)} is the button"
        )
        
        # Player seating
        for player in combined_data.get('players', []):
            history.append(
                f"Seat {player['seat']}: {player['name']} ({player['chips']} in chips)"
            )
        
        history.append("")  # Empty line
        
        # Blinds
        # Add blind postings based on button position
        
        # Hole cards
        history.append("*** HOLE CARDS ***")
        if 'hero_cards' in combined_data:
            history.append(f"Dealt to Hero {combined_data['hero_cards']}")
        
        # Pre-flop actions
        for action in combined_data.get('pre_flop', []):
            history.append(self._format_action(action))
        
        # Flop
        if 'flop_cards' in combined_data:
            history.append(f"\n*** FLOP *** {self._format_cards(combined_data['flop_cards'])}")
            for action in combined_data.get('flop_action', []):
                history.append(self._format_action(action))
        
        # Turn
        if 'turn_card' in combined_data:
            history.append(
                f"\n*** TURN *** {self._format_cards(combined_data['flop_cards'])} "
                f"[{combined_data.get('turn_card', '??')}]"
            )
            for action in combined_data.get('turn_action', []):
                history.append(self._format_action(action))
        
        # River
        if 'river_card' in combined_data:
            history.append(
                f"\n*** RIVER *** {self._format_cards(combined_data['flop_cards'])} "
                f"[{combined_data.get('turn_card', '??')}] [{combined_data.get('river_card', '??')}]"
            )
            for action in combined_data.get('river_action', []):
                history.append(self._format_action(action))
        
        # Showdown
        if 'showdown' in combined_data:
            history.append("\n*** SHOW DOWN ***")
            showdown = combined_data['showdown']
            if isinstance(showdown, dict):
                # Handle nested showdown structure
                if 'showdown' in showdown and isinstance(showdown['showdown'], dict):
                    showdown = showdown['showdown']
                
                if 'revealed_hands' in showdown:
                    for hand in showdown['revealed_hands']:
                        if isinstance(hand, dict):
                            player = hand.get('player_name', 'Unknown')
                            cards = hand.get('cards', ['??', '??'])
                            result = 'winner' if player == showdown.get('winner') else ''
                            history.append(f"{player}: shows {self._format_cards(cards)} {result}")
        
        # Summary
        history.append("\n*** SUMMARY ***")
        if 'summary' in combined_data:
            summary = combined_data['summary']
            history.append(f"Total pot {summary.get('total_pot', 0)} | Rake {summary.get('rake', 0)}")
            
            # Format board cards
            board_cards = summary.get('board_cards') or summary.get('board')
            if board_cards:
                history.append(f"Board {self._format_cards(board_cards)}")
            else:
                history.append("Board [?? ?? ??]")
            
            # Generate seat results from players and showdown info
            if 'players' in combined_data and 'showdown' in combined_data:
                showdown = combined_data['showdown']
                if isinstance(showdown, dict):
                    # Handle nested showdown structure
                    if 'showdown' in showdown and isinstance(showdown['showdown'], dict):
                        showdown = showdown['showdown']
                    
                    for player in combined_data['players']:
                        seat = player.get('seat', 0)
                        name = player.get('name', 'Unknown')
                        
                        # Check if player showed cards in showdown
                        if 'revealed_hands' in showdown:
                            # Case-insensitive player name matching
                            player_name_upper = name.upper()
                            revealed = next(
                                (hand for hand in showdown['revealed_hands'] 
                                 if hand.get('player_name', '').upper() == player_name_upper),
                                None
                            )
                            if revealed:
                                result = 'win' if name == showdown.get('winner') else 'lose'
                                history.append(
                                    f"Seat {seat}: {name} showed {self._format_cards(revealed.get('cards'))} "
                                    f"and {result}"
                                )
                                continue
                        
                        # If player didn't show cards, mark as folded
                        history.append(f"Seat {seat}: {name} folded")
        
        return "\n".join(history)

    def _combine_hand_data(self, image_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine data from multiple images into a single hand history."""
        combined = {
            'players': [],
            'pre_flop': [],
            'flop_action': [],
            'turn_action': [],
            'river_action': [],
            'showdown': []
        }
        
        for data in image_data:
            # Update tournament info if not set
            if 'tournament_details' in data:
                if 'tournament_name' not in combined:
                    combined['tournament_name'] = data['tournament_details'].get('tournament_name')
                if 'blind_levels' not in combined:
                    blind_levels = data['tournament_details'].get('blind_levels', {})
                    combined['blind_levels'] = f"{blind_levels.get('small_blind', '???')}/{blind_levels.get('big_blind', '???')}"
            
            # Update button seat
            if 'player_information' in data:
                if 'button_seat' not in combined:
                    button_seat = data['player_information'].get('button_seat')
                    # If button_seat is a player name or 'D', find their seat number
                    if isinstance(button_seat, str):
                        if button_seat.upper() == 'D':
                            # Default to seat 1 for dealer
                            combined['button_seat'] = 1
                        else:
                            players = data['player_information'].get('players', [])
                            # Normalize player names to uppercase for comparison
                            button_name = button_seat.upper()
                            for idx, player in enumerate(players):
                                if player.get('name', '').upper() == button_name:
                                    combined['button_seat'] = idx + 1
                                    break
                            else:
                                combined['button_seat'] = 1
                    else:
                        combined['button_seat'] = button_seat if button_seat else 1
            
            # Update players if empty
            if not combined['players'] and 'player_information' in data:
                players = data['player_information'].get('players', [])
                combined['players'] = [
                    {
                        'seat': idx + 1,  # Assign seats sequentially if not provided
                        'name': player.get('name', f'Player{idx+1}'),
                        'chips': player.get('chip_stack', 0)
                    }
                    for idx, player in enumerate(players)
                ]
            
            # Append actions in sequence
            if 'pre_flop' in data:
                actions = []
                for action in data['pre_flop']:
                    if isinstance(action, dict):
                        actions.append({
                            'player': action.get('player_name', action.get('player', 'Unknown')),
                            'action': action.get('action_type', action.get('action', 'unknown')),
                            'amount': action.get('amount', 0)
                        })
                combined['pre_flop'].extend(actions)
            
            # Handle post-flop actions
            if 'post_flop' in data:
                post_flop = data['post_flop']
                if isinstance(post_flop, dict):
                    if 'flop_cards' in post_flop and 'flop_cards' not in combined:
                        combined['flop_cards'] = post_flop['flop_cards']
                    if 'flop_action' in post_flop:
                        actions = []
                        for action in post_flop['flop_action']:
                            if isinstance(action, dict):
                                actions.append({
                                    'player': action.get('player_name', action.get('player', 'Unknown')),
                                    'action': action.get('action_type', action.get('action', 'unknown')),
                                    'amount': action.get('amount', 0)
                                })
                        combined['flop_action'].extend(actions)
            
            # Handle turn actions (support both 'turn' and 'turn_actions' keys)
            turn_data = data.get('turn_actions') or data.get('turn')
            if turn_data:
                turn = turn_data
                if isinstance(turn, dict):
                    if 'turn_card' in turn and turn['turn_card'] and 'turn_card' not in combined:
                        combined['turn_card'] = turn['turn_card']
                    if 'turn_action' in turn:
                        actions = []
                        for action in turn['turn_action']:
                            if isinstance(action, dict):
                                actions.append({
                                    'player': action.get('player_name', action.get('player', 'Unknown')),
                                    'action': action.get('action_type', action.get('action', 'unknown')),
                                    'amount': action.get('amount', 0)
                                })
                        combined['turn_action'].extend(actions)
            
            # Handle river actions (support both 'river' and 'river_actions' keys)
            river_data = data.get('river_actions') or data.get('river')
            if river_data:
                river = river_data
                if isinstance(river, dict):
                    if 'river_card' in river and river['river_card'] and 'river_card' not in combined:
                        combined['river_card'] = river['river_card']
                    if 'river_action' in river:
                        actions = []
                        for action in river['river_action']:
                            if isinstance(action, dict):
                                actions.append({
                                    'player': action.get('player_name', action.get('player', 'Unknown')),
                                    'action': action.get('action_type', action.get('action', 'unknown')),
                                    'amount': action.get('amount', 0)
                                })
                        combined['river_action'].extend(actions)
            
            # Handle showdown
            if 'showdown' in data:
                showdown_data = data['showdown']
                # Handle nested showdown structure
                if isinstance(showdown_data, dict):
                    if 'showdown' in showdown_data and isinstance(showdown_data['showdown'], dict):
                        showdown_data = showdown_data['showdown']
                    
                    # Convert players array to revealed_hands if needed
                    if 'players' in showdown_data and isinstance(showdown_data['players'], list):
                        showdown_data['revealed_hands'] = [
                            {
                                'player_name': player.get('name', 'Unknown'),
                                'cards': player.get('cards', ['??', '??']),
                                'result': 'win' if player.get('name') == showdown_data.get('winner') else 'lose'
                            }
                            for player in showdown_data['players']
                            if isinstance(player, dict)
                        ]
                
                combined['showdown'] = showdown_data
            
            # Handle summary (support nested summary structure)
            if 'summary' in data:
                summary_data = data['summary']
                # Handle nested summary
                if isinstance(summary_data, dict) and 'summary' in summary_data:
                    summary_data = summary_data['summary']
                
                if not combined.get('summary'):
                    combined['summary'] = {
                        'total_pot': summary_data.get('final_pot_size', 0),
                        'board': summary_data.get('board_cards', []),
                        'rake': 0,
                        'seat_results': []
                    }
        
        return combined

    def _normalize_amount(self, amount: Any) -> int:
        """Normalize different amount formats to integer."""
        if amount is None:
            return 0
        if isinstance(amount, (int, float)):
            return int(amount)
        if isinstance(amount, str):
            # Remove common formatting
            clean = amount.replace(',', '').replace('$', '').upper()
            # Handle 'M' suffix
            if clean.endswith('M'):
                return int(float(clean[:-1]) * 1000000)
            # Handle 'K' suffix
            if clean.endswith('K'):
                return int(float(clean[:-1]) * 1000)
            try:
                return int(float(clean))
            except (ValueError, TypeError):
                return 0
        return 0

    def _format_action(self, action: Dict[str, Any]) -> str:
        """Format a single poker action."""
        try:
            if not isinstance(action, dict):
                logging.warning(f"Invalid action format: {action}")
                return ""
            
            # Get action type from either 'action' or 'action_type' key
            action_type = action.get('action', action.get('action_type', '')).lower()
            # Get player name from either 'player' or 'player_name' key
            player = action.get('player', action.get('player_name', 'Unknown'))
            # Normalize amount
            amount = self._normalize_amount(action.get('amount', 0))
            
            if action_type in ['fold', 'folded']:
                return f"{player}: folds"
            elif action_type in ['check', 'checked']:
                return f"{player}: checks"
            elif action_type in ['call', 'called']:
                return f"{player}: calls {amount}"
            elif action_type in ['raise', 'raised']:
                return f"{player}: raises {amount}"
            elif action_type in ['all-in', 'all in', 'allin']:
                return f"{player}: raises {amount} and is all-in"
            elif action_type:
                return f"{player}: {action_type} {amount}".strip()
            else:
                logging.warning(f"Unknown action type in: {action}")
                return ""
                
        except Exception as e:
            logging.error(f"Error formatting action {action}: {str(e)}")
            return ""

    def _format_result(self, result: Dict[str, Any]) -> str:
        """Format a player's result for the summary section."""
        try:
            if not isinstance(result, dict):
                logging.warning(f"Invalid result format: {result}")
                return "folded"
                
            if 'hand' in result:
                action = 'showed' if result.get('result') == 'win' else 'showed'
                hand = result.get('hand', ['??', '??'])
                game_result = result.get('result', 'unknown')
                pot = result.get('pot', 0)
                return f"{action} {self._format_cards(hand)} and {game_result} ({pot})"
            return "folded"
            
        except Exception as e:
            logging.error(f"Error formatting result {result}: {str(e)}")
            return "folded"

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
