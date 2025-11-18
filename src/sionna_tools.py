"""Sionna simulation tools wrapper"""
import os
import subprocess
import json
import tempfile
import numpy as np
import tensorflow as tf
from sionna.phy.mapping import Constellation
from sionna.phy.channel.awgn import AWGN
from sionna.phy.channel.rayleigh_block_fading import RayleighBlockFading


import ast


def _parse_positions_string(value):
    """Robustly parse a string representation of positions.

    Claude sometimes returns non-JSON literals (e.g., list comprehensions).
    We first try json.loads and fall back to ast.literal_eval.
    """
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Empty position string")
    parsed = None
    if cleaned[0] in "[{":
        try:
            parsed = json.loads(cleaned.replace("'", '"'))
        except Exception:
            pass
    if parsed is None:
        parsed = ast.literal_eval(cleaned)
    return parsed


def _to_float_triplet(pos):
    if isinstance(pos, str):
        pos = _parse_positions_string(pos)
    return [float(pos[0]), float(pos[1]), float(pos[2])]


def _positions_slug(prefix, positions):
    normalized = [_to_float_triplet(pos) for pos in positions]
    parts = ["{}_{}_{}".format(pos[0], pos[1], pos[2]) for pos in normalized]
    return f"{prefix}{'__'.join(parts)}"
def simulate_constellation(modulation="qam", bits_per_symbol=2, num_symbols=2000, snr_db_list=[-5, 15]):
    """Generate constellation with AWGN at different SNR levels"""
    bits_per_symbol = int(bits_per_symbol)
    num_symbols = int(num_symbols)
    snr_db_list = [float(snr) for snr in snr_db_list]

    mod_lower = modulation.lower()
    if mod_lower in ["qpsk", "psk"]:
        modulation = "qam"
        bits_per_symbol = 2
    elif mod_lower == "bpsk":
        modulation = "pam"
        bits_per_symbol = 1
    
    const = Constellation(modulation, num_bits_per_symbol=bits_per_symbol, normalize=True)
    awgn = AWGN()
    idx = tf.random.uniform([num_symbols], minval=0, maxval=const.num_points, dtype=tf.int32)
    tx = tf.gather(const.points, idx)
    
    results = {
        "constellation": const.points.numpy(),
        "modulation": f"{2**bits_per_symbol}-{modulation.upper()}",
        "snr_levels": {}
    }
    
    for snr in snr_db_list:
        snr_lin = 10**(snr/10)
        no = tf.constant(1/snr_lin, dtype=tf.float32)
        rx = awgn(tx, no)
        results["snr_levels"][snr] = rx.numpy()
    
    return results

def simulate_ber(modulation="qam", bits_per_symbol=2, snr_db_list=[-5, 15], num_bits=100000, channels=["awgn", "rayleigh"]):
    """Simulate BER for different channels"""
    mod_lower = modulation.lower()
    if mod_lower in ["qpsk", "psk"]:
        modulation = "qam"
        bits_per_symbol = 2
    elif mod_lower == "bpsk":
        modulation = "pam"
        bits_per_symbol = 1
    
    const = Constellation(modulation, num_bits_per_symbol=bits_per_symbol, normalize=True)
    awgn = AWGN()
    rayleigh = RayleighBlockFading(num_rx=1, num_rx_ant=1, num_tx=1, num_tx_ant=1)
    
    results = {"modulation": f"{2**bits_per_symbol}-{modulation.upper()}", "ber": {}}
    
    def demodulate(rx):
        rx = tf.reshape(rx, [-1,1])
        distances = tf.abs(rx - const.points[None,:])**2
        return tf.argmin(distances, axis=1)
    
    for snr_db in snr_db_list:
        num_symbols = num_bits // bits_per_symbol
        idx = tf.random.uniform([num_symbols], minval=0, maxval=const.num_points, dtype=tf.int32)
        tx = tf.gather(const.points, idx)
        
        snr_lin = 10**(snr_db/10)
        no = tf.constant(1/snr_lin, dtype=tf.float32)
        
        results["ber"][snr_db] = {}
        
        if "awgn" in channels:
            rx_awgn = awgn(tx, no)
            idx_awgn = tf.cast(demodulate(rx_awgn), tf.int32)
            idx_cast = tf.cast(idx, tf.int32)
            ser = tf.reduce_mean(tf.cast(idx_awgn != idx_cast, tf.float32)).numpy()
            results["ber"][snr_db]["awgn"] = min(ser * bits_per_symbol, 0.5)
        
        if "rayleigh" in channels:
            h, _ = rayleigh(batch_size=num_symbols, num_time_steps=1)
            h = tf.squeeze(h)
            rx_rayleigh = awgn(h * tx, no) / h
            idx_rayleigh = tf.cast(demodulate(rx_rayleigh), tf.int32)
            idx_cast = tf.cast(idx, tf.int32)
            ser = tf.reduce_mean(tf.cast(idx_rayleigh != idx_cast, tf.float32)).numpy()
            results["ber"][snr_db]["rayleigh"] = min(ser * bits_per_symbol, 0.5)
    
    return results

