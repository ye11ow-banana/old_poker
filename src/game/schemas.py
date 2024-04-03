from pydantic import BaseModel, Field, ConfigDict


class PlayersInSearchCount(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    count: int = Field(
        alias="playersInSearchCount",
        description="Number of players in search of a game",
    )
