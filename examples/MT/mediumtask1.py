import sionna as sn
import tensorflow as tf
import matplotlib.pyplot as plt
import numpy as np

def simulate_ber_mimo(num_tx_ant=1, num_rx_ant=1, num_bits=100000):

    # QPSK constellation
    #const_points = tf.constant([1+1j, 1-1j, -1+1j, -1-1j], dtype=tf.complex64) / tf.sqrt(2.0)
    const_points = tf.constant([1 + 1j, 1 - 1j, -1 + 1j, -1 - 1j], dtype=tf.complex64) / tf.cast(tf.sqrt(2.0),
                                                                                                 tf.complex64)

    bits_per_symbol = 2
    snr_dbs = range(0, 21, 2)  # 0~20dB, step 2
    ber_dict = {}

    for snr_db in snr_dbs:
        # SNR in linear scale
        snr_lin = 10 ** (snr_db / 10)
        no = tf.constant(1.0 / snr_lin, dtype=tf.float32)

        num_symbols = num_bits // bits_per_symbol

        idx = tf.random.uniform([num_symbols], 0, 4, dtype=tf.int32)
        tx = tf.gather(const_points, idx)  # shape [num_symbols]


        tx = tf.tile(tx[:, None], [1, num_tx_ant])  # [num_symbols, num_tx_ant]


        h_real = tf.random.normal([num_symbols, num_rx_ant, num_tx_ant], dtype=tf.float32)
        h_imag = tf.random.normal([num_symbols, num_rx_ant, num_tx_ant], dtype=tf.float32)

        h = tf.complex(h_real, h_imag) / tf.cast(tf.sqrt(2.0), tf.complex64)


        noise_real = tf.random.normal([num_symbols, num_rx_ant], dtype=tf.float32)
        noise_imag = tf.random.normal([num_symbols, num_rx_ant], dtype=tf.float32)
        noise = tf.complex(noise_real, noise_imag) * tf.cast(tf.sqrt(no / 2), tf.complex64)


        tx = tf.reshape(tx, [num_symbols, num_tx_ant])
        y = tf.squeeze(tf.matmul(h, tx[:, :, None]), axis=-1) + noise  # [num_symbols, num_rx_ant]

        h_conj = tf.math.conj(h[:, :, 0])
        #combined = tf.reduce_sum(h_conj * y, axis=1) / tf.reduce_sum(tf.abs(h[:, :, 0])**2, axis=1)
        combined = tf.reduce_sum(h_conj * y, axis=1) / tf.cast(tf.reduce_sum(tf.abs(h[:, :, 0]) ** 2, axis=1),
                                                               tf.complex64)

        # Hard decision (QPSK)
        rx_bits_i = tf.cast(tf.math.real(combined) < 0, tf.int32)
        rx_bits_q = tf.cast(tf.math.imag(combined) < 0, tf.int32)
        rx_bits = tf.reshape(tf.stack([rx_bits_i, rx_bits_q], axis=1), [-1])

        # Original bits
        tx_bits = tf.reshape(tf.stack([(idx // 2) % 2, idx % 2], axis=1), [-1])

        # Compute BER
        bit_errors = tf.reduce_sum(tf.cast(rx_bits != tx_bits, tf.float32))
        ber = bit_errors / tf.cast(num_bits, tf.float32)
        ber_dict[snr_db] = ber.numpy()

    return ber_dict

def plot_ber_comparison(single_ber, multi_ber):
    plt.figure()
    plt.semilogy(list(single_ber.keys()), list(single_ber.values()), 'o-', label="SISO (1x1)")
    plt.semilogy(list(multi_ber.keys()), list(multi_ber.values()), 's-', label="MIMO (2x2)")
    plt.xlabel("SNR (dB)")
    plt.ylabel("BER")
    plt.grid(True, which="both")
    plt.legend()
    plt.title("Impact of Multiple Antennas on Link Performance")
    plt.show()


single = simulate_ber_mimo(num_tx_ant=1, num_rx_ant=1)
multi  = simulate_ber_mimo(num_tx_ant=2, num_rx_ant=2)
plot_ber_comparison(single, multi)
