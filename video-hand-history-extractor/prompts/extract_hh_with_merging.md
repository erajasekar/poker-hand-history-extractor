**Objective:**

Extract poker game details and hand history from the provided image and structure the output in JSON format that strictly adheres to the given JSON schema. If a previous poker hand history JSON is provided, merge new information into it based on semantic meaning instead of creating a new JSON from scratch. If no previous hand history is available, generate a new one.

## JSON schema for output format:

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
      "ohh": {
        "type": "object",
        "properties": {
          "spec_version": { "type": "string", "format": "version_string" },
          "site_name": { "type": "string" },
          "network_name": { "type": "string" },
          "internal_version": { "type": "string", "format": "version_string" },
          "tournament": { "type": "boolean" },
          "tournament_info": { "$ref": "#/definitions/tournament_info_obj" },
          "game_number": { "type": "string" },
          "start_date_utc": { "type": "string", "format": "date-time" },
          "table_name": { "type": "string" },
          "table_handle": { "type": "string" },
          "table_skin": { "type": "string" },
          "game_type": { "type": "string" },
          "bet_limit": { "$ref": "#/definitions/bet_limit_obj" },
          "table_size": { "type": "integer" },
          "currency": { "type": "string" },
          "dealer_seat": { "type": "integer" },
          "small_blind_amount": { "type": "number" },
          "big_blind_amount": { "type": "number" },
          "ante_amount": { "type": "number" },
          "hero_player_id": { "type": "integer" },
          "flags": {
            "type": "array",
            "items": { "type": "string" }
          },
          "players": {
            "type": "array",
            "items": { "$ref": "#/definitions/player_obj" }
          },
          "rounds": {
            "type": "array",
            "items": { "$ref": "#/definitions/round_obj" }
          },
          "pots": {
            "type": "array",
            "items": { "$ref": "#/definitions/pot_obj" }
          },
          "tournament_bounties": {
            "type": "array",
            "items": { "$ref": "#/definitions/tournament_bounty_obj" }
          }
        },
        "required": [
          "spec_version", "site_name", "game_number", "start_date_utc",
          "game_type", "bet_limit", "table_size", "currency", "dealer_seat",
          "small_blind_amount", "big_blind_amount", "players", "rounds", "pots"
        ]
      }
    },
    "required": ["ohh"],
    "definitions": {
      "bet_limit_obj": {
        "type": "object",
        "properties": {
          "bet_type": { "type": "string" },
          "bet_cap": { "type": "number" }
        },
        "required": ["bet_type"]
      },
      "player_obj": {
        "type": "object",
        "properties": {
          "id": { "type": "integer" },
          "seat": { "type": "integer" },
          "name": { "type": "string" },
          "display": { "type": "string" },
          "starting_stack": { "type": "number" },
          "player_bounty": { "type": "number" },
          "is_sitting_out": { "type": "boolean" }
        },
        "required": ["id", "seat", "name", "starting_stack"]
      },
      "round_obj": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "street_cards": {
            "type": "array",
            "items": { "type": "string", "format": "card_string" }
          },
          "actions": {
            "type": "array",
            "items": { "$ref": "#/definitions/action_obj" }
          }
        },
        "required": ["actions"]
      },
      "action_obj": {
        "type": "object",
        "properties": {
          "player_id": { "type": "integer" },
          "action_type": { "type": "string" },
          "amount": { "type": "number" },
          "is_all_in": { "type": "boolean" }
        },
        "required": ["player_id"]
      },
      "pot_obj": {
        "type": "object",
        "properties": {
          "type": { "type": "string" },
          "amount": { "type": "number" },
          "rake": { "type": "number" },
          "player_wins": {
            "type": "array",
            "items": { "$ref": "#/definitions/player_wins_obj" }
          }
        },
        "required": ["amount", "player_wins"]
      },
      "player_wins_obj": {
        "type": "object",
        "properties": {
          "player_id": { "type": "integer" },
          "amount": { "type": "number" },
          "hand": {
            "type": "array",
            "items": { "type": "string", "format": "card_string" }
          },
          "hand_name": { "type": "string" }
        },
        "required": ["player_id"]
      },
      "tournament_info_obj": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "buyin": { "type": "number" },
          "entry_fee": { "type": "number" },
          "bounty": { "type": "number" },
          "speed": { "$ref": "#/definitions/speed_obj" },
          "start_time": { "type": "string", "format": "date-time" },
          "table_size": { "type": "integer" },
          "starting_stack": { "type": "number" },
          "current_level": { "type": "integer" },
          "level_duration": { "type": "integer" },
          "late_reg_duration": { "type": "integer" },
          "rebuy_duration": { "type": "integer" },
          "addon_duration": { "type": "integer" },
          "players_remaining": { "type": "integer" },
          "prize_pool": { "type": "number" },
          "in_the_money": { "type": "boolean" }
        }
      },
      "tournament_bounty_obj": {
        "type": "object",
        "properties": {
          "player_id": { "type": "integer" },
          "amount": { "type": "number" }
        },
        "required": ["player_id", "amount"]
      },
      "speed_obj": {
        "type": "object",
        "properties": {
          "type": { "type": "string" },
          "duration": { "type": "integer" }
        },
        "required": ["type"]
      }
    }
  }
