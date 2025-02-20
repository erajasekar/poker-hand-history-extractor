**Objective:**

Extract poker game details and hand history from the provided image and structure the output in JSON format that strictly adheres to the given JSON schema. If a previous poker hand history JSON is provided, merge new information into it using an **upsert operation**, ensuring that new details are added while preserving existing data. If an `id` matches, update the existing entry instead of replacing or deleting any prior data. If no previous hand history is available, generate a new one.

## **JSON Schema for Output Format:**

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

## **Guidelines:**

### **1. Data Extraction & Formatting:**
- Identify all relevant poker game details from the image, including player names, bets, community cards, and actions.
- If a previous hand history JSON is provided, merge new information into it using an **upsert approach**, updating existing records when `id` matches, but never deleting data.
- If no previous hand history is available, create a new JSON.
- Ensure all extracted text is clean and free of OCR artifacts.

### **2. Handling Missing or Unavailable Data:**
- If a required field is missing in the image, assign:
  - "missing" for string fields.
  - 0 for numeric fields.
  - false for boolean fields.
  - [] for empty lists.
- Auto-generate unique IDs for player_id, game_number, and other identifier fields based on the expected data type.

### **3. Data Validation:**
- Ensure the final JSON output strictly conforms to the given schema.
- Verify all required fields are populated.
- Validate JSON structure to avoid schema mismatches.

---

## **Step-by-Step Extraction Guide:**

### **1. Extract General Game Information**
- Extract game metadata such as site name, game type, table size, bet limits, currency, blinds, and ante.
- If a previous history exists, merge any new details into corresponding fields but **do not overwrite existing values unless they are explicitly updated**.

### **2. Extract Player Information**
- Identify all players in the game, ensuring new players are added while retaining existing ones.
- For each player, extract and merge the following fields:
  - `id`: Maintain existing player IDs and only add new ones if not previously recorded.
  - `seat`, `name`, `display`, `starting_stack`, `player_bounty`, and `is_sitting_out` should be updated if new information is available but should never be removed.

### **3. Extract Hand Rounds and Actions**
- Identify rounds (Pre-Flop, Flop, Turn, River) and merge actions accordingly.
- When merging:
  - If an action for a player in a specific round already exists, update the action **only if new details are available**.
  - Do **not** remove any previously recorded actions.
  - Ensure correct order of actions is maintained when appending new ones.

### **4. Extract Pot and Winnings**
- Identify the pot size and breakdown.
- When merging, add new winning records while keeping all previously recorded winnings.
- If a player wins a new pot, append it under `player_wins` instead of overwriting.

### **5. Extract Tournament-Specific Details (If Applicable)**
- If the game is a tournament, ensure all tournament fields are merged appropriately without removing any pre-existing data.


## **Merging with Previous Hand History JSON (Upsert Operation)**

- **Players:**
  - If a player already exists (matching `id`), update their attributes if new details are available.
  - If a new player appears, append them to the list without affecting existing ones.

- **Rounds and Actions:**
  - If a round already exists, add any new actions to it while keeping the previous actions intact.
  - If a new round appears, append it to the `rounds` list.

- **Pots:**
  - If new winnings or pot information is available, append it without deleting any prior records.

- **General Metadata:**
  - Update fields only if new values are extracted but do not remove previous values if the new data is incomplete.


## **Output Example (Merged JSON Format)**

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

## **Final Notes:**
- **Always apply an upsert strategy when merging:** Never remove existing information, only add or update fields where applicable.
- Ensure extracted data is structured correctly and validates successfully against the provided JSON schema.
- Maintain the correct sequence of player actions and game state updates.
- Use schema validation tools to verify compliance with the JSON format.

This is the previous hand history JSON:

```json
{
    "ohh": {
        "spec_version": "1.0",
        "site_name": "PokerGO",
        "network_name": "WSOP",
        "internal_version": "1.0",
        "tournament": true,
        "tournament_info": {
            "id": "WSOP_2024_Main_Event",
            "buyin": "missing",
            "entry_fee": "missing",
            "bounty": 0,
            "speed": {
                "type": "standard",
                "duration": 0
            },
            "start_time": "missing",
            "table_size": 9,
            "starting_stack": "missing",
            "current_level": "missing",
            "level_duration": "missing",
            "late_reg_duration": "missing",
            "rebuy_duration": "missing",
            "addon_duration": "missing",
            "players_remaining": "missing",
            "prize_pool": "missing",
            "in_the_money": "missing"
        },
        "game_number": "missing",
        "start_date_utc": "2025-02-20T00:16:26.700108",
        "table_name": "WSOP Final Table",
        "table_handle": "missing",
        "table_skin": "missing",
        "game_type": "Texas Hold'em",
        "bet_limit": {
            "bet_type": "No Limit",
            "bet_cap": 0
        },
        "table_size": 9,
        "currency": "USD",
        "dealer_seat": "missing",
        "small_blind_amount": 800000,
        "big_blind_amount": 1600000,
        "ante_amount": 0,
        "hero_player_id": "missing",
        "flags": [],
        "players": [
            {
                "id": 1,
                "seat": 1,
                "name": "Angelov",
                "display": "Angelov",
                "starting_stack": 56900000,
                "player_bounty": 0,
                "is_sitting_out": false
            },
            {
                "id": 2,
                "seat": 2,
                "name": "Latinois",
                "display": "Latinois",
                "starting_stack": 24700000,
                "player_bounty": 0,
                "is_sitting_out": false
            },
            {
                "id": 3,
                "seat": 3,
                "name": "Kim",
                "display": "Kim",
                "starting_stack": 98600000,
                "player_bounty": 0,
                "is_sitting_out": false
            },
            {
                "id": 4,
                "seat": 4,
                "name": "Astedt",
                "display": "Astedt",
                "starting_stack": 98200000,
                "player_bounty": 0,
                "is_sitting_out": false
            },
            {
                "id": 5,
                "seat": 5,
                "name": "Serock",
                "display": "Serock",
                "starting_stack": 86300000,
                "player_bounty": 0,
                "is_sitting_out": false
            },
            {
                "id": 6,
                "seat": 6,
                "name": "Griff",
                "display": "Griff",
                "starting_stack": 139700000,
                "player_bounty": 0,
                "is_sitting_out": false
            },
            {
                "id": 7,
                "seat": 7,
                "name": "Tamayo",
                "display": "Tamayo",
                "starting_stack": 22700000,
                "player_bounty": 0,
                "is_sitting_out": false
            },
            {
                "id": 8,
                "seat": 8,
                "name": "Gonzalez",
                "display": "Gonzalez",
                "starting_stack": 14300000,
                "player_bounty": 0,
                "is_sitting_out": false
            },
            {
                "id": 9,
                "seat": 9,
                "name": "Sagle",
                "display": "Sagle",
                "starting_stack": 68100000,
                "player_bounty": 0,
                "is_sitting_out": false
            }
        ],
        "rounds": [
            {
                "name": "Preflop",
                "street_cards": [],
                "actions": [
                    {
                        "player_id": 6,
                        "action_type": "raise",
                        "amount": 3200000,
                        "is_all_in": false
                    },
                    {
                        "player_id": 7,
                        "action_type": "fold",
                        "amount": 0,
                        "is_all_in": false
                    }
                ]
            }
        ],
        "pots": [
            {
                "type": "main",
                "amount": 7200000,
                "rake": 0,
                "player_wins": []
            }
        ],
        "tournament_bounties": []
    }
}
```