def simulate_radio_map(tx_position=[0,0,0], rx_position=[100,0,0], metric="rss"):
    """Generate radio coverage map using ray tracing (runs external script)"""
    tx_position = _to_float_triplet(tx_position)
    rx_position = _to_float_triplet(rx_position)
    script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "run_radiomap.py")
    result = subprocess.run(["python3", script_path, metric, 
                           str(tx_position[0]), str(tx_position[1]), str(tx_position[2]),
                           str(rx_position[0]), str(rx_position[1]), str(rx_position[2])],
                          capture_output=True, text=True)
    
    filename = f"radiomap_{metric}_{_positions_slug('tx', [tx_position])}_{_positions_slug('rx', [rx_position])}.png"
    abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs", filename))
    return {
        "tx_position": tx_position,
        "rx_position": rx_position,
        "metric": metric,
        "output": result.stdout,
        "plot_path": abs_path,
        "relative_plot_path": os.path.join("outputs", filename),
        "cwd_plot_path": os.path.join(os.getcwd(), "outputs", filename),
    }


def simulate_multi_radio_map(tx_positions, rx_positions=None, metric="rss"):
    """Generate radio coverage map for multiple transmitters"""
    if not tx_positions:
        raise ValueError("tx_positions must contain at least one transmitter")
    if rx_positions is None or len(rx_positions) == 0:
        rx_positions = [[100, 0, 0]]
    if isinstance(tx_positions, str):
        tx_positions = _parse_positions_string(tx_positions)
    if isinstance(rx_positions, str):
        rx_positions = _parse_positions_string(rx_positions)
    tx_positions = [_to_float_triplet(pos) for pos in tx_positions]
    rx_positions = [_to_float_triplet(pos) for pos in rx_positions]
    script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "run_radiomap.py")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8") as tmp:
        json.dump({"tx_positions": tx_positions, "rx_positions": rx_positions, "metric": metric}, tmp)
        tmp_path = tmp.name
    try:
        result = subprocess.run(["python3", script_path, "--config", tmp_path],
                                capture_output=True, text=True)
    finally:
        os.unlink(tmp_path)
    filename = f"radiomap_{metric}_{_positions_slug('tx', tx_positions)}_{_positions_slug('rx', rx_positions)}.png"
    abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs", filename))
    return {
        "tx_positions": tx_positions,
        "rx_positions": rx_positions,
        "metric": metric,
        "output": result.stdout,
        "plot_path": abs_path,
        "relative_plot_path": os.path.join("outputs", filename),
        "cwd_plot_path": os.path.join(os.getcwd(), "outputs", filename),
    }

def list_available_tools():
    """List all available simulation tools"""
    return {
        "simulate_constellation": "Generate constellation diagrams with AWGN",
        "simulate_ber": "Calculate Bit Error Rate for different channels",
        "simulate_radio_map": "Generate radio coverage map using ray tracing",
        "simulate_multi_radio_map": "Generate radio map for multiple transmitters and receivers",
        "simulate_ber_mimo": "Simulate BER for MIMO systems with configurable antennas",
        "compare_mimo_performance": "Compare SISO vs MIMO performance with BER plots"
    }

