"""Caps request bodies on chosen paths before the app reads them."""

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.problems import Problem, problem_response


class BodySizeLimit:
    """Refuses with 413 a body over `max_bytes` on `paths`, whether it declares its length or streams it.
    A body within the cap is read here (at most `max_bytes`) and handed on unchanged."""

    def __init__(self, app: ASGIApp, paths: frozenset[str], max_bytes: int):
        self.app, self.paths, self.max_bytes = app, paths, max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] not in self.paths:
            await self.app(scope, receive, send)
            return
        declared = dict(scope["headers"]).get(b"content-length")
        if declared is not None and declared.isdigit() and int(declared) > self.max_bytes:
            await self._refuse(scope, receive, send)
            return
        messages: list[Message] = []
        size = 0
        while True:
            message = await receive()
            messages.append(message)
            if message["type"] != "http.request":
                break
            size += len(message.get("body", b""))
            if size > self.max_bytes:
                await self._refuse(scope, receive, send)
                return
            if not message.get("more_body", False):
                break

        async def replay() -> Message:
            return messages.pop(0) if messages else await receive()

        await self.app(scope, replay, send)

    async def _refuse(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = problem_response(Problem(
            title="Request body too large", status=413, detail=f"Send at most {self.max_bytes} bytes.",
        ))
        await response(scope, receive, send)
