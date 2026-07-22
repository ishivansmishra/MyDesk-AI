import logging
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("mydesk")
