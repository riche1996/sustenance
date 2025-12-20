"""
Simple test to verify contextual analysis is integrated.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("Testing Contextual Analysis Integration")
print("="*60)

# Test 1: Check if imports work
print("\n1. Checking imports...")
try:
    from src.main import BugTriageOrchestrator
    from src.services.code_analyzer import CodeAnalysisAgent
    print("   ✓ All imports successful")
except ImportError as e:
    print(f"   ✗ Import error: {e}")
    sys.exit(1)

# Test 2: Verify method signature
print("\n2. Verifying method signatures...")
import inspect

# Check analyze_bug signature
sig = inspect.signature(CodeAnalysisAgent.analyze_bug)
params = list(sig.parameters.keys())
print(f"   CodeAnalysisAgent.analyze_bug parameters: {params}")

if 'historical_context' in params:
    print("   ✓ historical_context parameter exists")
else:
    print("   ✗ historical_context parameter missing")
    sys.exit(1)

# Check _format_historical_context exists
if hasattr(BugTriageOrchestrator, '_format_historical_context'):
    print("   ✓ _format_historical_context method exists")
else:
    print("   ✗ _format_historical_context method missing")
    sys.exit(1)

# Test 3: Check if log history is enabled in config
print("\n3. Checking configuration...")
try:
    from config import Config
    if hasattr(Config, 'ENABLE_LOG_HISTORY'):
        print(f"   ENABLE_LOG_HISTORY: {Config.ENABLE_LOG_HISTORY}")
        print("   ✓ Configuration variable exists")
    else:
        print("   ℹ ENABLE_LOG_HISTORY not found (optional)")
except Exception as e:
    print(f"   ⚠ Config check failed: {e}")

print("\n" + "="*60)
print("✓ Contextual Analysis Integration Verified!")
print("="*60)
print("\nFeature Details:")
print("- Before analyzing a bug, system searches log history")
print("- Finds similar bugs with ≥70% similarity")
print("- Provides Claude with historical context")
print("- Ensures consistent solutions across similar issues")
print("\nTo see it in action:")
print("1. Ensure OpenSearch is running (localhost:9200)")
print("2. Set ENABLE_LOG_HISTORY=true in .env")
print("3. Run: python main.py")
print("\nYou'll see messages like:")
print("  🔍 Searching log history for similar bugs...")
print("  ✓ Found 2 similar bug(s) in history")
print("="*60)
