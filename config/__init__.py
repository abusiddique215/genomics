import os
import yaml
from typing import Dict, Any
from pathlib import Path

class Config:
    """Configuration management class"""
    
    def __init__(self):
        self._config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration based on environment"""
        env = os.getenv('ENV', 'default')
        config_path = Path(__file__).parent / f"{env}.yml"
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Replace environment variables
        self._config = self._replace_env_vars(config)
    
    def _replace_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively replace environment variables in config"""
        if isinstance(config, dict):
            return {k: self._replace_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._replace_env_vars(v) for v in config]
        elif isinstance(config, str) and config.startswith('${') and config.endswith('}'):
            env_var = config[2:-1]
            return os.getenv(env_var, config)
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        try:
            keys = key.split('.')
            value = self._config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def __getitem__(self, key: str) -> Any:
        """Get configuration value using dictionary syntax"""
        return self.get(key)
    
    @property
    def database(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.get('database', {})
    
    @property
    def services(self) -> Dict[str, Any]:
        """Get services configuration"""
        return self.get('services', {})
    
    @property
    def security(self) -> Dict[str, Any]:
        """Get security configuration"""
        return self.get('security', {})
    
    @property
    def features(self) -> Dict[str, Any]:
        """Get feature flags"""
        return self.get('features', {})

# Create global config instance
config = Config()