def simulate_ber_mimo(num_tx_ant=1, num_rx_ant=1, num_bits=100000):
    """
    Simulate BER for MIMO Rayleigh fading channel with QPSK modulation.
    Args:
        num_tx_ant: number of transmit antennas
        num_rx_ant: number of receive antennas
        num_bits: total bits to transmit
    Returns:
        ber_dict: dictionary mapping SNR(dB) -> BER
    """
    const_points = tf.constant([1 + 1j, 1 - 1j, -1 + 1j, -1 - 1j], dtype=tf.complex64) / tf.cast(tf.sqrt(2.0), tf.complex64)

    bits_per_symbol = 2
    snr_dbs = range(0, 21, 2)  # 0~20dB, step 2
    ber_dict = {}

    for snr_db in snr_dbs:
        # SNR in linear scale
        snr_lin = 10 ** (snr_db / 10)
        no = tf.constant(1.0 / snr_lin, dtype=tf.float32)
        num_symbols = num_bits // bits_per_symbol

        # Generate random QPSK symbols
        idx = tf.random.uniform([num_symbols], 0, 4, dtype=tf.int32)
        tx = tf.gather(const_points, idx)  # shape [num_symbols]

        tx = tf.tile(tx[:, None], [1, num_tx_ant])  # [num_symbols, num_tx_ant]

        # Rayleigh fading channel
        h_real = tf.random.normal([num_symbols, num_rx_ant, num_tx_ant], dtype=tf.float32)
        h_imag = tf.random.normal([num_symbols, num_rx_ant, num_tx_ant], dtype=tf.float32)
        h = tf.complex(h_real, h_imag) / tf.cast(tf.sqrt(2.0), tf.complex64)

        noise_real = tf.random.normal([num_symbols, num_rx_ant], dtype=tf.float32)
        noise_imag = tf.random.normal([num_symbols, num_rx_ant], dtype=tf.float32)
        noise = tf.complex(noise_real, noise_imag) * tf.cast(tf.sqrt(no / 2), tf.complex64)

        tx = tf.reshape(tx, [num_symbols, num_tx_ant])
        y = tf.squeeze(tf.matmul(h, tx[:, :, None]), axis=-1) + noise

        # Maximal Ratio Combining (MRC)
        h_total = h[:, :, 0]  # [num_symbols, num_rx_ant]
        h_power = tf.reduce_sum(tf.abs(h_total)**2, axis=1, keepdims=True)  # Total channel power
        h_conj = tf.math.conj(h_total)
        # MRC: sum weighted by conjugate channel, then normalize by total power
        combined = tf.reduce_sum(h_conj * y, axis=1) / tf.cast(tf.squeeze(h_power), tf.complex64)

        # Hard decision (QPSK)
        rx_bits_i = tf.cast(tf.math.real(combined) < 0, tf.int32)
        rx_bits_q = tf.cast(tf.math.imag(combined) < 0, tf.int32)
        rx_bits = tf.reshape(tf.stack([rx_bits_i, rx_bits_q], axis=1), [-1])

        # Original bits
        tx_bits = tf.reshape(tf.stack([(idx // 2) % 2, idx % 2], axis=1), [-1])

        # Compute BER
        bit_errors = tf.reduce_sum(tf.cast(rx_bits != tx_bits, tf.float32))
        ber = bit_errors / tf.cast(num_bits, tf.float32)
        ber_dict[snr_db] = ber.numpy()

    return ber_dict

def compare_mimo_performance(siso_config=[1,1], mimo_config=[2,2], num_bits=100000):
    """
    Compare SISO vs MIMO performance by running both simulations.
    Args:
        siso_config: [num_tx_ant, num_rx_ant] for SISO (default [1,1])
        mimo_config: [num_tx_ant, num_rx_ant] for MIMO (default [2,2])
        num_bits: total bits to transmit
    Returns:
        dict with both results and labels
    """
    siso_ber = simulate_ber_mimo(num_tx_ant=siso_config[0], num_rx_ant=siso_config[1], num_bits=num_bits)
    mimo_ber = simulate_ber_mimo(num_tx_ant=mimo_config[0], num_rx_ant=mimo_config[1], num_bits=num_bits)
    
    return {
        "siso": {"config": f"{siso_config[0]}x{siso_config[1]}", "ber": siso_ber},
        "mimo": {"config": f"{mimo_config[0]}x{mimo_config[1]}", "ber": mimo_ber}
    }
