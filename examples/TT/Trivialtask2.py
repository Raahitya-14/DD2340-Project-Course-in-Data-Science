import matplotlib.pyplot as plt
import tensorflow as tf
from sionna.phy.mapping import Constellation

# 1. Create a 16-QAM constellation (4 bits per symbol)
const = Constellation("qam", num_bits_per_symbol=4, normalize=True)

# 2. Extract constellation points (complex numbers)
symbols = const.points  # shape (16,), dtype=complex

# 3. Plot the constellation
plt.figure(figsize=(6,6))
plt.scatter(tf.math.real(symbols), tf.math.imag(symbols), s=100, c='blue')

# Add labels to each point (optional)
for i, point in enumerate(symbols.numpy()):
    plt.text(point.real+0.05, point.imag+0.05, str(i), fontsize=8)

# Plots
plt.axhline(0, color='gray', linestyle='--')
plt.axvline(0, color='gray', linestyle='--')
plt.title("Ideal 16-QAM Constellation (Sionna)")
plt.xlabel("In-phase (I)")
plt.ylabel("Quadrature (Q)")
plt.grid(True)
plt.savefig("16QAM")
print("Saved plot as 16QAM.png")
