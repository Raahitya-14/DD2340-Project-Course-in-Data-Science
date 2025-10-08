"""Gradio chat interface for Sionna AI Agent"""
import os
import json
import sys
from pathlib import Path
import gradio as gr

# Add src to path
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from agent import SionnaAgent
from sionna_tools import simulate_constellation, simulate_ber, simulate_radio_map
from utils.plotting import plot_constellation, plot_ber
from PIL import Image
import io

class ChatInterface:
    def __init__(self):
        self.agent = SionnaAgent(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    def process_message(self, message, history):
        """Process user message and return response with plot"""
        try:
            result = self.agent.run(message)
            
            response = f"**Understanding:** {result['task']}\n\n"
            response += f"**Model:** {result['model']}\n\n"
            
            plots = []
            for tool_call in result["tool_calls"]:
                tool_name = tool_call['tool']
                params = tool_call['parameters']
                
                response += f"**Tool:** {tool_name}\n"
                response += f"**Parameters:** {json.dumps(params, indent=2)}\n\n"
                
                if tool_name == "simulate_constellation":
                    sim_result = simulate_constellation(**params)
                    response += f"Generated {sim_result['modulation']} constellation\n"
                    fig = plot_constellation(sim_result)
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png')
                    buf.seek(0)
                    plots.append(Image.open(buf))
                
                elif tool_name == "simulate_ber":
                    sim_result = simulate_ber(**params)
                    response += f"Calculated BER for {sim_result['modulation']}\n"
                    fig = plot_ber(sim_result)
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png')
                    buf.seek(0)
                    plots.append(Image.open(buf))
                
                elif tool_name == "simulate_radio_map":
                    sim_result = simulate_radio_map(**params)
                    response += f"Generated radio map: {sim_result['plot_path']}\n"
                    if os.path.exists(sim_result['plot_path']):
                        plots.append(Image.open(sim_result['plot_path']))
            
            return response, plots[0] if plots else None
        
        except Exception as e:
            return f" Error: {str(e)}", None
    
    def create_interface(self):
        """Create Gradio interface"""
        with gr.Blocks(title="Project Sionna") as demo:
            gr.Markdown("# Sionna AI Agent")
            gr.Markdown("Ask me to simulate wireless communication scenarios!")
            
            with gr.Row():
                with gr.Column(scale=1):
                    chatbot = gr.Chatbot(height=400)
                    msg = gr.MultimodalTextbox(
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
                            "Simulate transmitter at (0,0,0) and receiver at (100,0,0)",
                        ],
                        inputs=msg
                    )
                
                with gr.Column(scale=1):
                    plot_output = gr.Image(label="Simulation Result", type="pil")
            
            def respond(message, chat_history):
                text = message["text"] if isinstance(message, dict) else message
                response, plot = self.process_message(text, chat_history)
                chat_history.append((text, response))
                return None, chat_history, plot
            
            submit.click(respond, [msg, chatbot], [msg, chatbot, plot_output])
            msg.submit(respond, [msg, chatbot], [msg, chatbot, plot_output])
            clear.click(lambda: ([], None), None, [chatbot, plot_output])
        
        return demo
    
    def launch(self, **kwargs):
        """Launch the interface"""
        demo = self.create_interface()
        demo.launch(**kwargs)