```  


**Guidelines:**

1. **Data Extraction & Formatting:**
   - Identify all relevant poker game details from the image, including player names, bets, community cards, and actions.
   - If a previous hand history JSON is provided, update it by merging new information based on semantic meaning rather than overwriting the entire structure.
   - If no previous hand history is available, create a new JSON.
   - Ensure all extracted text is clean and free of OCR artifacts.

2. **Handling Missing or Unavailable Data:**
   - If a required field is missing in the image, assign:
     - "missing" for string fields.
     - 0 for numeric fields.
     - false for boolean fields.
     - [] for empty lists.
   - Auto-generate unique IDs for player_id, game_number, and other identifier fields based on the expected data type.

3. **Data Validation:**
   - Ensure the final JSON output strictly conforms to the given schema.
   - Verify all required fields are populated.
   - Validate JSON structure to avoid schema mismatches.

---

### **Step-by-Step Extraction Guide**

#### 1. **Extract General Game Information**
   - `spec_version`: Assign a default version (e.g., "1.0").
   - `site_name`: Extract poker platform/site name.
   - `network_name`: Extract poker network (if present).
   - `internal_version`: Extract or assign "missing".
   - `tournament`: Determine whether it is a tournament (true/false).
   - `tournament_info`: If applicable, extract tournament details.
   - `game_number`: Extract or auto-generate if not visible.
   - `start_date_utc`: Extract timestamp or assign "missing".
   - `table_name` and `table_handle`: Extract if available.
   - `table_skin`: Extract or set "missing".
   - `game_type`: Identify from the game (e.g., "Texas Hold'em").
   - `bet_limit`: Extract bet type (e.g., "No Limit", "Pot Limit") and set `bet_cap` to 0 if unknown.
   - `table_size`: Count number of seats at the table.
   - `currency`: Extract (e.g., "USD", "missing" if not available).
   - `dealer_seat`: Identify dealer position.
   - `small_blind_amount` and `big_blind_amount`: Extract from game info.
   - `ante_amount`: Extract or set 0 if not applicable.
   - `hero_player_id`: Identify the "Hero" player (if applicable).

#### 2. **Extract Player Information**
   - Identify all players in the game.
   - For each player, extract:
     - `id`: Assign an auto-generated unique integer.
     - `seat`: Identify from the image.
     - `name` and `display`: Extract player name.
     - `starting_stack`: Extract or assign 0 if missing.
     - `player_bounty`: Extract for tournaments or assign 0.
     - `is_sitting_out`: Determine if the player is inactive (true/false).

#### 3. **Extract Hand Rounds and Actions**
   - Identify each game round (Pre-Flop, Flop, Turn, River).
   - Extract community cards for each round.
   - Capture player actions per round, including:
     - `player_id`: Map player ID.
     - `action_type`: Extract ("fold", "call", "raise", "check", "bet", "all-in").
     - `amount`: Extract the bet amount.
     - `is_all_in`: Determine if the player went all-in (true/false).

#### 4. **Extract Pot and Winnings**
   - Identify the total pot size and breakdown.
   - Extract winners and their earnings.
   - Capture their final hands, including:
     - `player_id`
     - `amount`
     - `hand`: List of final hole cards.
     - `hand_name`: Extract the name of the winning hand (e.g., "Flush").

#### 5. **Extract Tournament-Specific Details (If Applicable)**
   - If a tournament, capture:
     - Buy-in, entry fee, bounty.
     - Tournament start time, structure details.
     - Remaining players, prize pool, and payout information.

---

### **Merging with Previous Hand History JSON**

- If a previous hand history JSON is provided, update it by merging new information instead of recreating it from scratch.
- Preserve existing hand history data unless explicitly updated by newly extracted details.
- Merge actions, player states, and round details logically based on their semantic meaning to maintain an accurate timeline of the game.
- Ensure consistency in player IDs, actions, and game state updates across merged JSON data.

---

### **Output Format Example**

```json
{
    "ohh": {
        "spec_version": "1.2.2",
        "internal_version": "1.2.2",
        "network_name": "PokerStars",
        "site_name": "PokerStars",
        "game_type": "Holdem",
        "start_date_utc": "2019-03-28T08:16:05",
        "table_size": 3,
        "table_name": "2572001822 1",
        "game_number": "198636399064",
        "currency": "",
        "ante_amount": 0.00,
        "small_blind_amount": 10.00,
        "big_blind_amount": 20.00,
        "bet_limit": {
            "bet_cap": 0.00,
            "bet_type": "NL"
        },
        "players": [
            {
                "name": "Hero",
                "id": 0,
                "player_bounty": 0,
                "starting_stack": 500.00,
                "seat": 1
            }
        ],
        "rounds": [
            {
                "id": 0,
                "street": "Preflop",
                "actions": [
                    {
                        "action_number": 1,
                        "player_id": 2,
                        "action": "Post SB",
                        "amount": 10.00,
                        "is_allin": false
                    }
                ]
            }
        ],
        "pots": [
            {
                "rake": 0.00,
                "number": 0,
                "player_wins": [
                    {
                        "player_id": 2,
                        "win_amount": 40.00,
                        "contributed_rake": 0.00
                    }
                ],
                "amount": 40.00
            }
        ]
    }
}
```

### **Final Notes**
- Ensure extracted data is structured correctly and validates successfully against the provided JSON schema.
- Merge new details into existing hand history JSON instead of overwriting or duplicating data.
- Derive missing information logically where possible.
- Test the final JSON with a schema validator to confirm compliance.



