"""HTTP wrapper for MCP Server"""
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from flask import Flask, request, jsonify
import sionna_tools

app = Flask(__name__)

@app.route('/tools', methods=['GET'])
def list_tools():
    """List available tools"""
    return jsonify({
        "tools": [
            {
                "name": "simulate_constellation",
                "description": "Simulate constellation diagram with AWGN at different SNR levels",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "modulation": {"type": "string", "enum": ["qam", "pam", "psk"], "default": "qam"},
                        "bits_per_symbol": {"type": "integer", "minimum": 1, "maximum": 8, "default": 2},
                        "num_symbols": {"type": "integer", "default": 2000},
                        "snr_db_list": {"type": "array", "items": {"type": "number"}, "default": [-5, 15]}
                    }
                }
            },
            {
                "name": "simulate_ber",
                "description": "Simulate Bit Error Rate for different channels",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "modulation": {"type": "string", "enum": ["qam", "pam", "psk"], "default": "qam"},
                        "bits_per_symbol": {"type": "integer", "minimum": 1, "maximum": 8, "default": 2},
                        "snr_db_list": {"type": "array", "items": {"type": "number"}, "default": [-5, 15]},
                        "num_bits": {"type": "integer", "default": 100000},
                        "channels": {"type": "array", "items": {"type": "string"}, "default": ["awgn", "rayleigh"]}
                    }
                }
            },
            {
                "name": "simulate_radio_map",
                "description": "Generate radio coverage map using ray tracing",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tx_position": {"type": "array", "items": {"type": "number"}, "default": [0, 0, 0]},
                        "rx_position": {"type": "array", "items": {"type": "number"}, "default": [100, 0, 0]},
                        "metric": {"type": "string", "enum": ["rss", "path_gain", "sinr"], "default": "rss"}
                    }
                }
            },
            {
                "name": "list_available_tools",
                "description": "List all available simulation tools and their descriptions",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "simulate_ber_mimo",
                "description": "Simulate BER for MIMO Rayleigh fading channel with QPSK modulation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "num_tx_ant": {"type": "integer", "minimum": 1, "default": 1},
                        "num_rx_ant": {"type": "integer", "minimum": 1, "default": 1},
                        "num_bits": {"type": "integer", "default": 100000}
                    }
                }
            },
            {
                "name": "compare_mimo_performance",
                "description": "Compare SISO vs MIMO performance by running both simulations and plotting BER comparison",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "siso_config": {"type": "array", "items": {"type": "integer"}, "default": [1, 1]},
                        "mimo_config": {"type": "array", "items": {"type": "integer"}, "default": [2, 2]},
                        "num_bits": {"type": "integer", "default": 100000}
                    }
                }
            }
        ]
    })

@app.route('/tools/call', methods=['POST'])
def call_tool():
    """Execute a tool"""
    data = request.json
    tool_name = data.get('name')
    arguments = data.get('arguments', {})
    
    try:
        if tool_name == "simulate_constellation":
            result = sionna_tools.simulate_constellation(**arguments)
            # Convert numpy arrays and complex numbers to lists
            result["constellation"] = [[float(x.real), float(x.imag)] for x in result["constellation"]]
            for snr in result["snr_levels"]:
                result["snr_levels"][snr] = [[float(x.real), float(x.imag)] for x in result["snr_levels"][snr]]
        elif tool_name == "simulate_ber":
            result = sionna_tools.simulate_ber(**arguments)
        elif tool_name == "simulate_radio_map":
            result = sionna_tools.simulate_radio_map(**arguments)
        elif tool_name == "list_available_tools":
            result = sionna_tools.list_available_tools()
        elif tool_name == "simulate_ber_mimo":
            result = sionna_tools.simulate_ber_mimo(**arguments)
            result = {int(k): float(v) for k, v in result.items()}
        elif tool_name == "compare_mimo_performance":
            result = sionna_tools.compare_mimo_performance(**arguments)
            result["siso"]["ber"] = {int(k): float(v) for k, v in result["siso"]["ber"].items()}
            result["mimo"]["ber"] = {int(k): float(v) for k, v in result["mimo"]["ber"].items()}
        else:
            return jsonify({"error": f"Unknown tool: {tool_name}"}), 400
        
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    import os
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    print("Starting MCP HTTP server on port 5001...")
    app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)
