from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class Street(str, Enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"

class ActionType(str, Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"

class Action(BaseModel):
    type: ActionType
    amount: float

class Blinds(BaseModel):
    smallBlind: float
    bigBlind: float

class GameInfo(BaseModel):
    tournamentName: str
    eventName: str
    stage: str
    blinds: Blinds

class PlayerActions(BaseModel):
    preflop: List[Action]
    flop: List[Action]
    turn: List[Action]
    river: List[Action]

class Player(BaseModel):
    name: str
    nationality: str
    stack: float
    cards: List[str]
    actions: PlayerActions
    isWinner: bool
    amountWon: float
    isActive: bool = True  # Default to True when player is created

class Board(BaseModel):
    flop: List[str]
    turn: str
    river: str

class CraftyWheelPokerHandHistory(BaseModel):
    gameInfo: Optional[GameInfo] = None
    players: Optional[List[Player]] = None
    board: Optional[Board] = None
    pot: Optional[float] = None
    error: Optional[str] = None

    def to_openai_format(self) -> dict:
        """
        Convert the model to a dictionary format suitable for OpenAI API.
        This method is provided in case you need any special formatting for the API.
        """
        return self.model_dump()

    @classmethod
    def from_openai_response(cls, response_data: dict) -> 'CraftyWheelPokerHandHistory':
        """
        Create an instance from OpenAI API response data.
        
        Args:
            response_data: The JSON data from OpenAI API response
            
        Returns:
            CraftyWheelPokerHandHistory instance
        """
        return cls.model_validate(response_data)

    def get_current_street(self) -> Street:
        """
        Determine the current street based on the board state.
        Returns Street enum value.
        """
        if not self.board:
            return Street.PREFLOP
            
        if not self.board.flop:
            return Street.PREFLOP
            
        if not self.board.turn:
            return Street.FLOP
            
        if not self.board.river:
            return Street.TURN
            
        return Street.RIVER

    def get_player_with_cards(self) -> List[Player]:
        """
        Returns a list of players who have cards.
        """
        if not self.players:
            return []
        return [player for player in self.players if player.cards]
