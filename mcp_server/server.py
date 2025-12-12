from mcp_server import Server
from tools.filesystem import register_filesystem_tools

server = Server("code_context_server")

# Register your code-context tools
register_filesystem_tools(server)

if __name__ == "__main__":
    server.run()
