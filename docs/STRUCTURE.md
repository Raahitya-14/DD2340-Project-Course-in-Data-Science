# Project Structure

## Directory Layout

```
dd2340_project/
├── app.py                      # Main entry point - Launch chat interface
├── requirements.txt            # Python dependencies
├── .env                        # API keys (not in git)
├── README.md                   # Main documentation
│
├── src/                        # Core application code
│   ├── __init__.py
│   ├── agent.py                # AI agent (Claude integration)
│   ├── sionna_tools.py         # Sionna simulation wrappers
│   ├── mcp_server.py           # Model Context Protocol server
│   │
│   ├── ui/                     # User interface modules
│   │   ├── __init__.py
│   │   └── chat.py             # Gradio chat interface
│   │
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       └── plotting.py         # Matplotlib plotting functions
│
├── scripts/                    # Utility scripts
│   ├── run_agent.py            # Test agent interpretation
│   ├── run_server.py           # Launch MCP server
│   ├── run_simulation.py       # Run simulations from CLI
│   └── chat_interface.py       # Standalone chat (legacy)
│
├── examples/                   # Example simulation scripts
│   ├── ST/                     # Simple tasks
│   │   ├── simpletask1.py      # 64-QAM constellation
│   │   └── simpletask2.py      # QPSK BER comparison
│   └── TT/                     # Trivial tasks
│       ├── trivialtask1.py     # Ray tracing
│       └── Trivialtask2.py     # 16-QAM constellation
│
├── outputs/                    # Generated plots and results
│   └── .gitkeep
│
└── docs/                       # Documentation
    ├── QUICKSTART.md           # Quick start guide
    └── STRUCTURE.md            # This file
```

## Key Files

### Main Entry Points
- **`app.py`** - Launch web chat interface (recommended)
- **`scripts/run_agent.py`** - Test agent without simulations
- **`scripts/run_simulation.py`** - Run simulations from command line

### Core Modules
- **`src/agent.py`** - AI agent that interprets natural language
- **`src/sionna_tools.py`** - Wrapper functions for Sionna simulations
- **`src/mcp_server.py`** - MCP server for tool integration
- **`src/ui/chat.py`** - Gradio-based chat interface
- **`src/utils/plotting.py`** - Plotting utilities

### Configuration
- **`.env`** - Environment variables (API keys)
- **`requirements.txt`** - Python package dependencies

## Usage Patterns

### 1. Interactive (Web UI)
```bash
python3 app.py
```

### 2. Command Line
```bash
python3 scripts/run_simulation.py "Your task"
```

### 3. Programmatic
```python
from src.agent import SionnaAgent
agent = SionnaAgent()
result = agent.run("Your task")
```

## Adding New Features

### New Simulation Tool
1. Add function to `src/sionna_tools.py`
2. Register in `src/mcp_server.py`
3. Update agent prompt in `src/agent.py`

### New UI Component
1. Create module in `src/ui/`
2. Import in main `app.py`

### New Utility
1. Add to `src/utils/`
2. Import where needed
