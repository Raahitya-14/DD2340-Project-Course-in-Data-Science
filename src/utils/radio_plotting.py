"""Plotting utilities for radio map results"""
import matplotlib.pyplot as plt

def plot_radio_map(result):
    """Generate radio coverage map plot"""
    rm = result['radio_map']
    metric = result['metric']
    
    fig = plt.figure(figsize=(10, 8))
    rm.show(metric=metric)
    
    # Add transmitter and receiver markers
    tx_pos = result['tx_position']
    rx_pos = result['rx_position']
    plt.scatter(tx_pos[0], tx_pos[1], color='red', marker='^', s=200, 
                label='Transmitter', zorder=10, edgecolors='black', linewidths=2)
    plt.scatter(rx_pos[0], rx_pos[1], color='blue', marker='o', s=200, 
                label='Receiver', zorder=10, edgecolors='black', linewidths=2)
    
    plt.title(f"Radio Coverage Map - {metric.upper()}")
    plt.legend()
    plt.tight_layout()
    
    return fig
