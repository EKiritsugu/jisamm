"""
This file contains the code to run the systematic simulation for evaluation
of overiva and other algorithms.
"""
import os
import sys
import numpy as np
import pyroomacoustics as pra
import rrtools

# Get the data if needed
from get_data import get_data, samples_dir# 下载音频文件
from room_builder import random_room_builder, callback_noise_mixer

from arg_generators import generate

# Routines for manipulating audio samples
sys.path.append(samples_dir)
from generate_samples import sampling, wav_read_center

# find the absolute path to this file
base_dir = os.path.abspath(os.path.split(__file__)[0])# 当前文件夹目录


def init(parameters):
    parameters["base_dir"] = base_dir


def one_loop(args):
    global parameters

    import sys
    sys.path.append(parameters["base_dir"])
    from simulation_loop import run

    return run(args, parameters)


if __name__ == "__main__":

    rrtools.run(
        one_loop,
        generate,
        func_init=init,
        base_dir=base_dir,
        results_dir="data/",
        description="Simulation for OverIVA",
    )
