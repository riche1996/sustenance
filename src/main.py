"""Main orchestration workflow for bug triaging and analysis."""
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
from config import Config
from jira_mcp import JiraMCPServer, JiraIssue
from code_analyzer import CodeAnalysisAgent, CodeFile
from report_generator import ReportGenerator
from log_history_manager import LogHistoryManager


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
        
        # Initialize log history manager (if enabled)
        self.log_history = None
        if Config.ENABLE_LOG_HISTORY:
            try:
                self.log_history = LogHistoryManager(
                    opensearch_host=Config.OPENSEARCH_HOST,
                    opensearch_port=Config.OPENSEARCH_PORT,
                    index_name=Config.OPENSEARCH_INDEX,
                    embedding_model=Config.EMBEDDING_MODEL
                )
                print("✓ Log History enabled (OpenSearch + Embeddings)\n")
            except Exception as e:
                print(f"⚠ Warning: Could not initialize log history: {e}")
                print("  Continuing without log history...\n")
                self.log_history = None
    
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
            
            # Search for similar bugs in history (if enabled)
            # Similarity Thresholds:
            #   - min_score=0.7 (70%): Minimum similarity to provide context to Claude
            #   - >0.90 (90%): Duplicate threshold - bugs this similar won't be re-logged
            historical_context = None
            if self.log_history:
                try:
                    print("  🔍 Searching log history for similar bugs...")
                    similar_bugs = self.log_history.search_similar_bugs(
                        query=f"{bug.summary} {bug.description or ''}",
                        limit=3,
                        min_score=0.7  # Context threshold: Include bugs ≥70% similar
                    )
                    if similar_bugs:
                        print(f"  ✓ Found {len(similar_bugs)} similar bug(s) in history")
                        historical_context = self._format_historical_context(similar_bugs)
                    else:
                        print("  ℹ No similar bugs found in history")
                except Exception as e:
                    print(f"  ⚠ Warning: Could not search history: {e}")
            
            # Analyze the bug with historical context
            analysis_result = self.code_analyzer.analyze_bug(
                bug_description=bug_description,
                bug_key=bug.key,
                code_files=code_files,
                historical_context=historical_context
            )
            
            # Add bug metadata to result
            analysis_result['bug_summary'] = bug.summary
            analysis_result['bug_description'] = bug.description
            analysis_result['bug_status'] = bug.status
            analysis_result['bug_priority'] = bug.priority
            
            analysis_results.append(analysis_result)
            
            # Log to history (if enabled and not a duplicate)
            if self.log_history:
                try:
                    # Duplicate Detection: Bugs with >90% similarity are not re-logged
                    # to prevent redundant entries in log history.
                    # Analysis and reporting still proceed normally; only logging is skipped.
                    if similar_bugs and len(similar_bugs) > 0:
                        highest_similarity = similar_bugs[0].get('score', 0)
                        if highest_similarity > 0.90:  # Duplicate threshold
                            similar_bug_id = similar_bugs[0].get('bug_id', 'existing bug')
                            print(f"  ⚠ Skipping log: Bug is {highest_similarity:.1%} similar to {similar_bug_id} (likely duplicate)")
                        else:
                            files_analyzed = [f.relative_path for f in code_files]
                            self.log_history.log_analysis(
                                bug=bug,
                                analysis_result=analysis_result,
                                files_analyzed=files_analyzed,
                                metadata={'workflow': 'batch_analysis'}
                            )
                            print("  ✓ Analysis logged to history")
                    else:
                        # No similar bugs found, log this new analysis
                        files_analyzed = [f.relative_path for f in code_files]
                        self.log_history.log_analysis(
                            bug=bug,
                            analysis_result=analysis_result,
                            files_analyzed=files_analyzed,
                            metadata={'workflow': 'batch_analysis'}
                        )
                        print("  ✓ Analysis logged to history")
                except Exception as e:
                    print(f"  ⚠ Warning: Could not log to history: {e}")
            
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
        
        # Search for similar bugs in history (if enabled)
        # Similarity Thresholds:
        #   - min_score=0.7 (70%): Minimum similarity to provide context to Claude
        #   - >0.90 (90%): Duplicate threshold - bugs this similar won't be re-logged
        historical_context = None
        if self.log_history:
            try:
                print("\n🔍 Searching log history for similar bugs...")
                similar_bugs = self.log_history.search_similar_bugs(
                    query=f"{bug.summary} {bug.description or ''}",
                    limit=3,
                    min_score=0.7  # Context threshold: Include bugs ≥70% similar
                )
                if similar_bugs:
                    print(f"✓ Found {len(similar_bugs)} similar bug(s) in history")
                    historical_context = self._format_historical_context(similar_bugs)
                else:
                    print("ℹ No similar bugs found in history")
            except Exception as e:
                print(f"⚠ Warning: Could not search history: {e}")
        
        # Analyze with historical context
        analysis_result = self.code_analyzer.analyze_bug(
            bug_description=bug_description,
            bug_key=bug.key,
            code_files=code_files,
            historical_context=historical_context
        )
        
        # Add metadata
        analysis_result['bug_summary'] = bug.summary
        analysis_result['bug_description'] = bug.description
        analysis_result['bug_status'] = bug.status
        analysis_result['bug_priority'] = bug.priority
        
        # Log to history (if enabled and not a duplicate)
        if self.log_history:
            try:
                # Duplicate Detection: Bugs with >90% similarity are not re-logged
                # to prevent redundant entries in log history.
                # Analysis and reporting still proceed normally; only logging is skipped.
                should_log = True
                if 'similar_bugs' in locals() and similar_bugs and len(similar_bugs) > 0:
                    highest_similarity = similar_bugs[0].get('score', 0)
                    if highest_similarity > 0.90:  # Duplicate threshold
                        similar_bug_id = similar_bugs[0].get('bug_id', 'existing bug')
                        print(f"\n⚠ Skipping log: Bug is {highest_similarity:.1%} similar to {similar_bug_id} (likely duplicate)")
                        should_log = False
                
                if should_log:
                    files_analyzed = [f.relative_path for f in code_files]
                    self.log_history.log_analysis(
                        bug=bug,
                        analysis_result=analysis_result,
                        files_analyzed=files_analyzed,
                        metadata={'workflow': 'single_bug_analysis'}
                    )
                    print("\n✓ Analysis logged to history")
            except Exception as e:
                print(f"\n⚠ Warning: Could not log to history: {e}")
        
        # Generate report
        print("\nGenerating report...")
        report_path = self.report_generator.generate_individual_report(
            bug_key=issue_key,
            analysis_result=analysis_result
        )
        
        print(f"\n✓ Report generated: {report_path}")
    
    def _format_historical_context(self, similar_bugs: List[Dict[str, Any]]) -> str:
        """
        Format historical bug analyses into context for Claude.
        
        Args:
            similar_bugs: List of similar bug analyses from history
            
        Returns:
            Formatted string with historical context
        """
        if not similar_bugs:
            return ""
        
        context_parts = ["\n\n=== HISTORICAL CONTEXT: Similar Bugs Previously Analyzed ==="]
        
        for idx, bug in enumerate(similar_bugs, 1):
            score = bug.get('score', 0)
            
            context_parts.append(f"\n--- Similar Bug #{idx} (Similarity: {score:.2%}) ---")
            context_parts.append(f"Bug ID: {bug.get('bug_id', 'N/A')}")
            context_parts.append(f"Summary: {bug.get('bug_summary', 'N/A')}")
            context_parts.append(f"Status: {bug.get('bug_status', 'N/A')}")
            context_parts.append(f"Priority: {bug.get('bug_priority', 'N/A')}")
            
            # Include findings if available
            findings = bug.get('findings', [])
            if findings:
                context_parts.append(f"\nFindings ({len(findings)} total):")
                for f_idx, finding in enumerate(findings[:2], 1):  # Show max 2 findings
                    context_parts.append(f"  {f_idx}. File: {finding.get('file', 'N/A')}")
                    context_parts.append(f"     Issue: {finding.get('issue', 'N/A')}")
                    context_parts.append(f"     Resolution: {finding.get('resolution', 'N/A')}")
                    if finding.get('code_fix'):
                        context_parts.append(f"     Code Fix: {finding.get('code_fix', 'N/A')}")
            
        context_parts.append("\n=== END OF HISTORICAL CONTEXT ===\n")
        context_parts.append("Note: Use the above similar bugs as reference for consistent solutions, but adapt to the current bug's specific context.\n")
        
        return "\n".join(context_parts)


def main():
    """Main entry point."""
    orchestrator = BugTriageOrchestrator()
    
    # Example: Run full workflow
    # Uncomment and customize as needed
    orchestrator.run(
        status_filter=['Open', 'In Progress', 'To Do'],
        max_bugs=1,  # Test with just 1 bug
        file_extensions=['.py', '.java']
    )
    
    # Example: Analyze a single bug
    # orchestrator.analyze_single_bug('PROJ-123')


if __name__ == "__main__":
    main()
