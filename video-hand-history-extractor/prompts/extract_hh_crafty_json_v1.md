When extracting poker hand information from game screenshots, follow these steps and guidelines to create a structured JSON output:

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
Generate JSON confirming to provide json schem

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