"""FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status

from ai_security_camera import __version__
from ai_security_camera.api.auth import require_token
from ai_security_camera.api.schemas import EventCreate, EventOut
from ai_security_camera.api.storage import EventStore
from ai_security_camera.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    store = EventStore(settings.sqlite_path)
    app.state.event_store = store
    try:
        yield
    finally:
        store.close()


def get_store(request: Request) -> EventStore:
    return request.app.state.event_store


app = FastAPI(
    title="ai-security-camera",
    version=__version__,
    lifespan=lifespan,
)

StoreDep = Annotated[EventStore, Depends(get_store)]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.post("/v1/events", response_model=EventOut, dependencies=[Depends(require_token)])
def create_event(body: EventCreate, store: StoreDep) -> EventOut:
    return store.create_event(body)


@app.get("/v1/events", response_model=list[EventOut], dependencies=[Depends(require_token)])
def list_events(store: StoreDep, limit: int = 50) -> list[EventOut]:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="bad limit")
    return store.list_events(limit=limit)


@app.get("/v1/events/{eid}", response_model=EventOut, dependencies=[Depends(require_token)])
def get_event(eid: str, store: StoreDep) -> EventOut:
    try:
        return store.get_event(eid)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found") from None
