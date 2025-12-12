"""
Quick setup script for Bug Triage & Analysis System.
Run this to verify your setup and test the connection.
"""
import os
import sys
from pathlib import Path


def check_env_file():
    """Check if .env file exists."""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ .env file not found!")
        print("\n📋 Creating .env from template...")
        
        example_path = Path('.env.example')
        if example_path.exists():
            import shutil
            shutil.copy(example_path, env_path)
            print("✓ .env file created")
            print("\n⚠️  Please edit .env with your credentials before continuing.")
            return False
        else:
            print("❌ .env.example not found!")
            return False
    
    print("✓ .env file exists")
    return True


def check_dependencies():
    """Check if required packages are installed."""
    print("\nChecking dependencies...")
    
    required = {
        'anthropic': 'Anthropic Claude SDK',
        'jira': 'Jira Python library',
        'dotenv': 'python-dotenv',
        'pydantic': 'Pydantic',
        'requests': 'Requests'
    }
    
    missing = []
    
    for package, description in required.items():
        try:
            __import__(package if package != 'dotenv' else 'dotenv')
            print(f"  ✓ {description}")
        except ImportError:
            print(f"  ❌ {description} (pip install {package})")
            missing.append(package)
    
    if missing:
        print("\n⚠️  Missing dependencies. Install with:")
        print(f"    pip install {' '.join(missing)}")
        return False
    
    return True


def check_config():
    """Check if configuration is valid."""
    print("\nChecking configuration...")
    
    try:
        from config import Config
        Config.validate()
        print("✓ Configuration is valid")
        return True
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\n⚠️  Please update your .env file with valid credentials.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_jira_connection():
    """Test Jira connection."""
    print("\nTesting Jira connection...")
    
    try:
        from jira_mcp import JiraMCPServer
        jira = JiraMCPServer()
        print("✓ Connected to Jira successfully")
        return True
    except Exception as e:
        print(f"❌ Jira connection failed: {e}")
        return False


def test_claude_connection():
    """Test Claude API connection."""
    print("\nTesting Claude API connection...")
    
    try:
        import httpx
        from anthropic import Anthropic
        from config import Config
        
        # Create HTTP client with SSL verification disabled
        http_client = httpx.Client(verify=False)
        client = Anthropic(
            api_key=Config.ANTHROPIC_API_KEY,
            http_client=http_client
        )
        
        # Simple test message
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=50,
            messages=[
                {"role": "user", "content": "Say 'Connection successful' and nothing else."}
            ]
        )
        
        print("✓ Claude API connection successful")
        return True
    except Exception as e:
        print(f"❌ Claude API connection failed: {e}")
        return False


def check_repository():
    """Check if repository path exists and has code files."""
    print("\nChecking repository...")
    
    try:
        from config import Config
        
        if not Config.REPO_PATH.exists():
            print(f"❌ Repository path does not exist: {Config.REPO_PATH}")
            return False
        
        # Count code files
        code_files = list(Config.REPO_PATH.rglob('*.py'))
        code_files += list(Config.REPO_PATH.rglob('*.java'))
        
        if not code_files:
            print(f"⚠️  No code files found in: {Config.REPO_PATH}")
            print("    Make sure your repository path is correct.")
            return False
        
        print(f"✓ Found {len(code_files)} code files in repository")
        return True
    except Exception as e:
        print(f"❌ Repository check failed: {e}")
        return False


def main():
    """Run setup checks."""
    print("="*60)
    print("Bug Triage & Analysis System - Setup Check")
    print("="*60)
    
    checks = [
        ("Environment file", check_env_file),
        ("Dependencies", check_dependencies),
        ("Configuration", check_config),
        ("Jira connection", test_jira_connection),
        ("Claude API connection", test_claude_connection),
        ("Repository", check_repository),
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except KeyboardInterrupt:
            print("\n\nSetup check interrupted by user.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Unexpected error during {name}: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*60)
    print("Setup Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓" if result else "❌"
        print(f"{status} {name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if all(results.values()):
        print("\n🎉 All checks passed! You're ready to run the system.")
        print("\nTry running:")
        print("  python main.py")
        print("  or")
        print("  python examples.py")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above before running.")
        sys.exit(1)


if __name__ == "__main__":
    main()
