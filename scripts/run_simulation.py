#!/usr/bin/env python3
"""Run simulations based on agent output"""
import sys
import os
import json
sys.path.insert(0, 'src')

from src.agent import SionnaAgent
from src.sionna_tools import simulate_constellation, simulate_ber

def execute_tool_call(tool_name, parameters):
    """Execute a tool call and return results"""
    if tool_name == "simulate_constellation":
        return simulate_constellation(**parameters)
    elif tool_name == "simulate_ber":
        return simulate_ber(**parameters)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")

def main():
    agent = SionnaAgent(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Get task from command line or use default
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = "Simulate 64-QAM constellation at -5 and 15 dB SNR"
    
    print(f"\n{'='*60}")
    print(f"TASK: {task}")
    print('='*60)
    
    # Get tool calls from agent
    result = agent.run(task)
    print(f"\nAgent interpretation:")
    print(json.dumps(result, indent=2))
    
    # Execute tool calls
    print(f"\n{'='*60}")
    print("EXECUTING SIMULATIONS")
    print('='*60)
    
    for i, tool_call in enumerate(result["tool_calls"], 1):
        print(f"\n[{i}] Running {tool_call['tool']}...")
        sim_result = execute_tool_call(tool_call['tool'], tool_call['parameters'])
        print(f"Complete: {sim_result.get('modulation', 'N/A')}")
        
        # Show summary
        if 'ber' in sim_result:
            print(f"  BER results: {list(sim_result['ber'].keys())}")
        elif 'snr_levels' in sim_result:
            print(f"  SNR levels: {list(sim_result['snr_levels'].keys())}")
    
    print(f"\n{'='*60}")
    print("All simulations complete!")
    print('='*60)

if __name__ == "__main__":
    main()
