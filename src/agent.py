"""AI Agent for Sionna simulations using MCP"""
import os
import json
import asyncio
import requests
import subprocess
import time
from pathlib import Path
from anthropic import Anthropic

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass


class SionnaAgent:
    def __init__(self, api_key=None):
        self.client = Anthropic(api_key=api_key)
        self.models = [
            "claude-3-7-sonnet-20250219",  
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620",
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307",
        ]
        self.model = self.models[0]
        self.system_prompt = """You are an expert in wireless communications and Sionna simulations.

You can answer questions in two ways:
1. General explanation: If the user asks about theory, background knowledge, or clarification, respond directly without tools.
2. Simulation with tools: If the task requires constellation diagrams, BER curves, or radio maps, call the appropriate tool.

Available tools:
- simulate_constellation: Generate constellation diagrams with AWGN noise
- simulate_ber: Calculate Bit Error Rate for different channels
- simulate_radio_map: Generate radio coverage maps using ray tracing

Guidelines:
- Only call a tool if simulation is explicitly required.
- If conceptual, answer in natural language.
- Map schemes: QPSK=2 bits, 16-QAM=4 bits, 64-QAM=6 bits.
- For performance tasks: determine SNR levels.
- For propagation tasks: use simulate_radio_map.
"""
        # MCP HTTP server
        self.mcp_server_url = "http://127.0.0.1:5001"
        self.mcp_process = None
        self._start_mcp_server()
        # cache tools
        self.available_tools = self._get_tools_from_mcp()

    def _start_mcp_server(self):
        """Start MCP HTTP server if not already running"""
        try:
            requests.get(f"{self.mcp_server_url}/tools", timeout=1)
            print("MCP server already running")
            return
        except:
            pass

        server_script = str(Path(__file__).parent / "mcp_http_server.py")
        self.mcp_process = subprocess.Popen(
            ["python", server_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        for _ in range(20):
            try:
                requests.get(f"{self.mcp_server_url}/tools", timeout=1)
                print("MCP server started")
                return
            except:
                time.sleep(0.5)

        if self.mcp_process.poll() is not None:
            stdout, stderr = self.mcp_process.communicate()
            raise Exception(f"MCP server failed to start. Error: {stderr.decode()}")

        raise Exception("Failed to start MCP server - timeout")

    def _get_tools_from_mcp(self):
        """Fetch tool list from MCP server"""
        response = requests.get(f"{self.mcp_server_url}/tools")
        tools = response.json()["tools"]

        # Convert to Anthropic format
        formatted = []
        for tool in tools:
            formatted.append(
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool["inputSchema"],
                }
            )
        return formatted

    async def process_query(self, query: str) -> dict:
        """Process one query and return structured result for UI"""
        messages = [{"role": "user", "content": query}]
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=self.system_prompt,
            messages=messages,
            tools=self.available_tools,
        )

        result = {"task": query, "model": self.model, "tool_calls": []}

        process_query = True
        while process_query:
            assistant_content = []
            for content in response.content:
                if content.type == "text":
                    result["response"] = content.text
                    assistant_content.append(content)
                    if len(response.content) == 1:
                        process_query = False
                elif content.type == "tool_use":
                    result["tool_calls"].append(
                        {"tool": content.name, "parameters": content.input}
                    )
                    assistant_content.append(content)
                    # stop after first tool_use, UI will handle execution
                    process_query = False
            # break loop after one round
            process_query = False

        return result

    def run(self, query: str) -> dict:
        """Synchronous wrapper for Gradio UI"""
        return asyncio.run(self.process_query(query))

    def execute_tool(self, tool_name: str, parameters: dict):
        """Execute tool via MCP HTTP server"""
        response = requests.post(
            f"{self.mcp_server_url}/tools/call",
            json={"name": tool_name, "arguments": parameters},
        )
        if response.status_code == 200:
            return response.json()["result"]
        else:
            raise Exception(
                f"Tool execution failed: {response.json().get('error', 'Unknown error')}"
            )

    def __del__(self):
        if self.mcp_process:
            self.mcp_process.terminate()
            self.mcp_process.wait()


def main():
    agent = SionnaAgent(api_key=os.getenv("ANTHROPIC_API_KEY"))
    tasks = [
        "Simulate 64-QAM constellation at SNR of -5 dB and 15 dB",
        "What is the difference between QPSK and 16-QAM?",
    ]
    for task in tasks:
        print("=" * 60)
        print(f"TASK: {task}")
        print("=" * 60)
        result = agent.run(task)
        print(json.dumps(result, indent=2))
        for tool_call in result["tool_calls"]:
            print(f"\nExecuting {tool_call['tool']}...")
            sim_result = agent.execute_tool(tool_call["tool"], tool_call["parameters"])
            print(f"Result: {sim_result.get('modulation', 'N/A')}")


if __name__ == "__main__":
    main()
