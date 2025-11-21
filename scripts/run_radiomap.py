#!/usr/bin/env python3
"""Generate radio coverage map using Sionna RT"""
import argparse
import json
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os
from typing import List
from sionna.rt import load_scene, Transmitter, Receiver, PlanarArray, RadioMapSolver


def _ensure_position_list(positions):
    if positions is None:
        return [[0, 0, 0]]
    if not positions:
        return [[0, 0, 0]]
    if isinstance(positions[0], (int, float)):
        return [positions]
    return positions


def _positions_slug(prefix: str, positions: List[List[float]]) -> str:
    parts = ["{}_{}_{}".format(pos[0], pos[1], pos[2]) for pos in positions]
    return f"{prefix}{'__'.join(parts)}"


def generate_radio_map(tx_positions=None, rx_positions=None, metric="rss"):
    tx_positions = _ensure_position_list(tx_positions)
    rx_positions = _ensure_position_list(rx_positions)

    scene = load_scene()
    
    scene.tx_array = PlanarArray(num_rows=1, num_cols=1, vertical_spacing=0.5,
                                 horizontal_spacing=0.5, pattern="tr38901", polarization="V")
    scene.rx_array = PlanarArray(num_rows=1, num_cols=1, vertical_spacing=0.5,
                                 horizontal_spacing=0.5, pattern="dipole", polarization="cross")

    tx_objects = []
    for idx, tx_pos in enumerate(tx_positions):
        tx = Transmitter(name=f"tx_{idx}", position=tx_pos)
        scene.add(tx)
        tx_objects.append(tx)
    
    rx_objects = []
    for idx, rx_pos in enumerate(rx_positions):
        rx = Receiver(name=f"rx_{idx}", position=rx_pos)
        scene.add(rx)
        rx_objects.append(rx)
    
    if rx_objects:
        for tx in tx_objects:
            tx.look_at(rx_objects[0])
    
    # Ensure outputs directory exists at project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outputs_dir = os.path.join(project_root, 'outputs')
    os.makedirs(outputs_dir, exist_ok=True)
    
    # Calculate coverage area to include all TX and RX positions
    all_points = tx_positions + rx_positions
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    
    min_x = min(xs) - 50
    max_x = max(xs) + 50
    min_y = min(ys) - 50
    max_y = max(ys) + 50
    
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    size_x = max_x - min_x
    size_y = max_y - min_y
    
    rm_solver = RadioMapSolver()
    rm = rm_solver(scene, max_depth=3, samples_per_tx=10**6, cell_size=(2, 2),
                   center=[center_x, center_y, 1.5], size=[size_x, size_y], orientation=[0, 0, 0])
    
    rm.show(metric=metric)
    fig = plt.gcf()
    ax = plt.gca()
    fig.set_size_inches(9, 6)

    # Convert world coordinates (meters) into map cell coordinates so markers align with rm.show output.
    origin_x = center_x - size_x / 2
    origin_y = center_y - size_y / 2
    cell_size_x, cell_size_y = 2, 2

    def world_to_cell(position):
        return (
            (position[0] - origin_x) / cell_size_x,
            (position[1] - origin_y) / cell_size_y,
        )

    legend_entries = []
    for idx, tx_pos in enumerate(tx_positions):
        tx_cell = world_to_cell(tx_pos)
        plt.scatter(tx_cell[0], tx_cell[1], color="blue", marker="^", s=250,
                    label=f"Transmitter {idx+1}: {tuple(tx_pos)}", edgecolors='white', linewidths=2, zorder=10)
        legend_entries.append(f"TX{idx+1}: {tuple(tx_pos)}")
    for idx, rx_pos in enumerate(rx_positions):
        rx_cell = world_to_cell(rx_pos)
        plt.scatter(rx_cell[0], rx_cell[1], color="red", marker="o", s=200,
                    label=f"Receiver {idx+1}: {tuple(rx_pos)}", edgecolors='white', linewidths=2, zorder=10)
        legend_entries.append(f"RX{idx+1}: {tuple(rx_pos)}")

    # Replace axis labels with world coordinates (meters)
    ax.set_xlabel("X position (m)")
    ax.set_ylabel("Y position (m)")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda val, pos: f"{origin_x + val*cell_size_x:.0f}"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda val, pos: f"{origin_y + val*cell_size_y:.0f}"))

    # Reserve space on the right for colorbar + legend
    plt.subplots_adjust(right=0.7)
    plt.legend(
        loc="upper left",
        bbox_to_anchor=(1.25, 1.0),
        borderaxespad=0.0,
        title="Nodes",
        framealpha=0.95,
    )

    filename = f"radiomap_{metric}_{_positions_slug('tx', tx_positions)}_{_positions_slug('rx', rx_positions)}.png"
    output_path = os.path.join(outputs_dir, filename)
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")
    return output_path


def _load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("tx_positions"), data.get("rx_positions"), data.get("metric", "rss")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate radio coverage map.")
    parser.add_argument("metric", nargs="?", default="rss")
    parser.add_argument("legacy_args", nargs="*", help="Legacy single-TX arguments.")
    parser.add_argument("--config", help="Path to JSON config for multi-TX scenarios.")
    args = parser.parse_args()

    if args.config:
        tx_positions, rx_positions, metric = _load_config(args.config)
    else:
        metric = args.metric
        legacy = args.legacy_args
        tx_positions = [list(map(float, legacy[0:3]))] if len(legacy) >= 3 else [[0,0,0]]
        rx_positions = [list(map(float, legacy[3:6]))] if len(legacy) >= 6 else [[100,0,0]]
    generate_radio_map(tx_positions, rx_positions, metric)
