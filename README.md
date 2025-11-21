# Sionna AI Agent with MCP

AI agent for automating wireless communication simulations using Sionna and Model Context Protocol with intelligent task decomposition .

## Project Structure

```
DD2340-Project-Course-in-Data-Science/
├── src/                    # Core source code
│   ├── agent.py           # AI agent with MCP client and TaskDecomposer
│   ├── task_decomposer.py # Rule-based task classification and parameter extraction
│   ├── mcp_http_server.py # MCP HTTP server
│   ├── sionna_tools.py    # Sionna simulation wrappers
│   ├── ui/                # User interfaces
│   │   └── chat.py        # Gradio chat interface
│   └── utils/             # Utilities
│       └── plotting.py    # Plotting functions
├── examples/              # Example simulations
│   ├── MT/                # Medium tasks
│   ├── ST/                # Simple tasks
│   └── TT/                # Trivial tasks
├── outputs/               # Generated plots and radio maps
├── docs/                  # Documentation
├── app.py                 # Main chat interface
├── requirements.txt       # Dependencies
└── README.md
```

## Key Features

- **Intelligent Task Decomposition**: Automatically classifies and extracts parameters from natural language
- **Comprehensive Simulation Suite**: 6 simulation tools covering modulation, BER, MIMO, and radio propagation
- **Interactive Web Interface**: Gradio-based chat interface with real-time plotting
- **Flexible Architecture**: MCP-based tool communication with HTTP server
- **Professional Visualizations**: Publication-ready plots for all simulation types

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API key in .env file
echo 'ANTHROPIC_API_KEY=your-api-key-here' > .env

# 3. Launch chat interface
python3 app.py
# OR use the launcher script
./start.sh  # automatically restarts the MCP server before launching

# To restart the MCP server manually (after code changes)
./restart_mcp.sh
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

1. **simulate_constellation** - Generate constellation diagrams with AWGN noise
2. **simulate_ber** - Calculate Bit Error Rate for different channels (AWGN/Rayleigh)
3. **simulate_radio_map** - Generate single-transmitter radio coverage maps using ray tracing
4. **simulate_multi_radio_map** - Generate multi-transmitter radio coverage maps
5. **simulate_ber_mimo** - Simulate BER for MIMO systems with configurable antennas
6. **compare_mimo_performance** - Compare SISO vs MIMO performance with BER plots

## System Architecture

The agent uses intelligent task decomposition and MCP for simulation execution:

### Task Decomposition Layer
- **TaskDecomposer**: Rule-based classification of natural language queries
- **Task Types**: constellation, ber, mimo_comparison, radiomap, multi_tx_optimization
- **Parameter Extraction**: SNR values, modulation schemes, antenna configs, positions
- **Structured Guidance**: Generates step-by-step instructions for Claude

### MCP Communication
- MCP server runs on `http://127.0.0.1:5001`
- Agent fetches tool definitions from `/tools`
- Tool execution via `/tools/call`
- Automatic startup and cleanup

### Processing Flow
```
Natural Language → TaskDecomposer → Agent → Claude + MCP → Simulation Tools → Results
```

## Example Natural Language Tasks

### Constellation Diagrams
- "Show 64-QAM constellation at -5 and 15 dB"
- "Simulate 16-QAM with noise at 0, 5, 10 dB"

### BER Analysis
- "Compare QPSK BER in AWGN vs Rayleigh fading at -5, 15 dB"
- "Plot BER curves for 64-QAM from -10 to 20 dB"

### MIMO Performance
- "Compare SISO vs MIMO performance with BER plots"
- "Analyze 2x2 MIMO vs 4x4 MIMO antenna configurations"

### Radio Coverage Maps
- "Generate radio coverage map with transmitter at (0,0,0) and receiver at (100,0,0)"
- "Optimize placement of 4 transmitters for maximum coverage"
- "Show SINR map for multiple base stations"
