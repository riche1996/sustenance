"""Configuration management for the bug triaging system."""
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


class Config:
    """Application configuration."""
    
    # Jira Configuration
    JIRA_URL = os.getenv("JIRA_SERVER", os.getenv("JIRA_URL", ""))
    JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
    JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "")
    
    # Claude API Configuration
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
    
    # Repository Configuration
    REPO_PATH = Path(os.getenv("REPO_PATH", "./code_files"))
    
    # Report Configuration
    REPORT_OUTPUT_PATH = Path(os.getenv("REPORT_OUTPUT_PATH", "./reports"))
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        required_vars = [
            ("JIRA_URL", cls.JIRA_URL),
            ("JIRA_EMAIL", cls.JIRA_EMAIL),
            ("JIRA_API_TOKEN", cls.JIRA_API_TOKEN),
            ("ANTHROPIC_API_KEY", cls.ANTHROPIC_API_KEY),
        ]
        
        missing = [name for name, value in required_vars if not value]
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        
        # Create directories if they don't exist
        cls.REPORT_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
        
        return True
