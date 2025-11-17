#!/usr/bin/env python3
"""Generate radio coverage map using Sionna RT"""
import matplotlib.pyplot as plt
import os
from sionna.rt import load_scene, Transmitter, Receiver, PlanarArray, RadioMapSolver

def generate_radio_map(tx_pos=[0,0,0], rx_pos=[100,0,0], metric="rss"):
    scene = load_scene()
    
    scene.tx_array = PlanarArray(num_rows=1, num_cols=1, vertical_spacing=0.5,
                                 horizontal_spacing=0.5, pattern="tr38901", polarization="V")
    scene.rx_array = PlanarArray(num_rows=1, num_cols=1, vertical_spacing=0.5,
                                 horizontal_spacing=0.5, pattern="dipole", polarization="cross")
    
    tx = Transmitter(name="tx", position=tx_pos)
    scene.add(tx)
    
    rx = Receiver(name="rx", position=rx_pos)
    scene.add(rx)
    
    tx.look_at(rx)
    
    os.makedirs('outputs', exist_ok=True)
    
    # Calculate coverage area to include both TX and RX
    min_x = min(tx_pos[0], rx_pos[0]) - 50
    max_x = max(tx_pos[0], rx_pos[0]) + 50
    min_y = min(tx_pos[1], rx_pos[1]) - 50
    max_y = max(tx_pos[1], rx_pos[1]) + 50
    
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    size_x = max_x - min_x
    size_y = max_y - min_y
    
    rm_solver = RadioMapSolver()
    rm = rm_solver(scene, max_depth=3, samples_per_tx=10**6, cell_size=(2, 2),
                   center=[center_x, center_y, 1.5], size=[size_x, size_y], orientation=[0, 0, 0])
    
    rm.show(metric=metric)
    plt.scatter(tx_pos[0], tx_pos[1], color="blue", marker="^", s=300, 
               label="Transmitter", edgecolors='white', linewidths=3, zorder=10)
    plt.scatter(rx_pos[0], rx_pos[1], color="red", marker="o", s=250, 
               label="Receiver", edgecolors='white', linewidths=3, zorder=10)
    plt.legend()
    plt.savefig(f"outputs/radiomap_{metric}.png")
    plt.close()
    print(f"Saved: outputs/radiomap_{metric}.png")

if __name__ == "__main__":
    import sys
    metric = sys.argv[1] if len(sys.argv) > 1 else "rss"
    tx_pos = [float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])] if len(sys.argv) > 4 else [0,0,0]
    rx_pos = [float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7])] if len(sys.argv) > 7 else [100,0,0]
    generate_radio_map(tx_pos, rx_pos, metric)
