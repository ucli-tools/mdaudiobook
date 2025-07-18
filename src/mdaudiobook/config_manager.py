import os
import yaml
import json
from pathlib import Path
from dotenv import load_dotenv

class ConfigManager:
    """Manages loading of configuration and secrets for mdaudiobook."""

    def __init__(self, config_file=None):
        self.config = {}
        self._load_configuration(config_file)

    def _load_configuration(self, config_file_override=None):
        """Load config from files with a defined precedence."""
        # Define configuration paths
        global_config_dir = Path.home() / '.config' / 'mdaudiobook'
        local_config_dir = Path.cwd()
        local_config_subdir = local_config_dir / 'config'

        # Load environment variables from all possible locations
        # load_dotenv will not override existing env vars, so the first one found wins.
        load_dotenv(dotenv_path=(global_config_dir / '.env'))
        load_dotenv(dotenv_path=(local_config_dir / '.env'))

        # Expand user path for Google credentials to ensure '~' is resolved
        gac_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if gac_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.expanduser(gac_path)

        # Determine config file path with override, then global, then local
        if config_file_override:
            config_file = Path(config_file_override)
        else:
            # Check global user config first
            global_config_yaml = global_config_dir / 'config.yaml'
            if not global_config_yaml.is_file():
                global_config_yaml = global_config_dir / 'default.yaml'

            # Check local config
            local_config_yaml = local_config_subdir / 'default.yaml'
            if not local_config_yaml.is_file():
                local_config_yaml = local_config_dir / 'config.yaml'

            if global_config_yaml.is_file():
                config_file = global_config_yaml
            elif local_config_yaml.is_file():
                config_file = local_config_yaml
            else:
                raise FileNotFoundError(
                    f"Configuration file not found in {global_config_dir} or {local_config_dir}."
                    " Please run 'make install-system' or ensure config exists."
                )

        # Load main YAML configuration
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)



    def _process_google_credentials(self):
        """Process Google Cloud credentials from env var."""
        g_creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        if g_creds_json:
            try:
                creds_info = json.loads(g_creds_json)
            except json.JSONDecodeError:
                # Fail silently if the JSON is invalid
                pass

    def get(self, key, default=None):
        """Get a configuration value."""
        return os.getenv(key, self.config.get(key, default))

# Singleton instance for easy access
config_manager = ConfigManager()
