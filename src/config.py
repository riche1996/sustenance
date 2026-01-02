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
    
    # TFS/Azure DevOps Configuration
    TFS_URL = os.getenv("TFS_URL", "https://dev.azure.com")
    TFS_ORGANIZATION = os.getenv("TFS_ORGANIZATION", "")
    TFS_PROJECT = os.getenv("TFS_PROJECT", "")
    TFS_PAT = os.getenv("TFS_PAT", "")  # Personal Access Token
    
    # GitHub Configuration
    GITHUB_OWNER = os.getenv("GITHUB_OWNER", "")
    GITHUB_REPO = os.getenv("GITHUB_REPO", "")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    
    # Bug Tracking System Selection
    BUG_TRACKER = os.getenv("BUG_TRACKER", "jira")  # jira, tfs, or github
    
    # Claude API Configuration (for code analysis)
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
    
    # Azure OpenAI Configuration (for agent routing/chat)
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    # LLM Provider Selection
    # "azure" = Azure OpenAI, "anthropic" = Claude, "openai" = OpenAI
    AGENT_LLM_PROVIDER = os.getenv("AGENT_LLM_PROVIDER", "anthropic")  # For agent/chat
    CODE_ANALYSIS_LLM = os.getenv("CODE_ANALYSIS_LLM", "anthropic")    # For code analysis
    
    # Repository Configuration
    REPO_PATH = Path(os.getenv("REPO_PATH", "./code_files"))
    
    # Report Configuration
    REPORT_OUTPUT_PATH = Path(os.getenv("REPORT_OUTPUT_PATH", "./reports"))
    
    # OpenSearch Configuration
    OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
    OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", "9200"))
    OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "bug_analysis_logs")
    
    # Embedding Configuration
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    ENABLE_LOG_HISTORY = os.getenv("ENABLE_LOG_HISTORY", "true").lower() == "true"
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        required_vars = []
        
        # LLM provider requirements
        if cls.AGENT_LLM_PROVIDER == "anthropic" or cls.CODE_ANALYSIS_LLM == "anthropic":
            required_vars.append(("ANTHROPIC_API_KEY", cls.ANTHROPIC_API_KEY))
        
        if cls.AGENT_LLM_PROVIDER == "azure":
            required_vars.extend([
                ("AZURE_OPENAI_ENDPOINT", cls.AZURE_OPENAI_ENDPOINT),
                ("AZURE_OPENAI_KEY", cls.AZURE_OPENAI_KEY),
                ("AZURE_OPENAI_DEPLOYMENT", cls.AZURE_OPENAI_DEPLOYMENT),
            ])
        
        # Bug tracker specific requirements
        if cls.BUG_TRACKER == "jira":
            required_vars.extend([
                ("JIRA_URL", cls.JIRA_URL),
                ("JIRA_EMAIL", cls.JIRA_EMAIL),
                ("JIRA_API_TOKEN", cls.JIRA_API_TOKEN),
            ])
        elif cls.BUG_TRACKER == "tfs":
            required_vars.extend([
                ("TFS_URL", cls.TFS_URL),
                ("TFS_ORGANIZATION", cls.TFS_ORGANIZATION),
                ("TFS_PROJECT", cls.TFS_PROJECT),
                ("TFS_PAT", cls.TFS_PAT),
            ])
        elif cls.BUG_TRACKER == "github":
            required_vars.extend([
                ("GITHUB_OWNER", cls.GITHUB_OWNER),
                ("GITHUB_REPO", cls.GITHUB_REPO),
                ("GITHUB_TOKEN", cls.GITHUB_TOKEN),
            ])
        
        missing = [name for name, value in required_vars if not value]
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        
        # Create directories if they don't exist
        cls.REPORT_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
        
        return True
