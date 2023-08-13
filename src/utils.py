from fastapi import HTTPException, status
from pydantic import ValidationError


class PydanticConvertor:
    """
    Class for converting Pydantic errors to a list of dicts with fields "field" and "message".
    E.g.:
        from  {..., "loc": ("username",), "msg": "Assertion failed,
              Username must be alphanumeric", ...}
        to {"field": "username", "message": "Username must be alphanumeric"}
    """

    def __init__(
        self,
        error_message_substrings_to_convert: tuple[str, ...] | None = None,
    ) -> None:
        if error_message_substrings_to_convert is None:
            self._error_message_substrings_to_convert: tuple[str, ...] = (
                "error, ",
                "failed, ",
            )
        else:
            self._error_message_substrings_to_convert = (
                error_message_substrings_to_convert
            )

    def convert_errors(self, e: ValidationError) -> list[dict[str, str]]:
        new_errors: list[dict[str, str]] = []
        for error in e.errors():
            try:
                error_message = error["msg"]
            except KeyError:
                error_message = "Unknown error"
            try:
                field = str(error["loc"][0]) if error["loc"] else "all"
            except KeyError:
                field = "all"
            error_message = self._convert_error_message(error_message)
            new_errors.append(
                dict(
                    field=field,
                    message=error_message,
                )
            )
        return new_errors

    def _convert_error_message(self, error_message: str) -> str:
        for error in self._error_message_substrings_to_convert:
            error_message = error_message.split(error)[-1]
        return error_message


def create_http_exception(status_code: int, errors: list) -> HTTPException:
    detail = dict(result=False, errors=errors)
    return HTTPException(status_code=status_code, detail=detail)


def create_response(
    **kwargs,
) -> dict:
    return dict(detail=dict(result=True, **kwargs))
