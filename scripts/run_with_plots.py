#!/usr/bin/env python3
"""Run simulations and generate plots"""
import sys
import os
import json
import matplotlib.pyplot as plt
sys.path.insert(0, 'src')

from src.agent import SionnaAgent
from src.sionna_tools import simulate_constellation, simulate_ber

def plot_constellation(result, filename):
    """Plot constellation diagram"""
    ideal = result['constellation']
    snr_levels = result['snr_levels']
    
    fig, axes = plt.subplots(1, len(snr_levels), figsize=(6*len(snr_levels), 5))
    if len(snr_levels) == 1:
        axes = [axes]
    
    for ax, (snr, rx) in zip(axes, snr_levels.items()):
        ax.scatter(rx.real, rx.imag, s=10, alpha=0.6, label='Received')
        ax.scatter(ideal.real, ideal.imag, s=100, facecolors='none', 
                  edgecolors='red', linewidths=2, label='Ideal')
        ax.set_title(f"{result['modulation']} at SNR={snr} dB")
        ax.set_xlabel("In-phase (I)")
        ax.set_ylabel("Quadrature (Q)")
        ax.grid(True)
        ax.legend()
        ax.axhline(0, ls='--', c='gray')
        ax.axvline(0, ls='--', c='gray')
    
    plt.tight_layout()
    plt.savefig(f"outputs/{filename}")
    print(f"Saved plot: outputs/{filename}")

def plot_ber(result, filename):
    """Plot BER curves"""
    snr_list = sorted(result['ber'].keys())
    
    plt.figure(figsize=(8, 6))
    for channel in ['awgn', 'rayleigh']:
        ber_values = [result['ber'][snr].get(channel) for snr in snr_list]
        if any(v is not None for v in ber_values):
            ber_values = [v for v in ber_values if v is not None]
            plt.semilogy(snr_list[:len(ber_values)], ber_values, 'o-', label=channel.upper())
    
    plt.xlabel("SNR (dB)")
    plt.ylabel("Bit Error Rate (BER)")
    plt.title(f"{result['modulation']} BER Performance")
    plt.grid(True, which='both')
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"outputs/{filename}")
    print(f"Saved plot: outputs/{filename}")

def main():
    agent = SionnaAgent(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = "Simulate 64-QAM constellation at -5 and 15 dB SNR"
    
    print(f"\n{'='*60}")
    print(f"TASK: {task}")
    print('='*60)
    
    result = agent.run(task)
    print(f"\nAgent interpretation complete")
    
    print(f"\n{'='*60}")
    print("EXECUTING SIMULATIONS")
    print('='*60)
    
    for i, tool_call in enumerate(result["tool_calls"], 1):
        print(f"\n[{i}] Running {tool_call['tool']}...")
        sim_result = execute_and_plot(tool_call, i)
        print(f"Complete: {sim_result.get('modulation', 'N/A')}")
    
    print(f"\n{'='*60}")
    print("All simulations complete!")
    print(f"Check outputs/ directory for plots")
    print('='*60)

def execute_and_plot(tool_call, index):
    """Execute tool and generate plot"""
    tool_name = tool_call['tool']
    params = tool_call['parameters']
    
    if tool_name == "simulate_constellation":
        result = simulate_constellation(**params)
        filename = f"constellation_{index}.png"
        plot_constellation(result, filename)
        return result
    
    elif tool_name == "simulate_ber":
        result = simulate_ber(**params)
        filename = f"ber_{index}.png"
        plot_ber(result, filename)
        return result
    
    else:
        raise ValueError(f"Unknown tool: {tool_name}")

if __name__ == "__main__":
    main()
