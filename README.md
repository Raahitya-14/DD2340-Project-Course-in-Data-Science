# Sionna AI Agent with MCP

AI agent for automating wireless communication simulations using Sionna and Model Context Protocol.

## Project Structure

```
dd2340_project/
├── src/                    # Core source code
│   ├── agent.py           # AI agent
│   ├── sionna_tools.py    # Sionna simulation wrappers
│   ├── mcp_server.py      # MCP server
│   ├── ui/                # User interfaces
│   │   └── chat.py        # Gradio chat interface
│   └── utils/             # Utilities
│       └── plotting.py    # Plotting functions
├── scripts/               # Utility scripts
│   ├── run_agent.py       # Test agent
│   ├── run_server.py      # Run MCP server
│   ├── run_simulation.py  # Run simulations
│   └── chat_interface.py  # Old chat interface
├── examples/              # Example simulations
│   ├── ST/                # Simple tasks
│   └── TT/                # Trivial tasks
├── outputs/               # Generated plots
├── docs/                  # Documentation
├── app.py                 # Main chat interface
├── requirements.txt       # Dependencies
└── README.md
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API key in .env file
echo 'ANTHROPIC_API_KEY=sk-ant-your-key' > .env

# 3. Launch chat interface
python3 app.py
```

## Usage

### Chat Interface (Recommended)
```bash
python3 app.py
```
Opens web interface at http://localhost:7860

### Command Line
```bash
# Test agent
python3 scripts/run_agent.py

# Run with plots
python3 scripts/run_simulation.py "Your task here"

# MCP server
python3 scripts/run_server.py
```

### Programmatic
```python
import sys
sys.path.insert(0, 'src')
from agent import SionnaAgent

agent = SionnaAgent()
result = agent.run("Simulate 64-QAM at -5 and 15 dB")
print(result)
```

## Available Tools

1. **simulate_constellation** - Generate constellation diagrams with AWGN
2. **simulate_ber** - Calculate Bit Error Rate for different channels
3. **list_modulations** - List available modulation schemes
4. **get_modulation_info** - Get modulation details

## Example Natural Language Tasks

- "Show 64-QAM constellation at -5 and 15 dB"
- "Compare QPSK BER in AWGN vs Rayleigh fading"
- "Simulate 16-QAM with noise at 0, 5, 10 dB"
