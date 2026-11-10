from fastapi import FastAPI

from app.api import events
from app.api.problems import install_problem_handlers

app = FastAPI(title="recitAR API")
install_problem_handlers(app)
app.include_router(events.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
