"""Errors as RFC 7807 problem details (`application/problem+json`), the same shape everywhere."""

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException

from app.api.cursor import InvalidCursorError

MEDIA_TYPE = "application/problem+json"


class InvalidParameterError(ValueError):
    """Parameters that are each valid but do not make sense together; the message is the detail."""


class NotFoundError(LookupError):
    def __init__(self, title: str, detail: str):
        super().__init__(detail)
        self.title, self.detail = title, detail


class Problem(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    errors: list[dict] | None = None  # one entry per invalid parameter (422 only)


def problem_response(problem: Problem) -> JSONResponse:
    return JSONResponse(problem.model_dump(exclude_none=True), status_code=problem.status, media_type=MEDIA_TYPE)


def install_problem_handlers(app: FastAPI) -> None:
    @app.exception_handler(InvalidCursorError)
    def invalid_cursor(request: Request, error: InvalidCursorError) -> JSONResponse:
        return problem_response(Problem(
            title="Invalid cursor", status=400,
            detail="Use the next_cursor of a previous page as is, or leave cursor out to get the first page.",
        ))

    @app.exception_handler(InvalidParameterError)
    def invalid_parameter(request: Request, error: InvalidParameterError) -> JSONResponse:
        return problem_response(Problem(title="Invalid request", status=422, detail=str(error)))

    @app.exception_handler(NotFoundError)
    def not_found(request: Request, error: NotFoundError) -> JSONResponse:
        return problem_response(Problem(title=error.title, status=404, detail=error.detail))

    @app.exception_handler(RequestValidationError)
    def invalid_request(request: Request, error: RequestValidationError) -> JSONResponse:
        errors = [{key: item[key] for key in ("loc", "msg", "type") if key in item} for item in error.errors()]
        return problem_response(Problem(
            title="Invalid request", status=422, detail="Some parameters are not valid.", errors=jsonable_encoder(errors),
        ))

    @app.exception_handler(HTTPException)
    def http_error(request: Request, error: HTTPException) -> JSONResponse:
        return problem_response(Problem(title=str(error.detail), status=error.status_code))
