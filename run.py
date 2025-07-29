"""Runner used to run the FastAPI application."""

import uvicorn

from app.dependencies import get_env_settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=get_env_settings().server_host,
        port=get_env_settings().server_port,
        reload=get_env_settings().server_reload,
        log_level=get_env_settings().server_log_level,
    )
