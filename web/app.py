"""Web interface for Sustenance - Multi-tracker issue management using Flask."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, render_template, request, jsonify
from src.agents.agents import SuperAgent
from src.config import Config

app = Flask(__name__, template_folder='../web/templates')
super_agent = None


@app.route('/')
def index():
    """Home page."""
    try:
        global super_agent
        if not super_agent:
            super_agent = SuperAgent()
        
        agent_info = super_agent.get_agent_info()
        # Get available trackers for display
        available_trackers = [k.upper() for k in ["jira", "tfs", "github"] if k in super_agent.agents]
        tracker_display = ", ".join(available_trackers) if available_trackers else "None"
        return render_template('chat.html', 
                             tracker=tracker_display,
                             agent_info=agent_info)
    except Exception as e:
        return f"Error: {e}", 500


@app.route('/api/bugs', methods=['GET'])
def get_bugs():
    """API endpoint to fetch bugs."""
    try:
        max_results = int(request.args.get('max_results', 10))
        state = request.args.get('state', 'open')
        
        filters = {'max_results': max_results}
        if Config.BUG_TRACKER == "github":
            filters['state'] = state
        elif Config.BUG_TRACKER in ["tfs", "azuredevops"]:
            if state != 'all':
                filters['state'] = [state]
        elif Config.BUG_TRACKER == "jira":
            if state != 'all':
                filters['status'] = [state]
        
        result = super_agent.route("fetch_bugs", **filters)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/bugs/<bug_id>', methods=['GET'])
def get_bug_details(bug_id):
    """API endpoint to get bug details."""
    try:
        result = super_agent.route("get_bug_details", bug_id=bug_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/bugs/<bug_id>/comment', methods=['POST'])
def add_comment(bug_id):
    """API endpoint to add comment."""
    try:
        data = request.get_json()
        comment = data.get('comment', '')
        
        if not comment:
            return jsonify({"success": False, "error": "Comment is required"}), 400
        
        result = super_agent.route("add_comment", bug_id=bug_id, comment=comment)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/bugs/<bug_id>/status', methods=['PUT'])
def update_status(bug_id):
    """API endpoint to update bug status."""
    try:
        data = request.get_json()
        new_status = data.get('status', '')
        
        if not new_status:
            return jsonify({"success": False, "error": "Status is required"}), 400
        
        if Config.BUG_TRACKER == "jira":
            result = super_agent.route("update_status", bug_id=bug_id, new_status=new_status)
        else:
            result = super_agent.route("update_state", bug_id=bug_id, new_state=new_status)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/agent/info', methods=['GET'])
def agent_info():
    """API endpoint to get agent info."""
    try:
        info = super_agent.get_agent_info()
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint for chat messages with streaming support."""
    try:
        data = request.get_json()
        message = data.get('message', '')
        session_id = data.get('session_id', 'default')  # Get session ID from client
        
        if not message:
            return jsonify({"success": False, "message": "Message is required"}), 400
        
        # Check if streaming is requested
        stream = data.get('stream', True)
        
        if stream:
            def generate():
                """Generate streaming response."""
                try:
                    for chunk in super_agent.chat_stream(message, session_id=session_id):
                        yield f"data: {chunk}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    import json
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return app.response_class(
                generate(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no'
                }
            )
        else:
            result = super_agent.chat(message, session_id=session_id)
            return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    """API endpoint to get chat history for a session."""
    try:
        session_id = request.args.get('session_id', 'default')
        history = super_agent.conversation_history.get(session_id, [])
        return jsonify({"success": True, "history": history})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    """API endpoint to clear conversation history."""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id', 'default')
        super_agent.clear_history(session_id)
        return jsonify({"success": True, "message": "Conversation history cleared"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@app.route('/api/chat/sessions', methods=['GET'])
def get_sessions():
    """API endpoint to get all chat sessions."""
    try:
        sessions = super_agent.get_all_sessions()
        return jsonify({"success": True, "sessions": sessions})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/chat/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """API endpoint to delete a chat session."""
    try:
        deleted = super_agent.delete_session(session_id)
        if deleted:
            return jsonify({"success": True, "message": "Session deleted successfully"})
        else:
            return jsonify({"success": False, "message": "Session not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/chat/session/<session_id>/rename', methods=['PUT'])
def rename_session(session_id):
    """API endpoint to rename a chat session."""
    try:
        data = request.json
        new_title = data.get('title', '').strip()
        
        if not new_title:
            return jsonify({"success": False, "message": "Title is required"}), 400
        
        renamed = super_agent.rename_session(session_id, new_title)
        if renamed:
            return jsonify({"success": True, "message": "Session renamed successfully"})
        else:
            return jsonify({"success": False, "message": "Session not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


def main():
    """Run the web server."""
    print("="*70)
    print("SUSTENANCE - WEB INTERFACE")
    print("="*70)
    tracker_display = Config.BUG_TRACKER.upper() if Config.BUG_TRACKER else "DYNAMIC (Claude will decide)"
    print(f"Configured Tracker: {tracker_display}")
    print("\nInitializing Super Agent...")
    
    global super_agent
    try:
        super_agent = SuperAgent()
        print("\n✓ Super Agent initialized successfully!")
        print("\n" + "="*70)
        print("Starting web server...")
        print("Access the interface at: http://localhost:5050")
        print("="*70 + "\n")
        
        app.run(debug=False, host='0.0.0.0', port=5050)
    except Exception as e:
        print(f"\n❌ Failed to start: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
