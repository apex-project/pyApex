# -*- coding: utf-8 -*-
from pyrevit import script
logger = script.get_logger()
_config = script.get_config()

# try:
#     logger.info(_config.test_string2)
# except Exception as exc:
#     logger.info("-")

_config.test_string1 = "s"
# _config.test_string2 = "C:\\a foldere\\n\\t\\r"
# script.save_config()

try:
    _config.test_string3 = u"ы"
except Exception as exc:
    logger.error(exc)

script.save_config()
