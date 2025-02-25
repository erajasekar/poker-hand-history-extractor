from CraftyWheelPokerHandHistory import CraftyWheelPokerHandHistory, Action, ActionType, Street
import json;

class PokerHandProcessor:
    def __init__(self):
        self.final_history = CraftyWheelPokerHandHistory()
    
    def add_non_duplicate_actions(self, existing_actions, new_actions):
        for new_action in new_actions:
            # Check if action already exists
            exists = False
            for existing_action in existing_actions:
                if existing_action.type == new_action.type and existing_action.amount == new_action.amount:
                    exists = True
                    break
            if not exists:
                existing_actions.append(new_action)
        
    def handle(self, hand_history: CraftyWheelPokerHandHistory):

        # Validate hand_history
        hand_history.validate()
        
        # Skip if either history is empty or has error
        if not hand_history.players or hand_history.error:
            return
        if not self.final_history.players:
            self.final_history.players = []

        # Get current street from hand_history
        current_street = hand_history.get_current_street()

        # Log player info before Step 1
        for final_player in [p for p in self.final_history.players]:
            print(f"Before Step 1 - Player: {final_player.name}, isActive: {final_player.isActive}")

        # Step 1: For each active player in final_history, check if present in hand_history
        for final_player in [p for p in self.final_history.players if p.isActive]:
            found = False
            for hand_player in hand_history.players:
                if final_player.name == hand_player.name:
                    found = True
                    break
            
            # If player not found in hand_history, add fold action if it doesn't exist
            if not found:
                fold_action = Action(type=ActionType.FOLD, amount=0)
                fold_actions = [fold_action]
                if current_street == Street.PREFLOP:
                    self.add_non_duplicate_actions(final_player.actions.preflop, fold_actions)
                elif current_street == Street.FLOP:
                    self.add_non_duplicate_actions(final_player.actions.flop, fold_actions)
                elif current_street == Street.TURN:
                    self.add_non_duplicate_actions(final_player.actions.turn, fold_actions)
                elif current_street == Street.RIVER:
                    self.add_non_duplicate_actions(final_player.actions.river, fold_actions)
                print(f"Player {final_player.name} not found in hand_history, adding fold action")
                final_player.isActive = False  # Set isActive to False when fold action is added

        # Step 2: Get players with cards and copy their actions based on current street
        players_with_cards = hand_history.get_player_with_cards()
        for player_with_cards in players_with_cards:
            found = False
            for final_player in self.final_history.players:
                if final_player.name == player_with_cards.name:
                    # Get all actions from hand_history player
                    all_actions = []
                    if player_with_cards.actions.preflop:
                        all_actions.extend(player_with_cards.actions.preflop)
                    if player_with_cards.actions.flop:
                        all_actions.extend(player_with_cards.actions.flop)
                    if player_with_cards.actions.turn:
                        all_actions.extend(player_with_cards.actions.turn)
                    if player_with_cards.actions.river:
                        all_actions.extend(player_with_cards.actions.river)
                    
                    # Add actions to appropriate street based on current_street
                    if current_street == Street.PREFLOP:
                        self.add_non_duplicate_actions(final_player.actions.preflop, all_actions)
                    elif current_street == Street.FLOP:
                        self.add_non_duplicate_actions(final_player.actions.flop, all_actions)
                    elif current_street == Street.TURN:
                        self.add_non_duplicate_actions(final_player.actions.turn, all_actions)
                    elif current_street == Street.RIVER:
                        self.add_non_duplicate_actions(final_player.actions.river, all_actions)
                    found = True
                    break
            
            # If player not found in final_history, add them
            if not found:
                self.final_history.players.append(player_with_cards)

        # Step 3: Copy remaining fields from hand_history players to final_history (only for active players)
        for hand_player in hand_history.players:
            for final_player in [p for p in self.final_history.players if p.isActive]:
                if final_player.name == hand_player.name:
                    final_player.isActive = hand_player.isActive
                    # Update other fields regardless
                    final_player.nationality = hand_player.nationality
                    final_player.stack = hand_player.stack
                    final_player.cards = hand_player.cards
                    final_player.isWinner = hand_player.isWinner
                    final_player.amountWon = hand_player.amountWon
                    break

        # Step 4: Copy game info, board and pot
        if hand_history.gameInfo:
            self.final_history.gameInfo = hand_history.gameInfo
        if hand_history.board:
            self.final_history.board = hand_history.board
        if hand_history.pot:
            self.final_history.pot = hand_history.pot
        
    def get_final_hand_history(self) -> CraftyWheelPokerHandHistory:
        return self.final_history
    
    def get_final_hand_history_json(self) -> str:
        return json.dumps(self.final_history, default=lambda o: o.__dict__, indent=4)
