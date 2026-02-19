import logging
import os

logger = logging.getLogger(__name__)


def get_env_file_variables(path: str) -> dict:
	"""Load configuration from environment variables first, then fall back to .env file."""
	values = {}

	# First, check environment variables
	env_keys = ['ALBUM', 'GENRE', 'TITLE_SUFFIX', 'ORG']
	for key in env_keys:
		if key in os.environ:
			values[key] = os.environ[key]
			logger.debug(f"Loaded {key} from environment variable")

	# Then, load from .env file (only for keys not already set)
	if not os.path.exists(path):
		if not values:
			logger.warning("env file not found at %s and no environment variables set; using defaults", path)
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

			# Only use file value if not already set from environment
			if key not in values:
				values[key] = value

	return values
