# Quick Start Guide

## Installation

```bash
cd dd2340_project
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

## Running the Agent

```bash
python run_agent.py
```

This will run example tasks:
- "Simulate 64-QAM constellation at SNR of -5 dB and 15 dB"
- "Compare QPSK BER performance in AWGN and Rayleigh fading"
- "Show me 16-QAM constellation points"

## Running the MCP Server

```bash
python3 run_server.py
```

The server exposes 4 tools via stdio:
1. `simulate_constellation` - Generate constellation diagrams
2. `simulate_ber` - Calculate Bit Error Rate
3. `list_modulations` - List available modulations
4. `get_modulation_info` - Get modulation details

## Custom Tasks

```python
import sys
sys.path.insert(0, 'src')
from agent import SionnaAgent

agent = SionnaAgent()

# Your custom task
result = agent.run("Compare 16-QAM and 64-QAM at 10 dB SNR")
print(result)
```

## Examples

Check `examples/ST/` and `examples/TT/` for standalone simulation scripts.

## Outputs

All generated plots are saved to `outputs/` directory.
