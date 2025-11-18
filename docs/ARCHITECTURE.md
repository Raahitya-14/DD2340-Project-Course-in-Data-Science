# Project Architecture

## System Overview with TaskDecomposer

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                          │
└─────────────────────────────────────────────────────────────────┘

    app.py (Main Entry)
         │
         ▼
         ┌──────────────────────┐
         │  src/ui/chat.py      │  ← Gradio Web Interface
         │  (ChatInterface)     │
         └──────────────────────┘
                    │
                    │ imports & calls
                    ▼
         ┌──────────────────────┐
         │   src/agent.py       │  ← AI Agent (Claude API)
         │   (SionnaAgent)      │
         └──────────────────────┘
                    │
         ┌──────────┼──────────┐
         │          │          │
         ▼          ▼          ▼
┌─────────────┐ ┌─────────┐ ┌──────────────────────────┐
│TaskDecomposer│ │ Claude  │ │ src/mcp_http_server.py   │
│(Rule-based) │ │   API   │ │ Port: 5001               │
└─────────────┘ └─────────┘ └──────────────────────────┘
         │          │                     │
         │          │                     │ calls simulation functions
         │          │                     ▼
         │          │          ┌──────────────────────┐
         │          │          │ src/sionna_tools.py  │  ← 6 Simulation Tools
         │          │          └──────────────────────┘
                    │
        ┌───────────┼───────────┬──────────────┬──────────────┬──────────────┐
        │           │           │              │              │              │
        ▼           ▼           ▼              ▼              ▼              ▼
┌─────────────┐ ┌─────────┐ ┌──────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ simulate_   │ │simulate_│ │ simulate_    │ │simulate_    │ │simulate_ber_│ │compare_mimo_│
│constellation│ │  ber    │ │ radio_map    │ │multi_radio_ │ │    mimo     │ │performance  │
└─────────────┘ └─────────┘ └──────────────┘ │    map      │ └─────────────┘ └─────────────┘
        │           │                │        └─────────────┘        │              │
        │           │                │ subprocess.run()              │              │
        │           │                ▼                               │              │
        │           │       ┌──────────────────┐                    │              │
        │           │       │ scripts/         │                    │              │
        │           │       │ run_radiomap.py  │                    │              │
        │           │       └──────────────────┘                    │              │
        │           │                │                               │              │
        │           │                │ imports                       │              │
        │           │                ▼                               │              │
        │           │       ┌──────────────────┐                    │              │
        │           │       │  sionna.rt       │                    │              │
        │           │       │  (Ray Tracing)   │                    │              │
        │           │       └──────────────────┘                    │              │
        │           │
        │           │ uses
        ▼           ▼
┌─────────────────────────────────┐
│  Sionna Library Components      │
│  - Constellation                │
│  - AWGN                         │
│  - RayleighBlockFading          │
└─────────────────────────────────┘
        │
        │ returns results
        ▼
┌─────────────────────────────────┐
│  src/utils/plotting.py          │  ← Plotting Functions
│  - plot_constellation()         │
│  - plot_ber()                   │
└─────────────────────────────────┘
        │
        │ matplotlib figures → PIL images
        ▼
┌─────────────────────────────────┐
│  Gradio Display                 │
│  (Web Interface)                │
└─────────────────────────────────┘
```

## MCP Communication Flow

```
Agent                    MCP Server              Sionna Tools
  │                          │                         │
  │  GET /tools              │                         │
  ├─────────────────────────>│                         │
  │                          │                         │
  │  Tool definitions        │                         │
  │<─────────────────────────┤                         │
  │                          │                         │
  │  POST /tools/call        │                         │
  │  {name, arguments}       │                         │
  ├─────────────────────────>│                         │
  │                          │  function call          │
  │                          ├────────────────────────>│
  │                          │                         │
  │                          │  simulation results     │
  │                          │<────────────────────────┤
  │                          │                         │
  │  JSON response           │                         │
  │<─────────────────────────┤                         │
  │                          │                         │
```

## Key Design Decisions

### 1. TaskDecomposer Integration
Rule-based task classification extracts parameters (SNR, modulation, positions) and provides structured guidance to Claude for better tool selection and parameter handling.

### 2. HTTP-Based MCP Server
Flask server on port 5001 provides REST API for tool discovery and execution. Agent communicates via HTTP requests instead of stdio.

### 3. Subprocess for Ray Tracing
Mitsuba causes segfaults when imported in the main process, so ray tracing runs in a separate subprocess that saves results to disk.

### 4. Agent-Based Architecture
Claude API interprets natural language tasks (enhanced by TaskDecomposer hints) and generates tool calls. Agent fetches available tools from MCP server and executes them via HTTP.

### 5. Matplotlib → PIL Conversion
Gradio requires PIL images, so matplotlib figures are saved to BytesIO buffer and loaded as PIL images before display.

### 6. Complex Number Serialization
JSON doesn't support complex numbers, so they're converted to [real, imag] lists in the MCP server and reconstructed in the client.

### 7. MIMO Simulation Architecture
MIMO tools use direct TensorFlow operations for channel modeling and maximal ratio combining, avoiding external dependencies.

## Dependencies Between Files

```
app.py
  └─ src/ui/chat.py
       ├─ src/agent.py
       │    ├─ src/task_decomposer.py (Rule-based task classification)
       │    ├─ anthropic (Claude API)
       │    └─ requests → http://127.0.0.1:5001 (MCP Server)
       ├─ src/mcp_http_server.py (Flask)
       │    └─ src/sionna_tools.py
       │         ├─ sionna.phy.mapping
       │         ├─ sionna.phy.channel.awgn
       │         ├─ sionna.phy.channel.rayleigh_block_fading
       │         ├─ tensorflow (for MIMO simulations)
       │         └─ subprocess → scripts/run_radiomap.py
       │                           └─ sionna.rt
       └─ src/utils/plotting.py
            └─ matplotlib.pyplot
```

## Environment Variables

```
.env
  └─ ANTHROPIC_API_KEY  (required for agent.py)
```

## Output Files

```
outputs/
  ├─ *_constellation.png     (from simulate_constellation)
  ├─ *_BER.png              (from simulate_ber)
  ├─ radiomap_*.png         (from simulate_radio_map)
  ├─ radiomap_*_multi.png   (from simulate_multi_radio_map)
  └─ mimo_comparison_*.png  (from compare_mimo_performance)
```

## Task Classification System

```
TaskDecomposer Classification:

├─ constellation     → simulate_constellation
├─ ber              → simulate_ber
├─ mimo_comparison  → compare_mimo_performance
├─ radiomap         → simulate_radio_map
├─ multi_tx_optimization → simulate_multi_radio_map
└─ general          → Natural language response

Parameter Extraction:
├─ SNR values: -5, 15 dB → snr_db_list
├─ Modulation: 64-QAM → modulation="qam", bits_per_symbol=6
├─ Positions: (0,0,0) → tx_position=[0,0,0]
├─ Antenna configs: 2x2 → mimo_config=[2,2]
└─ Transmitter count: 4 transmitters → num_transmitters=4
```
