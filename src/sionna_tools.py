"""Sionna simulation tools wrapper"""
import numpy as np
import tensorflow as tf
from sionna.phy.mapping import Constellation
from sionna.phy.channel.awgn import AWGN
from sionna.phy.channel.rayleigh_block_fading import RayleighBlockFading

def simulate_constellation(modulation="qam", bits_per_symbol=2, num_symbols=2000, snr_db_list=[-5, 15]):
    """Generate constellation with AWGN at different SNR levels"""
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

def list_available_modulations():
    """List supported modulation schemes"""
    return ["qam", "pam", "psk"]

def simulate_radio_map(tx_position=[0,0,0], rx_position=[100,0,0], metric="rss"):
    """Generate radio coverage map using ray tracing (runs external script)"""
    import subprocess
    import os
    
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
        "constellation": "Generate constellation diagrams with AWGN",
        "ber": "Calculate Bit Error Rate for different channels",
        "radio_map": "Generate radio coverage map using ray tracing",
        "modulations": "List available modulation schemes"
    }

def get_modulation_info(modulation="qam", bits_per_symbol=2):
    """Get information about a modulation scheme"""
    # Handle QPSK and PSK aliases
    mod_lower = modulation.lower()
    if mod_lower in ["qpsk", "psk"]:
        modulation = "qam"  # QPSK = 4-QAM
        bits_per_symbol = 2
    elif mod_lower == "bpsk":
        modulation = "pam"  # BPSK = 2-PAM
        bits_per_symbol = 1
    
    const = Constellation(modulation, num_bits_per_symbol=bits_per_symbol, normalize=True)
    return {
        "modulation": f"{2**bits_per_symbol}-{modulation.upper()}",
        "num_points": const.num_points,
        "bits_per_symbol": bits_per_symbol,
        "points": const.points.numpy().tolist()
    }


