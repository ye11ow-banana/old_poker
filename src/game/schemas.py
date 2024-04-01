from pydantic import BaseModel, Field


class PlayersInSearchCount(BaseModel):
    count: int = Field(
        alias="playersInSearchCount",
        description="Number of players in search of a game",
    )

    class Config:
        populate_by_name = True
