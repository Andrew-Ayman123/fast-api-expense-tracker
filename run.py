"""Runner used to run the FastAPI application."""

import uvicorn

from app.dependencies.settings_dependencies import get_env_settings

if __name__ == "__main__":
    settings = get_env_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.server_reload,
        log_level=settings.server_log_level,
    )
