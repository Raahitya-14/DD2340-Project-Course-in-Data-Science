
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from sionna.phy.mapping import Constellation
from sionna.phy.channel.awgn import AWGN
from sionna.phy.channel.rayleigh_block_fading import RayleighBlockFading

# QPSK constellation (2 bits per symbol)
const = Constellation("qam", num_bits_per_symbol=2, normalize=True)

# Channels
awgn = AWGN()
rayleigh = RayleighBlockFading(num_rx=1, num_rx_ant=1, num_tx=1, num_tx_ant=1)

def simulate_ber(snr_db, num_bits=10000):
    # 1. Generate random QPSK symbols
    num_symbols = num_bits // 2
    idx = tf.random.uniform([num_symbols], minval=0, maxval=const.num_points, dtype=tf.int32)
    tx = tf.gather(const.points, idx)

    # 2. Compute noise variance
    snr_lin = 10**(snr_db/10)
    no = tf.constant(1/snr_lin, dtype=tf.float32)  # Es=1

    # 3. Pass through AWGN
    rx_awgn = awgn(tx, no)

    # 4. Pass through Rayleigh fading + AWGN
    h, _ = rayleigh(batch_size=num_symbols, num_time_steps=1)
    h = tf.squeeze(h)  # fading coefficients
    rx_rayleigh = awgn(h * tx, no)
    rx_rayleigh = rx_rayleigh / h 

    # 5. Nearest-neighbor demodulation
    def demodulate(rx):
        rx = tf.reshape(rx, [-1,1])
        distances = tf.abs(rx - const.points[None,:])**2
        return tf.argmin(distances, axis=1)

    idx_awgn = tf.cast(demodulate(rx_awgn), tf.int32)
    idx_rayleigh = tf.cast(demodulate(rx_rayleigh), tf.int32)
    idx = tf.cast(idx, tf.int32)

    # 6. Compute BER (SER × 2 bits/symbol)
    ser_awgn = tf.reduce_mean(tf.cast(idx_awgn != idx, tf.float32)).numpy()
    ser_rayleigh = tf.reduce_mean(tf.cast(idx_rayleigh != idx, tf.float32)).numpy()
    ber_awgn = ser_awgn * 2
    ber_rayleigh = ser_rayleigh * 2

    return ber_awgn, ber_rayleigh

# Run for -5 dB and 15 dB
snrs = [-5, 15]
ber_awgn_list, ber_rayleigh_list = [], []

for snr in snrs:
    ber_awgn, ber_rayleigh = simulate_ber(snr)
    ber_awgn_list.append(ber_awgn)
    ber_rayleigh_list.append(ber_rayleigh)

# Plot results
plt.figure(figsize=(7,5))
plt.plot(snrs, ber_awgn_list, 'o-', label="AWGN")
plt.plot(snrs, ber_rayleigh_list, 's-', label="Rayleigh fading")
plt.xlabel("SNR (dB)")
plt.ylabel("Bit Error Rate (BER)")
plt.title("QPSK BER under AWGN vs Rayleigh")
plt.legend()
plt.grid(True)

plt.savefig("QPSK.png")
print("Saved plot as QPSK.png")
