import logging
import os

logger = logging.getLogger(__name__)


def get_env_file_variables(path: str) -> dict:
	values = {}
	if not os.path.exists(path):
		logger.warning("env file not found; expected at %s; using defaults", path)
		return values
	with open(path, "r", encoding="utf-8") as handle:
		for raw_line in handle:
			line = raw_line.strip()
			if not line or line.startswith("#"):
				continue
			if "=" not in line:
				continue
			key, value = line.split("=", 1)
			key = key.strip()
			value = value.strip().strip('"').strip("'")

			values[key] = value
	return values
