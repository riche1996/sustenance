"""
Example usage scenarios for the Bug Triage & Analysis System.

This file demonstrates different ways to use the system.
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.main import BugTriageOrchestrator


def example_full_workflow():
    """Example: Run complete workflow with multiple bugs."""
    print("\n=== Example 1: Full Workflow ===\n")
    
    orchestrator = BugTriageOrchestrator()
    
    # Analyze open bugs from Jira
    orchestrator.run(
        project_key=None,  # Uses config default
        status_filter=['Open', 'To Do', 'In Progress'],
        max_bugs=5,
        file_extensions=['.py', '.java', '.js']
    )


def example_single_bug():
    """Example: Analyze a single bug."""
    print("\n=== Example 2: Single Bug Analysis ===\n")
    
    orchestrator = BugTriageOrchestrator()
    
    # Analyze specific bug by key
    orchestrator.analyze_single_bug(
        issue_key='PROJ-123',
        file_extensions=['.py']
    )


def example_python_only():
    """Example: Analyze only Python files."""
    print("\n=== Example 3: Python Files Only ===\n")
    
    orchestrator = BugTriageOrchestrator()
    
    orchestrator.run(
        status_filter=['Open'],
        max_bugs=10,
        file_extensions=['.py']  # Only Python files
    )


def example_high_priority():
    """Example: Focus on high priority bugs."""
    print("\n=== Example 4: High Priority Bugs ===\n")
    
    orchestrator = BugTriageOrchestrator()
    
    # Note: You'll need to modify the JiraMCPServer.get_bugs() method
    # to support priority filtering, or filter results after retrieval
    bugs = orchestrator.jira_mcp.get_bugs(
        status=['Open', 'In Progress'],
        max_results=20
    )
    
    # Filter for high priority
    high_priority_bugs = [b for b in bugs if b.priority in ['Highest', 'High']]
    
    print(f"Found {len(high_priority_bugs)} high priority bugs")
    
    # Analyze each high priority bug
    code_files = orchestrator.code_analyzer.scan_repository()
    analysis_results = []
    
    for bug in high_priority_bugs[:5]:  # Limit to 5
        bug_description = f"""
Summary: {bug.summary}
Description: {bug.description or 'No description'}
Priority: {bug.priority}
        """.strip()
        
        result = orchestrator.code_analyzer.analyze_bug(
            bug_description=bug_description,
            bug_key=bug.key,
            code_files=code_files
        )
        
        result['bug_summary'] = bug.summary
        result['bug_priority'] = bug.priority
        analysis_results.append(result)
    
    # Generate report
    orchestrator.report_generator.generate_consolidated_report(
        analysis_results=analysis_results,
        format='both'
    )


def example_custom_repo_path():
    """Example: Analyze code from a different repository."""
    print("\n=== Example 5: Custom Repository Path ===\n")
    
    import os
    from pathlib import Path
    
    # Temporarily change repo path
    original_path = os.environ.get('REPO_PATH')
    os.environ['REPO_PATH'] = str(Path.cwd() / 'another_project')
    
    # Reload config
    from importlib import reload
    import config
    reload(config)
    
    orchestrator = BugTriageOrchestrator()
    orchestrator.run(max_bugs=3)
    
    # Restore original path
    if original_path:
        os.environ['REPO_PATH'] = original_path


def example_with_jira_updates():
    """Example: Analyze bugs and update Jira with findings."""
    print("\n=== Example 6: Analysis with Jira Updates ===\n")
    
    orchestrator = BugTriageOrchestrator()
    
    # Fetch bugs
    bugs = orchestrator.jira_mcp.get_bugs(
        status=['Open'],
        max_results=3
    )
    
    # Scan repository
    code_files = orchestrator.code_analyzer.scan_repository()
    
    for bug in bugs:
        print(f"\nAnalyzing {bug.key}...")
        
        bug_description = f"""
Summary: {bug.summary}
Description: {bug.description or 'No description'}
        """.strip()
        
        # Analyze
        result = orchestrator.code_analyzer.analyze_bug(
            bug_description=bug_description,
            bug_key=bug.key,
            code_files=code_files
        )
        
        # Generate individual report
        report_path = orchestrator.report_generator.generate_individual_report(
            bug_key=bug.key,
            analysis_result=result
        )
        
        # Add comment to Jira with analysis summary
        findings = result.get('findings', [])
        if findings:
            comment = f"""
AI Analysis Complete:
- Found {len(findings)} potential issues
- Report available at: {report_path}

Top findings:
{chr(10).join([f"- {f.get('file')}: {f.get('issue', '')[:100]}" for f in findings[:3]])}
            """.strip()
            
            orchestrator.jira_mcp.add_comment(bug.key, comment)
            print(f"✓ Added comment to {bug.key}")


if __name__ == "__main__":
    # Uncomment the example you want to run
    
    example_full_workflow()
    
    # example_single_bug()
    
    # example_python_only()
    
    # example_high_priority()
    
    # example_custom_repo_path()
    
    # example_with_jira_updates()
