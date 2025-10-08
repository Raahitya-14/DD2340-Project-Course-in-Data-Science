#!/usr/bin/env python3
"""Simple chat interface for Sionna AI Agent"""
import sys
import os
import json
import gradio as gr
import matplotlib.pyplot as plt
sys.path.insert(0, 'src')

from src.agent import SionnaAgent
from src.sionna_tools import simulate_constellation, simulate_ber

# Initialize agent
agent = SionnaAgent(api_key=os.getenv("ANTHROPIC_API_KEY"))

def plot_constellation(result):
    """Generate constellation plot"""
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
    return fig

def plot_ber(result):
    """Generate BER plot"""
    snr_list = sorted(result['ber'].keys())
    
    fig = plt.figure(figsize=(8, 6))
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
    return fig

def process_message(message, history):
    """Process user message and return response with plot"""
    try:
        # Get agent interpretation
        result = agent.run(message)
        
        response = f"**Understanding:** {result['task']}\n\n"
        response += f"**Model:** {result['model']}\n\n"
        
        # Execute simulations
        plots = []
        for tool_call in result["tool_calls"]:
            tool_name = tool_call['tool']
            params = tool_call['parameters']
            
            response += f"**Tool:** {tool_name}\n"
            response += f"**Parameters:** {json.dumps(params, indent=2)}\n\n"
            
            if tool_name == "simulate_constellation":
                sim_result = simulate_constellation(**params)
                response += f"Generated {sim_result['modulation']} constellation\n"
                plots.append(plot_constellation(sim_result))
            
            elif tool_name == "simulate_ber":
                sim_result = simulate_ber(**params)
                response += f"Calculated BER for {sim_result['modulation']}\n"
                plots.append(plot_ber(sim_result))
        
        return response, plots[0] if plots else None
    
    except Exception as e:
        return f" Error: {str(e)}", None

# Create Gradio interface
with gr.Blocks(title="Project Sionna") as demo:
    gr.Markdown("#Project Sionna")
    gr.Markdown("Ask me to simulate wireless communication scenarios!")
    
    with gr.Row():
        with gr.Column(scale=1):
            chatbot = gr.Chatbot(height=400)
            msg = gr.Textbox(
                placeholder="e.g., 'Simulate 64-QAM at -5 and 15 dB'",
                label="Your Task"
            )
            
            with gr.Row():
                submit = gr.Button("Run Simulation", variant="primary")
                clear = gr.Button("Clear")
            
            gr.Examples(
                examples=[
                    "Simulate 64-QAM constellation at -5 and 15 dB",
                    "Compare QPSK BER in AWGN and Rayleigh at 0, 5, 10 dB",
                    "Show 16-QAM constellation at 0 dB",
                ],
                inputs=msg
            )
        
        with gr.Column(scale=1):
            plot_output = gr.Plot(label="Simulation Result")
    
    def respond(message, chat_history):
        response, plot = process_message(message, chat_history)
        chat_history.append((message, response))
        return "", chat_history, plot
    
    submit.click(respond, [msg, chatbot], [msg, chatbot, plot_output])
    msg.submit(respond, [msg, chatbot], [msg, chatbot, plot_output])
    clear.click(lambda: ([], None), None, [chatbot, plot_output])

if __name__ == "__main__":
    demo.launch(share=False)
