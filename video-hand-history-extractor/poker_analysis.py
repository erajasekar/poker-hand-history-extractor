import cv2
import numpy as np
import base64
import requests
import json
import os
from io import BytesIO
from PIL import Image
import time

class PokerGPT4Detector:
    def __init__(self, api_key):
        self.api_key = api_key
        self.previous_frame = None
        self.last_screenshot_time = 0
        self.min_screenshot_interval = 5
        self.api_endpoint = "https://api.openai.com/v1/chat/completions"  # GPT-4 Vision uses the chat completions endpoint
        
    def encode_image_to_base64(self, image_array):
        """Convert OpenCV image array to base64 string."""
        # Convert from BGR to RGB
        image_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        # Convert to PIL Image
        pil_image = Image.fromarray(image_rgb)
        # Save to BytesIO buffer
        buffer = BytesIO()
        pil_image.save(buffer, format="JPEG")
        # Get base64 string
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return image_base64

    def analyze_region_with_gpt4(self, frame, region, prompt):
        """Analyze a region of the frame using GPT-4 Vision."""
        x, y, w, h = region
        roi = frame[y:y+h, x:x+w]
        
        # Encode image
        base64_image = self.encode_image_to_base64(roi)
        
        # Prepare the API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "low"  # Use low detail to reduce tokens
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 100
        }
        
        try:
            response = requests.post(self.api_endpoint, headers=headers, json=payload)
            if response.status_code == 404:
                print("Error: API endpoint not found. Please check if you have access to GPT-4 Vision API.")
                return ""
            elif response.status_code == 401:
                print("Error: Invalid API key or unauthorized. Please check your OpenAI API key.")
                return ""
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            print(f"Error in GPT-4 Vision API call: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Response details: {e.response.text}")
            return ""
        except Exception as e:
            print(f"Unexpected error in GPT-4 Vision API call: {str(e)}")
            return ""

    def analyze_image_for_hand_history(self, image_path):
        """Analyze a poker image and return hand history information."""
        # Read the image
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"Error: Could not read image {image_path}")
            return None
            
        # Encode image
        base64_image = self.encode_image_to_base64(frame)
        
        # Prepare the API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        prompt = """
        You are a JSON generator. Analyze this poker game image and output ONLY a valid JSON object with no additional text or formatting. The JSON must follow this exact structure:

        {
            "table_name": "High Stakes Poker",
            "blinds": {"small": "$500", "big": "$1000"},
            "players": [
                {
                    "seat": "1",
                    "name": "Keating",
                    "stack": "$983000",
                    "position": "BTN",
                    "hole_cards": "As Ks"
                }
            ],
            "betting_round": "PREFLOP/FLOP/TURN/RIVER",
            "community_cards": {
                "flop": ["Ah", "7h", "5c"],
                "turn": "4s",
                "river": ""
            },
            "actions": [
                {"player": "Feldman", "action": "calls", "amount": "$1000"},
                {"player": "Keating", "action": "raises", "amount": "$3000"}
            ],
            "pot": "$269000"
        }

        Rules:
        - Include all visible information
        - For unknown values use empty strings ""
        - For unknown players use "Unknown" as name
        - Card notation: As = Ace of spades, Kh = King of hearts, etc.
        - Include $ in all amounts
        - Positions: BTN, SB, BB, UTG, etc.
        - Betting rounds: PREFLOP, FLOP, TURN, RIVER
        - Actions should be in chronological order

        Output only the JSON object, nothing else.
        """
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500
        }
        
        try:
            response = requests.post(self.api_endpoint, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Print raw response for debugging
            print(f"Raw GPT-4 response: {result['choices'][0]['message']['content']}")
            
            content = result['choices'][0]['message']['content'].strip()
            if not content:
                print("Error: Empty response from GPT-4")
                return {
                    "players": [],
                    "community_cards": "",
                    "action": "",
                    "pot": "",
                    "betting_round": ""
                }
            
            # Remove any markdown formatting if present
            content = content.replace("```json", "").replace("```", "").strip()
            
            try:
                # Try to parse the content as JSON
                parsed_data = json.loads(content)
                return parsed_data
            except json.JSONDecodeError as je:
                print(f"Error: Could not parse GPT-4 response as JSON")
                print(f"Raw response: {content}")
                # Return empty structure
                return {
                    "players": [],
                    "community_cards": "",
                    "action": "",
                    "pot": "",
                    "betting_round": ""
                }
        except Exception as e:
            print(f"Error analyzing image: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Response details: {e.response.text}")
            return None

    def convert_to_pokerstars_format(self, hand_data, hand_number):
        """Convert hand data to PokerStars hand history format."""
        if not hand_data:
            return ""
            
        # Format timestamp
        timestamp = time.strftime("%Y/%m/%d %H:%M:%S ET")
        
        # Start building the hand history
        history = []
        
        # Header with blinds
        blinds = hand_data.get('blinds', {'small': '', 'big': ''})
        history.append(f"PokerStars Hand #{hand_number:010d}: No Limit Hold'em ({blinds['small']}/{blinds['big']})")
        
        # Table information
        table_name = hand_data.get('table_name', 'Table 1')
        history.append(f"Table '{table_name}' 9-max Seat #1 is the button")
        
        # Player information
        for i in range(1, 10):  # 9 seats
            player_found = False
            for player in hand_data['players']:
                if player['seat'] == str(i):
                    history.append(f"Seat {i}: {player['name']} ({player['stack']} in chips)")
                    player_found = True
                    break
            if not player_found:
                history.append(f"Seat {i}: (Unknown)")
        
        # Hole cards section
        history.append("\n*** HOLE CARDS ***")
        for player in hand_data['players']:
            if player.get('hole_cards'):
                history.append(f"Dealt to {player['name']} [{player['hole_cards']}]")
        
        # Actions by betting round
        if hand_data.get('actions'):
            current_round = None
            for action in hand_data['actions']:
                if action.get('betting_round') != current_round:
                    current_round = action.get('betting_round')
                    if current_round == 'FLOP':
                        flop = hand_data['community_cards'].get('flop', [])
                        if flop:
                            history.append(f"\n*** FLOP *** [{' '.join(flop)}]")
                    elif current_round == 'TURN':
                        turn = hand_data['community_cards'].get('turn', '')
                        if turn:
                            history.append(f"\n*** TURN *** [{' '.join(hand_data['community_cards'].get('flop', []))}] [{turn}]")
                    elif current_round == 'RIVER':
                        river = hand_data['community_cards'].get('river', '')
                        if river:
                            history.append(f"\n*** RIVER *** [{' '.join(hand_data['community_cards'].get('flop', []))} {hand_data['community_cards'].get('turn', '')}] [{river}]")
                
                # Format action
                action_str = f"{action['player']}"
                if action['action'] == 'raises':
                    action_str += f" raises to {action['amount']}"
                elif action['action'] in ['calls', 'bets']:
                    action_str += f" {action['action']} {action['amount']}"
                else:
                    action_str += f" {action['action']}"
                history.append(action_str)
        
        # Pot
        if hand_data.get('pot'):
            history.append(f"\nTotal pot {hand_data['pot']}")
            
        return "\n".join(history)

    def process_images_to_hand_history(self, input_dir):
        """Process all images in a directory and generate hand history."""
        if not os.path.exists(input_dir):
            raise ValueError(f"Input directory {input_dir} does not exist")
            
        # Get all image files and extract moment numbers
        def get_moment_number(filename):
            try:
                # Extract number after last underscore (e.g., "poker_moment_21" -> 21)
                return int(filename.split('_')[-1].split('.')[0])
            except (IndexError, ValueError):
                return float('inf')  # Put files without valid numbers at the end
                
        # Get and sort image files by moment number
        image_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        image_files.sort(key=get_moment_number)  # Sort based on moment number
        
        complete_history = []
        hand_number = int(time.time())  # Use timestamp as starting hand number
        
        for image_file in image_files:
            image_path = os.path.join(input_dir, image_file)
            print(f"Processing {image_file}...")
            
            # Analyze image
            hand_data = self.analyze_image_for_hand_history(image_path)
            if hand_data:
                # Convert to PokerStars format
                history = self.convert_to_pokerstars_format(hand_data, hand_number)
                complete_history.append(history)
                hand_number += 1
        
        # Print complete history
        print("\nComplete Hand History:")
        print("=" * 50)
        print("\n\n".join(complete_history))
        print("=" * 50)
        
        return complete_history

    def detect_cards_on_table(self, frame):
        """Detect playing cards on the table using color and shape detection."""
        # Convert to HSV color space
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Define color ranges for white cards
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        
        # Create mask for white colors
        mask = cv2.inRange(hsv, lower_white, upper_white)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by size and shape to identify cards
        cards = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if 1000 < area < 5000:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w)/h
                if 0.5 < aspect_ratio < 0.9:
                    cards.append((x, y, w, h))
        
        return len(cards)

    def detect_chip_stacks(self, frame):
        """Detect poker chip stacks using circle detection."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=30,
            param1=50,
            param2=30,
            minRadius=10,
            maxRadius=30
        )
        
        if circles is not None:
            return len(circles[0])
        return 0

    def should_take_screenshot(self, frame):
        """Determine if current frame represents a key moment."""
        current_time = time.time()
        
        if current_time - self.last_screenshot_time < self.min_screenshot_interval:
            return False
            
        if self.previous_frame is not None:
            # Calculate frame difference
            diff = cv2.absdiff(frame, self.previous_frame)
            mean_diff = np.mean(diff)
            
            # Detect cards and chips
            num_cards = self.detect_cards_on_table(frame)
            num_chips = self.detect_chip_stacks(frame)
            
            # Define regions and prompts for GPT-4 Vision analysis
            pot_region = (1000, 600, 250, 80)
            # Left side for player actions (bet/call/check)
            action_region = (150, 600, 300, 100)
            
            pot_prompt = "What is the current pot size shown in this image? Return only the number, no text."
            action_prompt = "What poker action is shown in this image? Return only the action word (call, raise, fold, all-in)"
            
            # Analyze regions with GPT-4 Vision
            pot_text = self.analyze_region_with_gpt4(frame, pot_region, pot_prompt)
            action_text = self.analyze_region_with_gpt4(frame, action_region, action_prompt)
            
            # Decision logic for taking screenshot
            should_capture = (
                mean_diff > 50 or
                num_cards in [3, 4, 5] or
                'raise' in action_text.lower() or
                'all-in' in action_text.lower() or
                pot_text.strip().replace('$', '').replace('€', '').isdigit()
            )
            print(f"{should_capture} for frame {current_time} ")   
            if should_capture:
                self.last_screenshot_time = current_time
                return True
                
        self.previous_frame = frame.copy()
        return False

    def process_video(self, video_path, output_dir):
        """Process poker video and save screenshots of key moments."""
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            
            # Process every 5th frame to improve performance
            #if frame_count % 5 != 0:
             #   continue
                
            if self.should_take_screenshot(frame):
                screenshot_path = f"{output_dir}/poker_moment_{frame_count}.jpg"
                cv2.imwrite(screenshot_path, frame)
                print(f"Screenshot saved: {screenshot_path}")
                
        cap.release()

# Usage example
if __name__ == "__main__":
    api_key = os.getenv("OPENAI_KEY")
    if not api_key:
        raise ValueError("OPENAI_KEY environment variable is not set")
    detector = PokerGPT4Detector(api_key)
    # detector.process_video("poker_game1.mp4", "screenshots/game1")
    detector.process_images_to_hand_history("screenshots/game1")
