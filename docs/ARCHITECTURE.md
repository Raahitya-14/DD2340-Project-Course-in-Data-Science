# Project Architecture

## File Structure and Call Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                          │
└─────────────────────────────────────────────────────────────────┘

    app.py (Main Entry)                scripts/run_simulation.py
         │                                      │
         └──────────┬───────────────────────────┘
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
                    │ HTTP requests (MCP protocol)
                    ▼
         ┌──────────────────────────┐
         │ src/mcp_http_server.py   │  ← MCP Server (Flask)
         │ Port: 5001               │
         └──────────────────────────┘
                    │
                    │ calls simulation functions
                    ▼
         ┌──────────────────────┐
         │ src/sionna_tools.py  │  ← Simulation Functions
         └──────────────────────┘
                    │
        ┌───────────┼───────────┬──────────────┐
        │           │           │              │
        ▼           ▼           ▼              ▼
┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐
│ simulate_   │ │simulate_│ │  list_  │ │ simulate_    │
│constellation│ │  ber    │ │modula-  │ │ radio_map    │
└─────────────┘ └─────────┘ │ tions   │ └──────────────┘
        │           │         └─────────┘        │
        │           │                            │ subprocess.run()
        │           │                            ▼
        │           │                   ┌──────────────────┐
        │           │                   │ scripts/         │
        │           │                   │ run_radiomap.py  │
        │           │                   └──────────────────┘
        │           │                            │
        │           │                            │ imports
        │           │                            ▼
        │           │                   ┌──────────────────┐
        │           │                   │  sionna.rt       │
        │           │                   │  (Ray Tracing)   │
        │           │                   └──────────────────┘
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

### 1. HTTP-Based MCP Server
Flask server on port 5001 provides REST API for tool discovery and execution. Agent communicates via HTTP requests instead of stdio.

### 2. Subprocess for Ray Tracing
Mitsuba causes segfaults when imported in the main process, so ray tracing runs in a separate subprocess that saves results to disk.

### 3. Agent-Based Architecture
Claude API interprets natural language tasks and generates tool calls. Agent fetches available tools from MCP server and executes them via HTTP.

### 4. Matplotlib → PIL Conversion
Gradio requires PIL images, so matplotlib figures are saved to BytesIO buffer and loaded as PIL images before display.

### 5. Complex Number Serialization
JSON doesn't support complex numbers, so they're converted to [real, imag] lists in the MCP server and reconstructed in the client.

## Dependencies Between Files

```
app.py
  └─ src/ui/chat.py
       ├─ src/agent.py
       │    ├─ anthropic (Claude API)
       │    └─ requests → http://127.0.0.1:5001 (MCP Server)
       ├─ src/mcp_http_server.py (Flask)
       │    └─ src/sionna_tools.py
       │         ├─ sionna.phy.mapping
       │         ├─ sionna.phy.channel.awgn
       │         ├─ sionna.phy.channel.rayleigh_block_fading
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
  ├─ *_constellation.png  (from simulate_constellation)
  ├─ *_BER.png           (from simulate_ber)
  └─ radiomap_*.png      (from simulate_radio_map)
```
