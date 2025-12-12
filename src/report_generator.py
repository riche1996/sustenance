"""Report generation for bug analysis results."""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from config import Config


class ReportGenerator:
    """Generate reports from bug analysis results."""
    
    def __init__(self, output_dir: Path = None):
        """
        Initialize the report generator.
        
        Args:
            output_dir: Directory to save reports (default from config)
        """
        self.output_dir = output_dir or Config.REPORT_OUTPUT_PATH
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_consolidated_report(
        self,
        analysis_results: List[Dict[str, Any]],
        format: str = "both"
    ) -> Dict[str, Path]:
        """
        Generate a consolidated report from all analysis results.
        
        Args:
            analysis_results: List of analysis result dictionaries
            format: Output format - 'json', 'markdown', or 'both'
            
        Returns:
            Dictionary with report file paths
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_files = {}
        
        # Generate JSON report
        if format in ["json", "both"]:
            json_path = self.output_dir / f"bug_analysis_report_{timestamp}.json"
            self._generate_json_report(analysis_results, json_path)
            report_files["json"] = json_path
            print(f"✓ JSON report saved: {json_path}")
        
        # Generate Markdown report
        if format in ["markdown", "both"]:
            md_path = self.output_dir / f"bug_analysis_report_{timestamp}.md"
            self._generate_markdown_report(analysis_results, md_path)
            report_files["markdown"] = md_path
            print(f"✓ Markdown report saved: {md_path}")
        
        return report_files
    
    def _generate_json_report(self, analysis_results: List[Dict[str, Any]], output_path: Path):
        """Generate JSON format report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_bugs_analyzed": len(analysis_results),
            "summary": self._generate_summary(analysis_results),
            "detailed_results": analysis_results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    
    def _generate_markdown_report(self, analysis_results: List[Dict[str, Any]], output_path: Path):
        """Generate Markdown format report."""
        lines = []
        
        # Header
        lines.append("# Bug Analysis Report")
        lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"\n**Total Bugs Analyzed:** {len(analysis_results)}\n")
        
        # Summary
        summary = self._generate_summary(analysis_results)
        lines.append("## Summary\n")
        lines.append(f"- **Bugs with Findings:** {summary['bugs_with_findings']}")
        lines.append(f"- **Total Files Analyzed:** {summary['total_files_analyzed']}")
        lines.append(f"- **Total Issues Found:** {summary['total_issues_found']}")
        
        # Severity breakdown
        if summary['severity_breakdown']:
            lines.append("\n### Severity Breakdown\n")
            for severity, count in summary['severity_breakdown'].items():
                lines.append(f"- **{severity}:** {count}")
        
        lines.append("\n---\n")
        
        # Detailed Results
        lines.append("## Detailed Analysis\n")
        
        for idx, result in enumerate(analysis_results, 1):
            bug_key = result.get('bug_key', 'UNKNOWN')
            bug_summary = result.get('bug_summary', 'No summary')
            status = result.get('status', 'unknown')
            
            lines.append(f"### {idx}. {bug_key}: {bug_summary}\n")
            lines.append(f"**Status:** {status}\n")
            
            if result.get('bug_description'):
                lines.append(f"**Description:**\n```\n{result['bug_description']}\n```\n")
            
            findings = result.get('findings', [])
            
            if findings:
                lines.append(f"**Issues Found:** {len(findings)}\n")
                
                for finding_idx, finding in enumerate(findings, 1):
                    lines.append(f"#### Finding {finding_idx}\n")
                    lines.append(f"- **File:** `{finding.get('file', 'N/A')}`")
                    lines.append(f"- **Lines:** {finding.get('lines', 'N/A')}")
                    lines.append(f"- **Severity:** {finding.get('severity', 'Unknown')}")
                    lines.append(f"- **Issue:** {finding.get('issue', 'No description')}")
                    lines.append(f"- **Resolution:** {finding.get('resolution', 'No resolution provided')}")
                    
                    if finding.get('code_fix'):
                        lines.append(f"\n**Code Fix:**\n```\n{finding['code_fix']}\n```\n")
                    else:
                        lines.append("")
            else:
                lines.append("**No specific issues identified in the analyzed code.**\n")
            
            lines.append("---\n")
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def _generate_summary(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics from analysis results."""
        total_files = 0
        total_issues = 0
        bugs_with_findings = 0
        severity_breakdown = {}
        
        for result in analysis_results:
            total_files += result.get('total_files_analyzed', 0)
            findings = result.get('findings', [])
            
            if findings:
                bugs_with_findings += 1
                total_issues += len(findings)
                
                for finding in findings:
                    severity = finding.get('severity', 'Unknown')
                    severity_breakdown[severity] = severity_breakdown.get(severity, 0) + 1
        
        return {
            "bugs_with_findings": bugs_with_findings,
            "total_files_analyzed": total_files,
            "total_issues_found": total_issues,
            "severity_breakdown": severity_breakdown
        }
    
    def generate_individual_report(
        self,
        bug_key: str,
        analysis_result: Dict[str, Any]
    ) -> Path:
        """
        Generate a report for a single bug analysis.
        
        Args:
            bug_key: Jira issue key
            analysis_result: Analysis result dictionary
            
        Returns:
            Path to the generated report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"{bug_key}_{timestamp}.md"
        
        self._generate_markdown_report([analysis_result], report_path)
        
        return report_path
