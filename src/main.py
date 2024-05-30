from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from game.router import router as router_game
from auth.router import router as router_auth
from schemas import (
    ErrorResponseDTO,
    PydanticErrorResponseDTO,
    MessageErrorResponseDTO,
)
from utils import PydanticConvertor

app = FastAPI(
    title="Poker app",
    responses={
        401: {"model": ErrorResponseDTO[MessageErrorResponseDTO]},
        422: {"model": ErrorResponseDTO[PydanticErrorResponseDTO]},
    },
)

ORIGINS = {"*"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request, exc: RequestValidationError
):
    errors = PydanticConvertor().convert_errors(exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"error": {"errors": errors}}),
    )


@app.exception_handler(HTTPException)
async def validation_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({"error": {"message": exc.detail}}),
    )


app.include_router(router_game)
app.include_router(router_auth)
