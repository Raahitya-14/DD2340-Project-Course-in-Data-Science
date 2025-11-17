#!/usr/bin/env python3
"""Generate radio coverage map using free-space path loss"""
import matplotlib.pyplot as plt
import numpy as np

def generate_radio_map(tx_pos=[0,0,0], rx_pos=[100,0,0], metric="rss"):
    # Create grid
    x = np.linspace(-20, 120, 200)
    y = np.linspace(-50, 50, 150)
    X, Y = np.meshgrid(x, y)
    
    # Calculate distance from transmitter to each point
    dist = np.sqrt((X - tx_pos[0])**2 + (Y - tx_pos[1])**2 + 1e-6)  # avoid division by zero
    
    # Free-space path loss: RSS = Pt - 20*log10(4*pi*d/lambda)
    # Assuming frequency = 2.4 GHz, lambda = 0.125 m, Pt = 20 dBm
    wavelength = 0.125
    rss = 20 - 20 * np.log10(4 * np.pi * dist / wavelength)
    
    # Create plot
    fig, ax = plt.subplots(figsize=(12, 8))
    im = ax.contourf(X, Y, rss, levels=20, cmap='viridis')
    cbar = plt.colorbar(im, ax=ax, label='Received Signal Strength (dBm)')
    
    # Plot transmitter and receiver
    ax.scatter(tx_pos[0], tx_pos[1], color="blue", marker="^", s=300, 
               label="Transmitter", edgecolors='white', linewidths=3, zorder=10)
    ax.scatter(rx_pos[0], rx_pos[1], color="red", marker="o", s=250, 
               label="Receiver", edgecolors='white', linewidths=3, zorder=10)
    
    ax.set_xlabel('X Position (m)', fontsize=12)
    ax.set_ylabel('Y Position (m)', fontsize=12)
    ax.set_title('Free-Space Radio Coverage Map', fontsize=14)
    ax.legend(loc='upper right', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"outputs/radiomap_{metric}.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: outputs/radiomap_{metric}.png")

if __name__ == "__main__":
    import sys
    metric = sys.argv[1] if len(sys.argv) > 1 else "rss"
    tx_pos = [float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])] if len(sys.argv) > 4 else [0,0,0]
    rx_pos = [float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7])] if len(sys.argv) > 7 else [100,0,0]
    generate_radio_map(tx_pos, rx_pos, metric)
