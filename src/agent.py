"""AI Agent for Sionna simulations using MCP"""
import json
import os
import subprocess
import time
import requests
from pathlib import Path
from anthropic import Anthropic

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass

class SionnaAgent:
    def __init__(self, api_key=None):
        self.client = Anthropic(api_key=api_key)
        self.models = [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620", 
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307"
        ]
        self.model = self.models[0]
        self.mcp_server_url = "http://127.0.0.1:5001"
        self.mcp_process = None
        self._start_mcp_server()
    
    def _start_mcp_server(self):
        """Start MCP HTTP server"""
        # Check if already running
        try:
            requests.get(f"{self.mcp_server_url}/tools", timeout=1)
            print("MCP server already running")
            return
        except:
            pass
        
        # Start server
        server_script = str(Path(__file__).parent / 'mcp_http_server.py')
        self.mcp_process = subprocess.Popen(
            ['python3', server_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        for i in range(20):
            try:
                requests.get(f"{self.mcp_server_url}/tools", timeout=1)
                print("MCP server started")
                return
            except:
                time.sleep(0.5)
        
        # Check if process died
        if self.mcp_process.poll() is not None:
            stdout, stderr = self.mcp_process.communicate()
            raise Exception(f"MCP server failed to start. Error: {stderr.decode()}")
        
        raise Exception("Failed to start MCP server - timeout")
    
    def _get_tools_from_mcp(self):
        """Get tools from MCP server"""
        response = requests.get(f"{self.mcp_server_url}/tools")
        return response.json()["tools"]
    
    def run(self, task_description: str) -> dict:
        """Execute a research task described in natural language"""
        
        system_prompt = """You are an expert in wireless communications and Sionna simulations.
You have access to these tools:
1. simulate_constellation - Generate constellation diagrams with AWGN noise
2. simulate_ber - Calculate Bit Error Rate for different channels
3. simulate_radio_map - Generate radio coverage maps using ray tracing

When given a task:
- Identify the modulation scheme (QPSK=2 bits, 16-QAM=4 bits, 64-QAM=6 bits)
- Determine SNR levels to test
- For coverage/propagation tasks, use simulate_radio_map
- Choose appropriate simulation function

Examples:
- "Show 64-QAM at -5 and 15 dB" → simulate_constellation with bits_per_symbol=6
- "Compare QPSK BER in AWGN vs Rayleigh" → simulate_ber with bits_per_symbol=2
- "Generate radio coverage map" → simulate_radio_map
"""
        
        # Get tools from MCP server
        mcp_tools = self._get_tools_from_mcp()
        
        # Convert to Anthropic format
        tools = []
        for tool in mcp_tools:
            tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["inputSchema"]
            })
        
        response = None
        last_error = None
        
        for model in self.models:
            try:
                response = self.client.messages.create(
                    model=model,
                    max_tokens=2000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": task_description}],
                    tools=tools
                )
                self.model = model
                print(f"Using model: {model}")
                break
            except Exception as e:
                last_error = e
                if "not_found_error" in str(e):
                    continue
                else:
                    raise
        
        if response is None:
            raise Exception(f"No available models found. Last error: {last_error}")
        
        result = {"task": task_description, "model": self.model, "tool_calls": []}
        
        for block in response.content:
            if block.type == "tool_use":
                result["tool_calls"].append({
                    "tool": block.name,
                    "parameters": block.input
                })
        
        return result
    
    def execute_tool(self, tool_name: str, parameters: dict):
        """Execute tool via MCP server"""
        response = requests.post(
            f"{self.mcp_server_url}/tools/call",
            json={"name": tool_name, "arguments": parameters}
        )
        
        if response.status_code == 200:
            return response.json()["result"]
        else:
            raise Exception(f"Tool execution failed: {response.json().get('error')}")
    
    def __del__(self):
        """Cleanup MCP server"""
        if self.mcp_process:
            self.mcp_process.terminate()
            self.mcp_process.wait()

def main():
    """Example usage"""
    import os
    
    agent = SionnaAgent(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    tasks = [
        "Simulate 64-QAM constellation at SNR of -5 dB and 15 dB"
    ]
    
    for task in tasks:
        print(f"\n{'='*60}")
        print(f"TASK: {task}")
        print('='*60)
        result = agent.run(task)
        print(json.dumps(result, indent=2))
        
        for tool_call in result["tool_calls"]:
            print(f"\nExecuting {tool_call['tool']}...")
            sim_result = agent.execute_tool(tool_call['tool'], tool_call['parameters'])
            print(f"Result: {sim_result.get('modulation', 'N/A')}")

if __name__ == "__main__":
    main()
