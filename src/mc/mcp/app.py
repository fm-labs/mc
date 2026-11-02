from fastmcp import FastMCP
from fastmcp.server.auth import StaticTokenVerifier, DebugTokenVerifier, TokenVerifier

from mc.config import API_VERSION, DEV_MODE, MC_MCP_TOKEN, MC_MCP_ENABLED
from mc.plugin.containers.mcp import ContainersFastMcpProvider
from mc.plugin.tools.mcp import ToolsFastMcpProvider


class DenyAllTokenVerifier(TokenVerifier):
    def verify_token(self, token):
        return None


if MC_MCP_ENABLED and DEV_MODE:
    verifier = DebugTokenVerifier(
        validate=lambda token: token.startswith("dev-"),
        client_id="development-client",
        scopes=["test:read", "test:write"],
        required_scopes=["test:read"]
    )
elif MC_MCP_ENABLED:
    verifier = StaticTokenVerifier(
        required_scopes=["read"],
        tokens={
            MC_MCP_TOKEN: {
                "client_id": "mcp-client",
                "scopes": ["read",]
            },
        },
    )
else:
    verifier = DenyAllTokenVerifier()


mcp = FastMCP("Mission Control MCP", version=API_VERSION, auth=verifier)
mcp.add_provider(ToolsFastMcpProvider())
mcp.add_provider(ContainersFastMcpProvider())
