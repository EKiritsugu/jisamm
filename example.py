
"""
Overdetermined Blind Source Separation offline example
======================================================

This script requires the `mir_eval` to run, and `tkinter` and `sounddevice` packages for the GUI option.
"""
import argparse
import json
import sys
import time

import matplotlib
import numpy as np
import pyroomacoustics as pra
from pyroomacoustics.bss import projection_back
from scipy.io import wavfile

import bss
# Get the data if needed
from get_data import get_data, samples_dir
from room_builder import (callback_noise_mixer, choose_target_locations,
                          convergence_callback, random_locations)
from routines import (PlaySoundGUI, grid_layout, random_layout,
                      semi_circle_layout)
from samples.generate_samples import sampling, wav_read_center

# Once we are sure the data is there, import some methods
# to select and read samples
sys.path.append(samples_dir)


# We concatenate a few samples to make them long enough
if __name__ == "__main__":

    algo_choices = list(bss.algos.keys())
    model_choices = ["laplace", "gauss"]
    init_choices = ["pca"]
    ogive_n_iter_default = 1000
    n_iter_default = 10

    parser = argparse.ArgumentParser(
        description="Demonstration of blind source extraction using FIVE."
    )
    parser.add_argument(
        "--no_cb", action="store_true", help="Removes callback function"
    )
    parser.add_argument("-b", "--block", type=int, default=2048, help="STFT block size")
    parser.add_argument(
        "-a",
        "--algo",
        type=str,
        default=algo_choices[0],
        choices=algo_choices,
        help="Chooses BSS method to run",
    )
    parser.add_argument(
        "-d",
        "--dist",
        type=str,
        default=model_choices[0],
        choices=model_choices,
        help="IVA model distribution",
    )
    parser.add_argument(
        "-i",
        "--init",
        type=str,
        choices=init_choices,
        help="Initialization, eye: identity, eig: principal eigenvectors",
    )
    parser.add_argument("-m", "--mics", type=int, default=5, help="Number of mics")
    parser.add_argument("-s", "--srcs", type=int, default=1, help="Number of sources")
    parser.add_argument(
        "-z", "--interf", type=int, default=10, help="Number of interferers"
    )
    parser.add_argument(
        "--sinr", type=float, default=5, help="Signal-to-interference-and-noise ratio"
    )
    parser.add_argument(
        "-n", "--n_iter", type=int, default=None, help="Number of iterations"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Creates a small GUI for easy playback of the sound samples",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Saves the output of the separation to wav files",
    )
    parser.add_argument("--seed", type=int, help="Random number generator seed")
    args = parser.parse_args()

    if args.gui:
        print("setting tkagg backend")
        # avoids a bug with tkinter and matplotlib
        import matplotlib

        matplotlib.use("TkAgg")

    import pyroomacoustics as pra

    # Simulation parameters
    fs = 16000
    absorption, max_order = 0.35, 17  # RT60 == 0.3
    # absorption, max_order = 0.45, 12  # RT60 == 0.2
    n_sources = args.srcs + args.interf
    n_mics = args.mics
    n_sources_target = args.srcs  # the single source case

    if bss.is_single_source[args.algo]:
        print("IVE only works with a single source. Using only one source.")
        n_sources_target = 1

    # fix the randomness for repeatability
    if args.seed is None:
        seed = np.random.randint(2 ** 31)
    else:
        seed = args.seed
    print(f"The RNG seed is {seed}")

    np.random.seed(seed)

    # set the source powers, the first one is half
    source_std = np.ones(n_sources_target)

    SINR = args.sinr  # signal-to-interference-and-noise ratio
    if args.interf == 0:
        SINR_diffuse_ratio = 0.0
    else:
        SINR_diffuse_ratio = 0.9999  # ratio of uncorrelated to diffuse noise
    ref_mic = 0  # the reference microphone for SINR and projection back
    # the distance between microphone array and targets as a ratio to the critical distance
    dist_ratio = 0.5

    # STFT parameters
    framesize = 512
    hop = framesize // 4
    window = "hamming"
    stft_params = {"framesize": framesize, "hop": hop, "window": window}
    if stft_params["window"] == "hann":
        win_a = pra.hamming(framesize)
    else:  # default is Hann
        win_a = pra.hann(framesize)
    win_s = pra.transform.stft.compute_synthesis_window(win_a, hop)

    # Process number of iterations
    if args.n_iter is None:
        if args.algo.startswith("ogive"):
            n_iter = ogive_n_iter_default
        else:
            n_iter = n_iter_default
    else:
        n_iter = args.n_iter

    # Force an even number of iterations
    if n_iter % 2 == 1:
        n_iter += 1

    # param ogive
    ogive_mu = 0.1

    # Geometry of the room and location of sources and microphones
    # Use the room model from experiment 2
    with open("experiment2_config.json", "r") as f:
        config = json.load(f)

    room_dim = config["room"]["room_kwargs"]["p"]
    mic_array_center = np.array(config["room"]["mic_array_location_m"])
    angles = np.arange(n_mics) * 2 * np.pi / (n_mics)
    rel_mics_locs = np.vstack(
        [
            0.02 * np.cos(angles),
            0.02 * np.sin(angles),
            np.zeros(n_mics),
        ]
    )
    mic_locs = mic_array_center[:, None] + rel_mics_locs
    critical_distance = config["room"]["critical_distance_m"]

    # all source locations
    target_locs = choose_target_locations(
        args.srcs, mic_array_center, dist_ratio * critical_distance
    )
    interferers_locs = random_locations(
        args.interf, room_dim, mic_array_center, min_dist=critical_distance
    )
    source_locs = np.concatenate((target_locs, interferers_locs), axis=1)

    # Prepare the signals
    wav_files = sampling(
        1,
        n_sources,
        f"{samples_dir}/metadata.json",
        gender_balanced=True,
        seed=np.random.randint(2 ** 31),
    )[0]
    signals = wav_read_center(wav_files, seed=123)

    # Create the room itself
    room = pra.ShoeBox(**config["room"]["room_kwargs"])

    # Place a source of white noise playing for 5 s
    for sig, loc in zip(signals, source_locs.T):
        room.add_source(loc, signal=sig)

    # Place the microphone array
    room.add_microphone_array(pra.MicrophoneArray(mic_locs, fs=room.fs))

    # compute RIRs
    room.compute_rir()

    # signals after propagation but before mixing
    # (n_sources, n_mics, n_samples)
    premix = room.simulate(return_premix=True)
    n_samples = premix.shape[-1]

    # create the mix (n_mics, n_samples)
    # this routine will also resize the signals in premix
    mix = callback_noise_mixer(
        premix,
        sinr=SINR,
        n_src=n_sources,
        n_tgt=n_sources_target,
        ref_mic=ref_mic,
        diffuse_ratio=SINR_diffuse_ratio,
    )

    # create the reference signals
    # (n_sources + 1, n_samples)
    refs = np.zeros((n_sources_target + 1, n_samples))
    refs[:-1, :] = premix[:n_sources_target, ref_mic, :]
    refs[-1, :] = np.sum(premix[n_sources_target:, ref_mic, :], axis=0)

    print("Simulation done.")

    # Monitor Convergence
    #####################

    SDR, SIR, cost_list, eval_time = [], [], [], []

    def cb_local(W, Y, source_model):
        convergence_callback(
            W,
            Y,
            source_model,
            X_mics,
            n_sources_target,
            SDR,
            SIR,
            cost_list,
            eval_time,
            refs,
            ref_mic,
            stft_params,
            args.algo,
            not bss.is_determined[args.algo],
        )

    if args.algo.startswith("ogive"):
        ogive_iter_step = n_iter // 20
        callback_checkpoints = list(
            range(ogive_iter_step, n_iter + ogive_iter_step, ogive_iter_step)
        )
    elif not bss.is_iterative[args.algo]:
        callback_checkpoints = [1]
    else:
        if bss.is_dual_update[args.algo]:
            callback_checkpoints = list(range(2, n_iter + 1, 2))
        else:
            callback_checkpoints = list(range(1, n_iter + 1))

    if args.no_cb:
        callback_checkpoints = [1]

    # START BSS
    ###########

    # shape: (n_frames, n_freq, n_mics)
    X_all = pra.transform.stft.analysis(mix.T, framesize, hop, win=win_a).astype(
        np.complex128
    )
    X_mics = X_all[:, :, :n_mics]

    tic = time.perf_counter()

    # First evaluation of SDR/SIR
    cb_local(np.eye(n_mics)[None, :, :], X_mics[:, :, :1], args.dist)

    Y, W = bss.separate(
        X_mics,
        algorithm=args.algo,
        n_src=n_sources_target,
        proj_back=False,
        n_iter=n_iter,
        return_filters=True,
        step_size=ogive_mu,
        model=args.dist,
        init=args.init,
        callback=cb_local,
        callback_checkpoints=callback_checkpoints,
    )

    # projection back
    Y = bss.project_back(Y, X_mics[:, :, 0])

    toc = time.perf_counter()

    tot_eval_time = sum(eval_time)

    print("Processing time: {:8.3f} s".format(toc - tic - tot_eval_time))
    print("Evaluation time: {:8.3f} s".format(tot_eval_time))

    # Run iSTFT
    if Y.shape[2] == 1:
        y = pra.transform.stft.synthesis(Y[:, :, 0], framesize, hop, win=win_s)[:, None]
    else:
        y = pra.transform.stft.synthesis(Y, framesize, hop, win=win_s)
    y = y[framesize - hop :, :].astype(np.float64)

    if args.algo != "blinkiva":
        new_ord = np.argsort(np.std(y, axis=0))[::-1]
        y = y[:, new_ord]

    y_hat = y[:, :n_sources_target]

    # Look at the result
    SDR = np.array(SDR)
    SIR = np.array(SIR)
    for s in range(n_sources_target):
        print(f"SDR: In: {SDR[0, s]:6.2f} dB -> Out: {SDR[-1, s]:6.2f} dB")
    for s in range(n_sources_target):
        print(f"SIR: In: {SIR[0, s]:6.2f} dB -> Out: {SIR[-1, s]:6.2f} dB")

    import matplotlib.pyplot as plt

    room.plot(img_order=0)

    plt.figure()

    plt.subplot(2, 1, 1)
    plt.specgram(mix[0], NFFT=1024, Fs=room.fs)
    plt.title("Microphone 0 input")

    plt.subplot(2, 1, 2)
    plt.specgram(y_hat[:, 0], NFFT=1024, Fs=room.fs)
    plt.title("Extracted source")

    plt.tight_layout(pad=0.5)

    plt.figure()
    plt.plot([0] + callback_checkpoints, cost_list)
    plt.title("Cost function")
    plt.xlabel("Iteration")
    plt.ylabel("Cost")
    plt.tight_layout(pad=0.5)

    plt.figure()
    for s in range(n_sources_target):
        plt.plot([0] + callback_checkpoints, SDR[:, s], label=f"SDR {s+1}", marker="*")
        plt.plot([0] + callback_checkpoints, SIR[:, s], label=f"SIR {s+1}", marker="o")
    plt.title(args.algo)
    plt.legend()
    plt.tight_layout(pad=0.5)

    if not args.gui:
        plt.show()
    else:
        plt.show(block=False)

    if args.save:
        wavfile.write(
            "bss_iva_mix.wav",
            room.fs,
            pra.normalize(mix[0, :], bits=16).astype(np.int16),
        )
        for i, sig in enumerate(y_hat):
            wavfile.write(
                "bss_iva_source{}.wav".format(i + 1),
                room.fs,
                pra.normalize(sig, bits=16).astype(np.int16),
            )

    if args.gui:

        from tkinter import Tk

        # Make a simple GUI to listen to the separated samples
        root = Tk()
        my_gui = PlaySoundGUI(
            root, room.fs, mix[0, :], y_hat.T, references=refs[:n_sources_target, :]
        )
        root.mainloop()
