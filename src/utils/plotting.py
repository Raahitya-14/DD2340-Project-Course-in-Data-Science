"""Plotting utilities for simulation results"""
import matplotlib.pyplot as plt

def plot_constellation(result):
    """Generate constellation diagram plot"""
    ideal = result['constellation']
    snr_levels = result['snr_levels']
    
    fig, axes = plt.subplots(1, len(snr_levels), figsize=(6*len(snr_levels), 5))
    if len(snr_levels) == 1:
        axes = [axes]
    
    for ax, (snr, rx) in zip(axes, snr_levels.items()):
        ax.scatter(rx.real, rx.imag, s=10, alpha=0.6, label='Received')
        ax.scatter(ideal.real, ideal.imag, s=100, facecolors='none', 
                  edgecolors='red', linewidths=2, label='Ideal')
        ax.set_title(f"{result['modulation']} at SNR={snr} dB")
        ax.set_xlabel("In-phase (I)")
        ax.set_ylabel("Quadrature (Q)")
        ax.grid(True)
        ax.legend()
        ax.axhline(0, ls='--', c='gray')
        ax.axvline(0, ls='--', c='gray')
    
    plt.tight_layout()
    return fig

def plot_ber(result):
    """Generate BER curve plot"""
    snr_list = sorted(result['ber'].keys())
    
    fig = plt.figure(figsize=(8, 6))
    for channel in ['awgn', 'rayleigh']:
        snr_vals = []
        ber_vals = []
        for snr in snr_list:
            ber = result['ber'][snr].get(channel)
            if ber is not None:
                snr_vals.append(snr)
                ber_vals.append(max(ber, 1e-6))
        if ber_vals:
            plt.semilogy(snr_vals, ber_vals, 'o-', label=channel.upper())
    
    plt.xlabel("SNR (dB)")
    plt.ylabel("Bit Error Rate (BER)")
    plt.title(f"{result['modulation']} BER Performance")
    plt.grid(True, which='both')
    plt.legend()
    plt.tight_layout()
    return fig

def save_plot(fig, filename, output_dir='outputs'):
    """Save plot to file"""
    import os
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    fig.savefig(filepath)
    return filepath
