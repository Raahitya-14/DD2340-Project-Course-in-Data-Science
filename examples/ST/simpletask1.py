import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from sionna.phy.mapping import Constellation

# 1) 64-QAM constellation (6 bits/symbol), unit average power
const = Constellation("qam", num_bits_per_symbol=6, normalize=True)
M = const.num_points

# 2) Generate random transmit symbols
N = 2000
idx = tf.random.uniform([N], minval=0, maxval=M, dtype=tf.int32)
s  = tf.gather(const.points, idx)          # complex symbols, Es ≈ 1

def add_awgn(x, snr_db):
    """Add complex AWGN with Es/N0 = snr_db (since Es ≈ 1 after normalize=True)."""
    snr_lin   = 10.0**(snr_db/10.0)
    sigma2    = 1.0 / snr_lin              # noise variance per complex symbol
    sigma     = np.sqrt(sigma2/2.0)        # per real (I or Q) component
    n_real    = tf.random.normal(x.shape, stddev=sigma, dtype=tf.float32)
    n_imag    = tf.random.normal(x.shape, stddev=sigma, dtype=tf.float32)
    noise     = tf.complex(n_real, n_imag)
    return x + noise

snrs = [-5, 15]
rx = [add_awgn(s, snr) for snr in snrs]

# # 3) Plot with fixed axis limits so both panels are comparable
# plt.figure(figsize=(12,6))
# for i, snr in enumerate(snrs):
#     x = rx[i].numpy()
#     plt.subplot(1,2,i+1)
#     plt.scatter(x.real, x.imag, s=10, alpha=0.6)
#     plt.title(f"64-QAM with AWGN (SNR = {snr} dB)")
#     plt.xlabel("In-phase (I)"); plt.ylabel("Quadrature (Q)")
#     plt.axhline(0, ls="--", c="gray"); plt.axvline(0, ls="--", c="gray")
#     # Use the same limits for both so you actually see the -5 dB cloud
#     plt.xlim(-10, 10); plt.ylim(-10, 10)
#     plt.grid(True)


# Ideal 64-QAM reference points
ideal_points = const.points.numpy()

plt.figure(figsize=(12,6))
for i, snr in enumerate(snrs):
    x = rx[i].numpy()
    plt.subplot(1,2,i+1)
    # Noisy symbols
    plt.scatter(x.real, x.imag, s=10, alpha=0.6, label="Received symbols")
    # Ideal reference
    plt.scatter(ideal_points.real, ideal_points.imag, s=120, facecolors='none', 
                edgecolors='red', linewidths=2, label="Ideal constellation")
    
    plt.title(f"64-QAM Constellation with AWGN (SNR = {snr} dB)")
    plt.xlabel("In-phase (I)"); plt.ylabel("Quadrature (Q)")
    plt.axhline(0, ls="--", c="gray"); plt.axvline(0, ls="--", c="gray")
    plt.xlim(-10, 10); plt.ylim(-10, 10)
    plt.grid(True)
    plt.legend()

plt.tight_layout()
plt.savefig("64QAM")
print("Saved plot as 64QAM.png")
