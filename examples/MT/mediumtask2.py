import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt


def simulate_ber_for_nt(num_tx_ant, num_rx_ant=16, num_bits=200000):
    # QPSK constellation (complex64)
    const_points = tf.constant(
        [1+1j, 1-1j, -1+1j, -1-1j],
        dtype=tf.complex64
    ) / tf.complex(tf.sqrt(tf.constant(2.0, dtype=tf.float32)), 0.0)

    bits_per_symbol = 2
    snr_dbs = np.arange(0, 21, 2)
    ber_list = []

    for snr_db in snr_dbs:
        num_symbols = num_bits // bits_per_symbol

        # Random QPSK mapping indices
        idx = tf.random.uniform([num_symbols], minval=0, maxval=4, dtype=tf.int32)
        tx_syms = tf.gather(const_points, idx)

        # Repeat symbols across Nt antennas
        x = tf.tile(tf.reshape(tx_syms, [-1, 1]), [1, num_tx_ant])

        # Rayleigh channel - float32 only
        h_real = tf.random.normal(
            [num_symbols, num_rx_ant, num_tx_ant],
            dtype=tf.float32
        )
        h_imag = tf.random.normal(
            [num_symbols, num_rx_ant, num_tx_ant],
            dtype=tf.float32
        )

        h = tf.complex(h_real, h_imag) / tf.complex(
            tf.sqrt(tf.constant(2.0, dtype=tf.float32)), 0.0
        )

        # Received signal y = Hx + n
        y = tf.reduce_sum(h * tf.expand_dims(x, 1), axis=2)

        # Noise (float32 ONLY)
        snr_lin = tf.constant(10 ** (snr_db / 10), dtype=tf.float32)
        noise_var = 1.0 / snr_lin  # float32

        n_real = tf.random.normal(tf.shape(y), dtype=tf.float32)
        n_imag = tf.random.normal(tf.shape(y), dtype=tf.float32)

        n = tf.complex(n_real, n_imag) * tf.complex(
            tf.sqrt(noise_var / 2.0), 0.0
        )

        y_noisy = y + n

        # MRC combining using 1st Tx stream
        h0 = h[:, :, 0]               # Nr antennas
        h0_conj = tf.math.conj(h0)

        combined = tf.reduce_sum(h0_conj * y_noisy, axis=1) / tf.cast(
            tf.reduce_sum(tf.abs(h0)**2, axis=1),
            tf.complex64
        )

        # Hard decision QPSK
        rx_bits_i = tf.cast(tf.math.real(combined) < 0, tf.int32)
        rx_bits_q = tf.cast(tf.math.imag(combined) < 0, tf.int32)
        rx_bits = tf.reshape(tf.stack([rx_bits_i, rx_bits_q], axis=1), [-1])

        # Ground truth bits
        tx_bits = tf.reshape(tf.stack([(idx // 2) % 2, idx % 2], axis=1), [-1])

        ber = tf.reduce_mean(tf.cast(rx_bits != tx_bits, tf.float32))
        ber_list.append(float(ber.numpy()))

    return snr_dbs, ber_list


def sweep_tx_antennas(nt_list, num_rx_ant=16):
    results = {}

    for nt in nt_list:
        snr_dbs, ber_list = simulate_ber_for_nt(nt, num_rx_ant=num_rx_ant)
        results[nt] = ber_list
        print(f"Nt={nt} simulation done.")

    # Plot
    plt.figure()
    for nt, ber_list in results.items():
        plt.semilogy(snr_dbs, ber_list, marker='o', label=f"Nt={nt}")
    plt.xlabel("SNR (dB)")
    plt.ylabel("BER")
    plt.title("BER vs SNR for Different Tx Antennas")
    plt.grid(True, which="both")
    plt.legend()
    plt.show()

    # Best Nt at 10 dB
    target_idx = list(snr_dbs).index(10)
    best_nt = min(results.keys(), key=lambda nt: results[nt][target_idx])
    print(f"Best Nt at 10 dB = {best_nt}")


if __name__ == "__main__":
    nt_list = [1, 2, 4, 8, 16, 32]
    sweep_tx_antennas(nt_list, num_rx_ant=16)
