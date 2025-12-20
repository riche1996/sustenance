"""Simple CLI interface for bug tracker agents."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.agents import SuperAgent
from src.config import Config
import json


class BugTrackerCLI:
    """Command-line interface for bug tracker agents."""
    
    def __init__(self):
        """Initialize CLI and super agent."""
        print("="*70)
        print("BUG TRACKER AGENT SYSTEM")
        print("="*70)
        print(f"\nConfigured Tracker: {Config.BUG_TRACKER.upper()}\n")
        
        try:
            self.super_agent = SuperAgent()
            self.running = True
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            sys.exit(1)
    
    def display_menu(self):
        """Display main menu."""
        print("\n" + "="*70)
        print("MAIN MENU")
        print("="*70)
        print("1. Fetch Bugs")
        print("2. Get Bug Details")
        print("3. Add Comment to Bug")
        print("4. Update Bug Status/State")
        print("5. Show Available Actions")
        print("6. Show Agent Info")
        print("0. Exit")
        print("="*70)
    
    def fetch_bugs(self):
        """Fetch bugs from tracker."""
        print("\n" + "-"*70)
        print("FETCH BUGS")
        print("-"*70)
        
        max_results = input("Number of bugs to fetch (default 10): ").strip()
        max_results = int(max_results) if max_results else 10
        
        # Get tracker-specific filters
        filters = {}
        if Config.BUG_TRACKER == "jira":
            status = input("Filter by status (leave empty for all): ").strip()
            if status:
                filters['status'] = status.split(',')
        elif Config.BUG_TRACKER in ["tfs", "azuredevops"]:
            state = input("Filter by state (leave empty for all): ").strip()
            if state:
                filters['state'] = state.split(',')
        elif Config.BUG_TRACKER == "github":
            state = input("State (open/closed/all, default open): ").strip() or "open"
            filters['state'] = state
        
        print("\n🔄 Fetching bugs...")
        result = self.super_agent.route("fetch_bugs", max_results=max_results, **filters)
        
        if result['success']:
            print(f"\n✓ Found {result['count']} bugs:\n")
            for i, bug in enumerate(result['data'], 1):
                print(f"{i}. [{bug['id']}] {bug['title']}")
                print(f"   Status: {bug.get('status') or bug.get('state')}")
                if bug.get('priority'):
                    print(f"   Priority: {bug['priority']}")
                print()
        else:
            print(f"\n❌ Error: {result['error']}")
    
    def get_bug_details(self):
        """Get details of a specific bug."""
        print("\n" + "-"*70)
        print("GET BUG DETAILS")
        print("-"*70)
        
        bug_id = input("Enter bug ID/number: ").strip()
        if not bug_id:
            print("❌ Bug ID is required")
            return
        
        print("\n🔄 Fetching bug details...")
        result = self.super_agent.route("get_bug_details", bug_id=bug_id)
        
        if result['success']:
            bug = result['data']
            print("\n" + "="*70)
            print(f"BUG DETAILS: {bug['id']}")
            print("="*70)
            print(f"Title: {bug['title']}")
            print(f"Status: {bug.get('status') or bug.get('state')}")
            if bug.get('priority'):
                print(f"Priority: {bug['priority']}")
            if bug.get('assignee'):
                print(f"Assignee: {bug['assignee']}")
            if bug.get('labels'):
                print(f"Labels: {', '.join(bug['labels'])}")
            print(f"Created: {bug['created']}")
            if bug.get('url'):
                print(f"URL: {bug['url']}")
            print(f"\nDescription:")
            print("-"*70)
            print(bug['description'] or "No description")
            print("="*70)
        else:
            print(f"\n❌ Error: {result['error']}")
    
    def add_comment(self):
        """Add comment to a bug."""
        print("\n" + "-"*70)
        print("ADD COMMENT")
        print("-"*70)
        
        bug_id = input("Enter bug ID/number: ").strip()
        if not bug_id:
            print("❌ Bug ID is required")
            return
        
        print("Enter comment (press Enter twice to finish):")
        lines = []
        while True:
            line = input()
            if not line and lines:
                break
            lines.append(line)
        
        comment = '\n'.join(lines)
        if not comment:
            print("❌ Comment cannot be empty")
            return
        
        print("\n🔄 Adding comment...")
        result = self.super_agent.route("add_comment", bug_id=bug_id, comment=comment)
        
        if result['success']:
            print(f"\n✓ {result['message']}")
        else:
            print(f"\n❌ Error: {result['error']}")
    
    def update_status(self):
        """Update bug status/state."""
        print("\n" + "-"*70)
        print("UPDATE BUG STATUS/STATE")
        print("-"*70)
        
        bug_id = input("Enter bug ID/number: ").strip()
        if not bug_id:
            print("❌ Bug ID is required")
            return
        
        if Config.BUG_TRACKER == "jira":
            new_status = input("Enter new status (e.g., In Progress, Done): ").strip()
            action_key = "new_status"
            action = "update_status"
        elif Config.BUG_TRACKER in ["tfs", "azuredevops"]:
            new_status = input("Enter new state (e.g., Active, Resolved, Closed): ").strip()
            action_key = "new_state"
            action = "update_state"
        elif Config.BUG_TRACKER == "github":
            new_status = input("Enter new state (open/closed): ").strip()
            action_key = "new_state"
            action = "update_state"
        else:
            print("❌ Unknown tracker type")
            return
        
        if not new_status:
            print("❌ Status/state is required")
            return
        
        print(f"\n🔄 Updating {action.replace('_', ' ')}...")
        result = self.super_agent.route(action, bug_id=bug_id, **{action_key: new_status})
        
        if result['success']:
            print(f"\n✓ {result['message']}")
        else:
            print(f"\n❌ Error: {result['error']}")
    
    def show_available_actions(self):
        """Show all available actions."""
        print("\n" + "-"*70)
        print("AVAILABLE ACTIONS")
        print("-"*70)
        
        actions = self.super_agent.get_available_actions()
        for i, action in enumerate(actions, 1):
            print(f"{i}. {action}")
    
    def show_agent_info(self):
        """Show agent information."""
        print("\n" + "-"*70)
        print("AGENT INFORMATION")
        print("-"*70)
        
        info = self.super_agent.get_agent_info()
        if 'error' in info:
            print(f"❌ {info['error']}")
        else:
            print(f"Agent Name: {info['name']}")
            print(f"Tracker Type: {info['tracker'].upper()}")
            print(f"\nCapabilities:")
            for cap in info['capabilities']:
                print(f"  - {cap}")
    
    def run(self):
        """Run the CLI."""
        while self.running:
            self.display_menu()
            choice = input("\nSelect an option: ").strip()
            
            if choice == "1":
                self.fetch_bugs()
            elif choice == "2":
                self.get_bug_details()
            elif choice == "3":
                self.add_comment()
            elif choice == "4":
                self.update_status()
            elif choice == "5":
                self.show_available_actions()
            elif choice == "6":
                self.show_agent_info()
            elif choice == "0":
                print("\n👋 Goodbye!")
                self.running = False
            else:
                print("\n❌ Invalid option. Please try again.")
            
            if self.running:
                input("\nPress Enter to continue...")


def main():
    """Main entry point."""
    try:
        cli = BugTrackerCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
