import logging
import os

def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    # Opcional: Configurar un manejador de archivo si se desea
    # file_handler = logging.FileHandler("app.log")
    # file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    # logging.getLogger().addHandler(file_handler)

    logging.info("Configuración de logging inicializada.")
