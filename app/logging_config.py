import logging

def configure_logging(level: int = logging.DEBUG) -> None:
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()],
    )   