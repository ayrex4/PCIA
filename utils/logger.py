import logging
import sys

def get_logger(name="PCIA"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        fmt = logging.Formatter('%(asctime)s - [%(levelname)s] - %(name)s: %(message)s')
        
        # Console Handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(fmt)
        logger.addHandler(ch)
        
        # File Handler (Optional: saves logs to file)
        fh = logging.FileHandler("pcia_agent.log")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        
    return logger