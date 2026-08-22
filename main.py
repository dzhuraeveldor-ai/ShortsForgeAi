import logging
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from worker.config import settings


def setup_logging() -> None:
    """Configure worker logging."""
    Path(settings.LOG_DIR).mkdir(parents=True, exist_ok=True)

    log_level = logging.DEBUG if settings.DEV_MODE else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                f"{settings.LOG_DIR}/worker.log",
                encoding="utf-8"
            )
        ]
    )

    # Set log levels for noisy libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def init_database_tables() -> None:
    """Initialize database tables on startup."""
    from database.database import init_database
    init_database()


def main() -> None:
    """Start the ShortsForge AI Worker."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("ShortsForge AI Worker starting...")
    logger.info(f"Version: {settings.APP_VERSION}")
    logger.info(f"Worker ID: {settings.WORKER_ID}")
    logger.info(f"Mode: {'DEVELOPMENT' if settings.DEV_MODE else 'PRODUCTION'}")

    # Initialize database
    init_database_tables()
    logger.info("Database initialized")

    # Start API server
    import uvicorn

    logger.info(f"Starting API server on {settings.WORKER_HOST}:{settings.WORKER_PORT}")
    logger.info("=" * 60)

    uvicorn.run(
        "worker.api.server:app",
        host=settings.WORKER_HOST,
        port=settings.WORKER_PORT,
        workers=1,  # Single worker to avoid concurrent job processing issues
        log_level="info",
        reload=settings.DEV_MODE
    )


if __name__ == "__main__":
    main()
