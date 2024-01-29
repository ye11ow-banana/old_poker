from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse

from analysis.router import router as router_analysis
from auth.router import router as router_auth
from schemas import ErrorResponse, PydanticErrorResponse, MessageErrorResponse
from utils import PydanticConvertor

app = FastAPI(
    title="Poker app",
    responses={
        401: {"model": ErrorResponse[MessageErrorResponse]},
        422: {"model": ErrorResponse[PydanticErrorResponse]},
    },
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


app.include_router(router_analysis)
app.include_router(router_auth)
