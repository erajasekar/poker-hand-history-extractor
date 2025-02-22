from CraftyWheelPokerHandHistory import CraftyWheelPokerHandHistory, Action, ActionType, Street
import json;

class PokerHandProcessor:
    def __init__(self):
        self.final_history = CraftyWheelPokerHandHistory()
        
    def handle(self, hand_history: CraftyWheelPokerHandHistory):
        # Skip if either history is empty or has error
        if not hand_history.players or hand_history.error:
            return
        if not self.final_history.players:
            self.final_history.players = []

        # Get current street from hand_history
        current_street = hand_history.get_current_street()

        # Step 1: For each player in final_history, check if present in hand_history
        for final_player in self.final_history.players:
            found = False
            for hand_player in hand_history.players:
                if final_player.name == hand_player.name:
                    found = True
                    break
            
            # If player not found in hand_history, add flop action
            if not found:
                fold_action = Action(type=ActionType.FOLD, amount=0)
                if current_street == Street.PREFLOP:
                    final_player.actions.preflop.append(fold_action)
                elif current_street == Street.FLOP:
                    final_player.actions.flop.append(fold_action)
                elif current_street == Street.TURN:
                    final_player.actions.turn.append(fold_action)
                elif current_street == Street.RIVER:
                    final_player.actions.river.append(fold_action)

        # Step 2: Get players with cards and copy their actions
        players_with_cards = hand_history.get_player_with_cards()
        for player_with_cards in players_with_cards:
            found = False
            for final_player in self.final_history.players:
                if final_player.name == player_with_cards.name:
                    # Copy all actions from all streets
                    final_player.actions.preflop.extend(player_with_cards.actions.preflop)
                    final_player.actions.flop.extend(player_with_cards.actions.flop)
                    final_player.actions.turn.extend(player_with_cards.actions.turn)
                    final_player.actions.river.extend(player_with_cards.actions.river)
                    found = True
                    break
            
            # If player not found in final_history, add them
            if not found:
                self.final_history.players.append(player_with_cards)

        # Step 3: Copy remaining fields from hand_history players to final_history
        for hand_player in hand_history.players:
            for final_player in self.final_history.players:
                if final_player.name == hand_player.name:
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
        return json.dumps(self.final_history, indent=4, default=lambda x: x.__dict__)
