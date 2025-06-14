class GameIsFinishedError(Exception):
    """Raised when an action is attempted on a finished game."""

    def __init__(self, message="The game is finished."):
        self.message = message
        super().__init__(self.message)
