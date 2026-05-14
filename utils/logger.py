import logging
from datetime import datetime
from pathlib import Path


def setup_logger(log_level=logging.INFO):
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create log filename with timestamp
    log_filename = f"nebula_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_path = log_dir / log_filename

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure root logger
    logger = logging.getLogger("Nebula")
    logger.setLevel(log_level)

    # File handler
    file_handler = logging.FileHandler(log_path, encoding="utf-8", mode="w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info("=" * 60)
    logger.info(f"✓ Logger initialized - Logs: {log_path}")
    logger.info("=" * 60)

    return logger
