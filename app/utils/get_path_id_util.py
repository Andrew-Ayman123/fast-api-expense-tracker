"""Utility to extract IDs from request path parameters."""
import uuid

from fastapi import Request


async def get_id_from_path(request: Request, id_key: str) -> uuid.UUID:
    """Extract ID from the request path parameters."""
    path_params = request.path_params
    id_str = path_params.get(id_key)

    if not id_str:
        message = f"{id_key} is required in the path."
        raise ValueError(message)
    return uuid.UUID(id_str)
