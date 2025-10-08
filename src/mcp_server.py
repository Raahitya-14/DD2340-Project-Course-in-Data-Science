"""MCP Server for Sionna simulation tools"""
import json
import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent
import sionna_tools

app = Server("sionna-simulator")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="simulate_constellation",
            description="Simulate constellation diagram with AWGN at different SNR levels. Returns constellation points and received symbols.",
            inputSchema={
                "type": "object",
                "properties": {
                    "modulation": {"type": "string", "enum": ["qam", "pam", "psk"], "default": "qam"},
                    "bits_per_symbol": {"type": "integer", "minimum": 1, "maximum": 8, "default": 2},
                    "num_symbols": {"type": "integer", "default": 2000},
                    "snr_db_list": {"type": "array", "items": {"type": "number"}, "default": [-5, 15]}
                },
                "required": []
            }
        ),
        Tool(
            name="simulate_ber",
            description="Simulate Bit Error Rate (BER) for different channels (AWGN, Rayleigh fading) at various SNR levels.",
            inputSchema={
                "type": "object",
                "properties": {
                    "modulation": {"type": "string", "enum": ["qam", "pam", "psk"], "default": "qam"},
                    "bits_per_symbol": {"type": "integer", "minimum": 1, "maximum": 8, "default": 2},
                    "snr_db_list": {"type": "array", "items": {"type": "number"}, "default": [-5, 15]},
                    "num_bits": {"type": "integer", "default": 10000},
                    "channels": {"type": "array", "items": {"type": "string", "enum": ["awgn", "rayleigh"]}, "default": ["awgn", "rayleigh"]}
                },
                "required": []
            }
        ),
        Tool(
            name="list_modulations",
            description="List all available modulation schemes supported by Sionna.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_modulation_info",
            description="Get detailed information about a specific modulation scheme including constellation points.",
            inputSchema={
                "type": "object",
                "properties": {
                    "modulation": {"type": "string", "enum": ["qam", "pam", "psk"], "default": "qam"},
                    "bits_per_symbol": {"type": "integer", "minimum": 1, "maximum": 8, "default": 2}
                },
                "required": []
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "simulate_constellation":
        result = sionna_tools.simulate_constellation(**arguments)
        # Convert numpy arrays to lists for JSON serialization
        result["constellation"] = result["constellation"].tolist()
        for snr in result["snr_levels"]:
            result["snr_levels"][snr] = result["snr_levels"][snr].tolist()
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "simulate_ber":
        result = sionna_tools.simulate_ber(**arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "list_modulations":
        result = sionna_tools.list_available_modulations()
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "get_modulation_info":
        result = sionna_tools.get_modulation_info(**arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
