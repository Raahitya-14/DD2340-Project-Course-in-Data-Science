# Sionna AI Agent with MCP

AI agent for automating wireless communication simulations using Sionna and Model Context Protocol.

## Project Structure

```
DD2340-Project-Course-in-Data-Science/
├── src/                    # Core source code
│   ├── agent.py           # AI agent with MCP client
│   ├── mcp_http_server.py # MCP HTTP server
│   ├── sionna_tools.py    # Sionna simulation wrappers
│   ├── ui/                # User interfaces
│   │   └── chat.py        # Gradio chat interface
│   └── utils/             # Utilities
│       └── plotting.py    # Plotting functions
├── scripts/               # Utility scripts
│   ├── run_agent.py       # Test agent
│   ├── run_simulation.py  # Run simulations with plots
│   └── run_radiomap.py    # Generate radio coverage maps
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
echo 'ANTHROPIC_API_KEY=your-api-key-here' > .env

# 3. Launch chat interface
python3 app.py
# OR use the launcher script
./start.sh
```

## Usage

### Chat Interface (Recommended)
```bash
python3 app.py
# OR
./start.sh
```
Opens web interface at http://localhost:7860

### Command Line
```bash
# Test agent (starts MCP server automatically)
python3 src/agent.py

# Run simulations with plots
python3 scripts/run_simulation.py "Your task here"

# Generate radio coverage map
python3 scripts/run_radiomap.py rss
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

## Available Tools (via MCP)

1. **simulate_constellation** - Generate constellation diagrams with AWGN
2. **simulate_ber** - Calculate Bit Error Rate for different channels
3. **simulate_radio_map** - Generate radio coverage maps using ray tracing

## MCP Architecture

The agent communicates with simulation tools through an HTTP-based MCP server:
- MCP server runs on `http://127.0.0.1:5001`
- Agent fetches tool definitions from `/tools`
- Tool execution via `/tools/call`
- Automatic startup and cleanup

## Example Natural Language Tasks

- "Show 64-QAM constellation at -5 and 15 dB"
- "Compare QPSK BER in AWGN vs Rayleigh fading at -5, 15 dB"
- "Simulate 16-QAM with noise at 0, 5, 10 dB"
- "Generate radio coverage map with transmitter at (0,0,0) and receiver at (100,0,0)"
