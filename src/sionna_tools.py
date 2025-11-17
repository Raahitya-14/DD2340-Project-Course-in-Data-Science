"""Sionna simulation tools wrapper"""
import os
import subprocess
import numpy as np
import tensorflow as tf
from sionna.phy.mapping import Constellation
from sionna.phy.channel.awgn import AWGN
from sionna.phy.channel.rayleigh_block_fading import RayleighBlockFading
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
    script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "run_radiomap.py")
    result = subprocess.run(["python3", script_path, metric, 
                           str(tx_position[0]), str(tx_position[1]), str(tx_position[2]),
                           str(rx_position[0]), str(rx_position[1]), str(rx_position[2])],
                          capture_output=True, text=True)
    
    return {
        "tx_position": tx_position,
        "rx_position": rx_position,
        "metric": metric,
        "output": result.stdout,
        "plot_path": f"outputs/radiomap_{metric}.png"
    }

def list_available_tools():
    """List all available simulation tools"""
    return {
        "simulate_constellation": "Generate constellation diagrams with AWGN",
        "simulate_ber": "Calculate Bit Error Rate for different channels",
        "simulate_radio_map": "Generate radio coverage map using ray tracing",
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

