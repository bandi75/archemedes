from __future__ import annotations

from fastapi import Request

from archimedes.orchestrator.controller import StageController

from .storage import InMemoryArchimedesStorage


def get_storage(request: Request) -> InMemoryArchimedesStorage:
    return request.app.state.storage


def get_stage_controller(request: Request) -> StageController:
    return request.app.state.stage_controller
