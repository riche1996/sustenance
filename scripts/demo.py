"""
Demo script to show the bug triaging workflow without Claude API.
This demonstrates Jira integration and report generation with mock analysis.
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.trackers.jira_client import JiraMCPServer
from src.services.code_analyzer import CodeAnalysisAgent
from src.services.report_generator import ReportGenerator
from src.config import Config


def demo_jira_integration():
    """Demonstrate Jira bug fetching."""
    print("\n" + "="*60)
    print("DEMO: Jira Integration")
    print("="*60 + "\n")
    
    jira = JiraMCPServer()
    
    print(f"Fetching bugs from project: {Config.JIRA_PROJECT_KEY}\n")
    bugs = jira.get_bugs(max_results=5)
    
    print(f"\nFound {len(bugs)} bugs:\n")
    for bug in bugs:
        print(f"  {bug.key}: {bug.summary}")
        print(f"    Status: {bug.status}")
        print(f"    Priority: {bug.priority or 'None'}")
        print(f"    Created: {bug.created}")
        print()
    
    return bugs


def demo_repository_scan():
    """Demonstrate repository scanning."""
    print("\n" + "="*60)
    print("DEMO: Repository Scanning")
    print("="*60 + "\n")
    
    analyzer = CodeAnalysisAgent()
    
    print("Scanning repository for code files...\n")
    code_files = analyzer.scan_repository(extensions=['.py', '.java'])
    
    print(f"Found {len(code_files)} code files:\n")
    for file in code_files[:10]:  # Show first 10
        print(f"  - {file.relative_path} ({len(file.content)} bytes)")
    
    if len(code_files) > 10:
        print(f"  ... and {len(code_files) - 10} more files")
    
    return code_files


def demo_mock_analysis(bugs, code_files):
    """Demonstrate analysis with mock data (without Claude API)."""
    print("\n" + "="*60)
    print("DEMO: Mock Bug Analysis")
    print("="*60 + "\n")
    
    print("Note: Using mock analysis data (Claude API unavailable)\n")
    
    analysis_results = []
    
    for bug in bugs[:2]:  # Analyze first 2 bugs
        print(f"\nAnalyzing {bug.key}: {bug.summary}")
        
        # Create mock analysis result
        mock_findings = [
            {
                "file": str(code_files[0].relative_path) if code_files else "example.py",
                "lines": "25-30",
                "issue": f"Potential issue related to: {bug.summary[:50]}",
                "severity": "Medium",
                "resolution": "Review the code logic and add proper error handling",
                "code_fix": "# Add try-except block\ntry:\n    # existing code\nexcept Exception as e:\n    logger.error(f'Error: {e}')"
            }
        ]
        
        result = {
            "bug_key": bug.key,
            "bug_summary": bug.summary,
            "bug_description": bug.description or "No description",
            "bug_status": bug.status,
            "bug_priority": bug.priority,
            "status": "analyzed",
            "total_files_analyzed": len(code_files),
            "findings": mock_findings
        }
        
        analysis_results.append(result)
        print(f"  ✓ Mock analysis complete: {len(mock_findings)} findings")
    
    return analysis_results


def demo_report_generation(analysis_results):
    """Demonstrate report generation."""
    print("\n" + "="*60)
    print("DEMO: Report Generation")
    print("="*60 + "\n")
    
    generator = ReportGenerator()
    
    print("Generating reports...\n")
    report_files = generator.generate_consolidated_report(
        analysis_results=analysis_results,
        format="both"
    )
    
    print("\nGenerated reports:")
    for format_type, path in report_files.items():
        print(f"  {format_type.upper()}: {path}")
        if path.exists():
            size_kb = path.stat().st_size / 1024
            print(f"    Size: {size_kb:.2f} KB")
    
    return report_files


def main():
    """Run the demo."""
    print("\n" + "="*70)
    print(" " * 20 + "BUG TRIAGE SYSTEM DEMO")
    print("="*70)
    
    try:
        # Step 1: Jira Integration
        bugs = demo_jira_integration()
        
        if not bugs:
            print("\n⚠️  No bugs found in Jira. Cannot continue demo.")
            return
        
        # Step 2: Repository Scan
        code_files = demo_repository_scan()
        
        # Step 3: Mock Analysis (without Claude API)
        analysis_results = demo_mock_analysis(bugs, code_files)
        
        # Step 4: Report Generation
        report_files = demo_report_generation(analysis_results)
        
        # Summary
        print("\n" + "="*70)
        print(" " * 25 + "DEMO COMPLETE!")
        print("="*70)
        print(f"\nProcessed {len(bugs)} bugs from Jira")
        print(f"Scanned {len(code_files)} code files")
        print(f"Generated {len(report_files)} reports")
        print("\n✓ All components working successfully!")
        print("\nNote: This demo used mock analysis data.")
        print("With a valid Claude API key, the system will perform real AI-powered analysis.")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
