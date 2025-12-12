"""Main orchestration workflow for bug triaging and analysis."""
import sys
from pathlib import Path
from typing import List, Optional
from config import Config
from jira_mcp import JiraMCPServer, JiraIssue
from code_analyzer import CodeAnalysisAgent, CodeFile
from report_generator import ReportGenerator


class BugTriageOrchestrator:
    """Orchestrates the bug triaging and analysis workflow."""
    
    def __init__(self):
        """Initialize the orchestrator."""
        print("\n" + "="*60)
        print("Bug Triage & Analysis System")
        print("="*60 + "\n")
        
        # Validate configuration
        try:
            Config.validate()
            print("✓ Configuration validated\n")
        except ValueError as e:
            print(f"❌ Configuration error: {e}")
            print("\nPlease create a .env file based on .env.example")
            sys.exit(1)
        
        # Initialize components
        self.jira_mcp = JiraMCPServer()
        self.code_analyzer = CodeAnalysisAgent()
        self.report_generator = ReportGenerator()
    
    def run(
        self,
        project_key: Optional[str] = None,
        status_filter: Optional[List[str]] = None,
        max_bugs: int = 10,
        file_extensions: Optional[List[str]] = None
    ):
        """
        Run the complete bug triaging workflow.
        
        Args:
            project_key: Jira project key (default from config)
            status_filter: List of bug statuses to process
            max_bugs: Maximum number of bugs to process
            file_extensions: File extensions to analyze
        """
        print(f"Starting bug triage workflow...")
        print(f"Project: {project_key or Config.JIRA_PROJECT_KEY}")
        print(f"Status Filter: {status_filter or 'All'}")
        print(f"Max Bugs: {max_bugs}\n")
        
        # Step 1: Scan repository
        print("Step 1: Scanning repository for code files...")
        code_files = self.code_analyzer.scan_repository(extensions=file_extensions)
        
        if not code_files:
            print("❌ No code files found in repository. Exiting.")
            return
        
        # Step 2: Fetch bugs from Jira
        print("\nStep 2: Fetching bugs from Jira...")
        try:
            bugs = self.jira_mcp.get_bugs(
                project_key=project_key,
                status=status_filter,
                max_results=max_bugs
            )
        except Exception as e:
            print(f"❌ Failed to fetch bugs: {e}")
            return
        
        if not bugs:
            print("No bugs found matching the criteria.")
            return
        
        # Step 3: Analyze each bug
        print(f"\nStep 3: Analyzing {len(bugs)} bugs...")
        analysis_results = []
        
        for idx, bug in enumerate(bugs, 1):
            print(f"\n{'='*60}")
            print(f"Bug {idx}/{len(bugs)}: {bug.key}")
            print(f"{'='*60}")
            print(f"Summary: {bug.summary}")
            print(f"Status: {bug.status}")
            print(f"Priority: {bug.priority or 'N/A'}")
            
            # Prepare bug description
            bug_description = f"""
Summary: {bug.summary}
Description: {bug.description or 'No description provided'}
Priority: {bug.priority or 'N/A'}
Status: {bug.status}
Labels: {', '.join(bug.labels) if bug.labels else 'None'}
            """.strip()
            
            # Analyze the bug
            analysis_result = self.code_analyzer.analyze_bug(
                bug_description=bug_description,
                bug_key=bug.key,
                code_files=code_files
            )
            
            # Add bug metadata to result
            analysis_result['bug_summary'] = bug.summary
            analysis_result['bug_description'] = bug.description
            analysis_result['bug_status'] = bug.status
            analysis_result['bug_priority'] = bug.priority
            
            analysis_results.append(analysis_result)
            
            # Show summary
            findings_count = len(analysis_result.get('findings', []))
            print(f"\n✓ Analysis complete: {findings_count} findings")
        
        # Step 4: Generate consolidated report
        print(f"\n{'='*60}")
        print("Step 4: Generating consolidated report...")
        print(f"{'='*60}\n")
        
        report_files = self.report_generator.generate_consolidated_report(
            analysis_results=analysis_results,
            format="both"
        )
        
        # Final summary
        print(f"\n{'='*60}")
        print("Workflow Complete!")
        print(f"{'='*60}")
        print(f"\nTotal bugs analyzed: {len(bugs)}")
        print(f"Total code files scanned: {len(code_files)}")
        print(f"\nReports generated:")
        for format_type, path in report_files.items():
            print(f"  - {format_type.upper()}: {path}")
        print()
    
    def analyze_single_bug(
        self,
        issue_key: str,
        file_extensions: Optional[List[str]] = None
    ):
        """
        Analyze a single bug by its issue key.
        
        Args:
            issue_key: Jira issue key (e.g., 'PROJ-123')
            file_extensions: File extensions to analyze
        """
        print(f"\nAnalyzing single bug: {issue_key}\n")
        
        # Scan repository
        print("Scanning repository...")
        code_files = self.code_analyzer.scan_repository(extensions=file_extensions)
        
        if not code_files:
            print("❌ No code files found in repository.")
            return
        
        # Fetch the specific bug
        print(f"Fetching bug {issue_key} from Jira...")
        try:
            bug = self.jira_mcp.get_issue(issue_key)
        except Exception as e:
            print(f"❌ Failed to fetch bug: {e}")
            return
        
        print(f"\nBug Details:")
        print(f"Summary: {bug.summary}")
        print(f"Status: {bug.status}")
        print(f"Priority: {bug.priority or 'N/A'}")
        
        # Prepare bug description
        bug_description = f"""
Summary: {bug.summary}
Description: {bug.description or 'No description provided'}
Priority: {bug.priority or 'N/A'}
Status: {bug.status}
        """.strip()
        
        # Analyze
        analysis_result = self.code_analyzer.analyze_bug(
            bug_description=bug_description,
            bug_key=bug.key,
            code_files=code_files
        )
        
        # Add metadata
        analysis_result['bug_summary'] = bug.summary
        analysis_result['bug_description'] = bug.description
        analysis_result['bug_status'] = bug.status
        analysis_result['bug_priority'] = bug.priority
        
        # Generate report
        print("\nGenerating report...")
        report_path = self.report_generator.generate_individual_report(
            bug_key=issue_key,
            analysis_result=analysis_result
        )
        
        print(f"\n✓ Report generated: {report_path}")


def main():
    """Main entry point."""
    orchestrator = BugTriageOrchestrator()
    
    # Example: Run full workflow
    # Uncomment and customize as needed
    orchestrator.run(
        status_filter=['Open', 'In Progress', 'To Do'],
        max_bugs=5,
        file_extensions=['.py', '.java']
    )
    
    # Example: Analyze a single bug
    # orchestrator.analyze_single_bug('PROJ-123')


if __name__ == "__main__":
    main()
