#!/usr/bin/env python3
"""Generate radio coverage map using Sionna RT"""
import matplotlib.pyplot as plt
from sionna.rt import load_scene, Transmitter, Receiver, PlanarArray, RadioMapSolver

def generate_radio_map(tx_pos=[0,0,0], rx_pos=[100,0,0], metric="rss"):
    scene = load_scene()
    
    scene.tx_array = PlanarArray(num_rows=1, num_cols=1, vertical_spacing=0.5,
                                 horizontal_spacing=0.5, pattern="tr38901", polarization="V")
    scene.rx_array = PlanarArray(num_rows=1, num_cols=1, vertical_spacing=0.5,
                                 horizontal_spacing=0.5, pattern="dipole", polarization="cross")
    
    tx = Transmitter(name="tx", position=tx_pos, display_radius=2)
    scene.add(tx)
    
    rx = Receiver(name="rx", position=rx_pos, display_radius=2)
    scene.add(rx)
    
    tx.look_at(rx)
    
    rm_solver = RadioMapSolver()
    rm = rm_solver(scene, max_depth=5, samples_per_tx=10**7, cell_size=(5, 5),
                   center=[-10, -10, -10], size=[400, 400], orientation=[0, 0, 0])
    
    rm.show(metric=metric)
    plt.scatter(rx_pos[0], rx_pos[1], color="red", marker="o", s=100, label="Receiver")
    plt.legend()
    plt.savefig(f"outputs/radiomap_{metric}.png")
    print(f"Saved: outputs/radiomap_{metric}.png")

if __name__ == "__main__":
    import sys
    metric = sys.argv[1] if len(sys.argv) > 1 else "rss"
    tx_pos = [float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])] if len(sys.argv) > 4 else [0,0,0]
    rx_pos = [float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7])] if len(sys.argv) > 7 else [100,0,0]
    generate_radio_map(tx_pos, rx_pos, metric)
