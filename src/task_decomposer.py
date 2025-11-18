"""Lightweight rule-based task decomposition for the Sionna agent."""
from __future__ import annotations

import math
import re
from typing import Dict, List, Tuple


class TaskDecomposer:
    """Parse natural language requests into structured hints and parameters."""

    MODULATION_BITS = {
        "bpsk": 1,
        "qpsk": 2,
        "8-psk": 3,
        "16qam": 4,
        "64qam": 6,
        "256qam": 8,
    }

    def decompose(self, text: str) -> Dict:
        """Return structured task metadata and extra guidance."""
        lowered = text.lower()
        task_type = self._classify_task(lowered)
        params: Dict = {}

        snr_values = self._extract_snr(lowered)
        if snr_values and task_type in {"constellation", "ber"}:
            params["snr_db_list"] = snr_values

        modulation = self._extract_modulation(lowered)
        if modulation and task_type in {"constellation", "ber"}:
            params["modulation"] = modulation["scheme"]
            params["bits_per_symbol"] = modulation["bits"]

        antenna_configs = self._extract_antenna_configs(lowered)
        if antenna_configs and task_type == "mimo_comparison":
            params["siso_config"] = antenna_configs.get("siso") or [1, 1]
            params["mimo_config"] = antenna_configs.get("mimo") or [2, 2]

        positions = self._extract_positions(lowered)
        if positions and task_type in {"radiomap", "multi_tx_optimization"}:
            if "tx_position" not in params and positions:
                params["tx_position"] = positions[0]
            if len(positions) > 1:
                params["rx_position"] = positions[1]

        num_tx = self._extract_transmitter_count(lowered)
        if num_tx:
            params["num_transmitters"] = num_tx

        extra_instructions = self._build_extra_instructions(task_type, params)

        return {
            "task_type": task_type,
            "parameters": params,
            "extra_instructions": extra_instructions,
        }

    def format_for_prompt(self, decomposition: Dict) -> str:
        """Render decomposition into a short instruction block for Claude."""
        if not decomposition:
            return ""

        lines = ["Auto-generated task guidance:"]
        lines.append(f"- Task type: {decomposition.get('task_type', 'unknown')}")

        parameters = decomposition.get("parameters") or {}
        if parameters:
            param_parts = [
                f"{key}={value}"
                for key, value in parameters.items()
                if key != "num_transmitters"
            ]
            if param_parts:
                lines.append(f"- Suggested parameters: {', '.join(param_parts)}")

        num_tx = parameters.get("num_transmitters")
        if num_tx:
            lines.append(f"- Target number of transmitters: {num_tx}")

        instructions = decomposition.get("extra_instructions") or []
        if instructions:
            lines.append("- Detailed instructions:")
            lines.extend([f"  * {inst}" for inst in instructions])

        if decomposition.get("task_type") == "multi_tx_optimization":
            lines.append("- TOOL: Use simulate_multi_radio_map with the transmitter list above.")
            if "rx_position" in parameters:
                lines.append(f"- RECEIVER_HINT: Use receiver position {parameters['rx_position']} unless user specifies otherwise.")

        return "\n".join(lines)

    # -------------------------- helpers --------------------------

    def _classify_task(self, text: str) -> str:
        if any(word in text for word in ["optimize", "optimal", "placement"]) and "transmit" in text:
            return "multi_tx_optimization"
        if "mimo" in text or "antenna" in text and "compare" in text:
            return "mimo_comparison"
        if any(word in text for word in ["coverage", "radio map", "radiomap", "path gain", "sinr"]):
            return "radiomap"
        if "ber" in text:
            return "ber"
        if "constellation" in text or any(qam in text for qam in ["qam", "psk", "modulation"]):
            return "constellation"
        return "general"

    def _extract_snr(self, text: str) -> List[int]:
        values = []
        for match in re.findall(r"(-?\d+(?:\.\d+)?)\s*dB", text):
            try:
                values.append(int(float(match)))
            except ValueError:
                continue
        return sorted(list(dict.fromkeys(values)))

    def _extract_modulation(self, text: str) -> Dict | None:
        if "qpsk" in text:
            return {"scheme": "qam", "bits": 2}
        if "bpsk" in text:
            return {"scheme": "pam", "bits": 1}
        qam_match = re.search(r"(\d+)\s*[- ]?\s*qam", text)
        if qam_match:
            order = int(qam_match.group(1))
            bits = int(math.log2(order)) if order > 0 else 2
            return {"scheme": "qam", "bits": bits}
        if "psk" in text:
            return {"scheme": "qam", "bits": 2}
        return None

    def _extract_antenna_configs(self, text: str) -> Dict[str, List[int]]:
        configs: Dict[str, List[int]] = {}
        match = re.findall(r"(\d+)\s*x\s*(\d+)", text)
        if not match:
            return configs

        unique_pairs = []
        for tx, rx in match:
            pair = [int(tx), int(rx)]
            if pair not in unique_pairs:
                unique_pairs.append(pair)

        if unique_pairs:
            configs["siso"] = unique_pairs[0]
        if len(unique_pairs) > 1:
            configs["mimo"] = unique_pairs[1]
        elif unique_pairs:
            first = unique_pairs[0]
            if first != [2, 2]:
                configs["mimo"] = [max(2, first[0]), max(2, first[1])]

        return configs

    def _extract_positions(self, text: str) -> List[List[float]]:
        coords = []
        for match in re.findall(r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)", text):
            coords.append([float(match[0]), float(match[1]), float(match[2])])
        return coords

    def _extract_transmitter_count(self, text: str) -> int | None:
        match = re.search(r"(\d+)\s+(?:transmitters?|tx|base stations?)", text)
        if match:
            return int(match.group(1))
        return None

    def _build_extra_instructions(self, task_type: str, params: Dict) -> List[str]:
        instructions: List[str] = []
        if task_type == "constellation":
            instructions.append("Call `simulate_constellation` with the suggested modulation and SNR values.")
            instructions.append("Return at least one constellation plot and describe the noise impact at each SNR.")
        elif task_type == "ber":
            instructions.append("Use `simulate_ber` and ensure multiple SNR points form a smooth BER curve.")
            instructions.append("Compare AWGN and Rayleigh channels when possible.")
        elif task_type == "radiomap":
            instructions.append("Invoke `simulate_radio_map` with the provided TX/RX positions or reasonable defaults.")
            instructions.append("Explain the selected metric (RSS/path_gain/SINR) and highlight TX/RX markers.")
        elif task_type == "mimo_comparison":
            instructions.append("Use `compare_mimo_performance` to contrast SISO and MIMO BER trends.")
            instructions.append("Discuss how antenna counts influence diversity gain.")
        elif task_type == "multi_tx_optimization":
            instructions.append("This is an optimization problem: propose several 4-transmitter layouts before running simulations.")
            instructions.append("Call `simulate_multi_radio_map` with a list of transmitter coordinates (e.g., [[x1,y1,z1], ...]) and representative receiver/user points to evaluate SINR/coverage.")
            instructions.append("If needed, run additional single-transmitter maps to gain intuition before refining the multi-TX layout.")
            instructions.append("Summarize the trade-offs and recommend the configuration that maximizes average throughput/coverage.")
        else:
            instructions.append("Provide a clear explanation or choose the most relevant simulation tool if one applies.")
        return instructions
