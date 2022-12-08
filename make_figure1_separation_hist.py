"""
This script takes the output from the simulation and produces a number of plots
used in the publication.
"""
import argparse
import json
import os
import sys
import warnings

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import MaxNLocator

from data_loader import load_data

matplotlib.rc("pdf", fonttype=42)


if __name__ == "__main__":

    # parse arguments
    parser = argparse.ArgumentParser(
        description="Plot the data simulated by separake_near_wall"
    )
    parser.add_argument(
        "-p",
        "--pickle",
        action="store_true",
        help="Read the aggregated data table from a pickle cache",
    )
    parser.add_argument(
        "-s",
        "--show",
        action="store_true",
        help="Display the plots at the end of data analysis",
    )
    parser.add_argument(
        "dirs",
        type=str,
        nargs="+",
        metavar="DIR",
        help="The directory containing the simulation output files.",
    )# 没错这个比较重要

    cli_args = parser.parse_args()
    plot_flag = cli_args.show
    pickle_flag = cli_args.pickle

    df, rt60, parameters = load_data(cli_args.dirs, pickle=pickle_flag)

    # Draw the figure
    print("Plotting...")

    # sns.set(style='whitegrid')
    # sns.plotting_context(context='poster', font_scale=2.)
    # pal = sns.cubehelix_palette(8, start=0.5, rot=-.75)

    df_melt = df.melt(id_vars=df.columns[:-5], var_name="metric")
    # df_melt = df_melt.replace(substitutions)

    # Aggregate the convergence curves
    df_agg = (
        df_melt.groupby(
            by=[
                "Algorithm",
                "Sources",
                "Interferers",
                "SINR",
                "Mics",
                "Iteration",
                "metric",
            ]
        )
        .mean()
        .reset_index()
    )

    all_algos = [
        "OverIVA-IP",
        "OverIVA-IP-NP",
        "OverIVA-IP2",
        "OverIVA-IP2-NP",
        "OverIVA-DX/BG",
        "FIVE",
        "OGIVEs",
        "AuxIVA-IP",
        "AuxIVA-IP2",
    ]

    sns.set(
        style="whitegrid",
        context="paper",
        font_scale=0.75,
        rc={
            # 'figure.figsize': (3.39, 3.15),
            "lines.linewidth": 1.0,
            # 'font.family': 'sans-serif',
            # 'font.sans-serif': [u'Helvetica'],
            # 'text.usetex': False,
        },
    )
    pal = sns.cubehelix_palette(
        4, start=0.5, rot=-0.5, dark=0.3, light=0.75, reverse=True, hue=1.0
    )
    sns.set_palette(pal)

    if not os.path.exists("figures"):
        os.mkdir("figures")

    fig_dir = "figures/{}_{}_{}".format(
        parameters["name"], parameters["_date"], parameters["_git_sha"]
    )

    if not os.path.exists(fig_dir):
        os.mkdir(fig_dir)

    plt_kwargs = {
        # "improvements": {"ylim": [-5.5, 20.5], "yticks": [-5, 0, 5, 10, 15]},
        # "raw": {"ylim": [-5.5, 20.5], "yticks": [-5, 0, 5, 10, 15]},
        # "runtime": {"ylim": [-0.5, 40.5], "yticks": [0, 10, 20, 30]},
    }

    full_width = 6.93  # inches, == 17.6 cm, double column width
    half_width = 3.35  # inches, == 8.5 cm, single column width

    # Third figure
    # Classic # of microphones vs metric (box-plots ?)
    the_metrics = {
        "improvements": ["\u0394SI-SDR [dB]", "\u0394SI-SIR [dB]"],
        "raw": ["SI-SDR [dB]", "SI-SIR [dB]"],
    }

    # width = aspect * height
    aspect = 1.5  # width / height
    height = full_width / aspect
    height = 1.6

    sinr = parameters["sinr"][0]
    iteration_index = 12
    n_interferers = 10

    for m_name in the_metrics.keys():

        metric = the_metrics[m_name]

        select = (
            np.logical_or(df_melt["Iteration"] == 100, df_melt["Iteration"] == 2000)
            & (df_melt["Interferers"] == n_interferers)
            & (df_melt["SINR"] == sinr)
            & df_melt.metric.isin(metric)
        )

        fig = plt.figure()
        g = sns.catplot(
            data=df_melt[select],
            x="Mics",
            y="value",
            hue="Algorithm",
            row="Sources",
            col="metric",
            col_order=metric,
            hue_order=all_algos,
            kind="box",
            legend=False,
            aspect=aspect,
            height=height,
            linewidth=0.5,
            fliersize=0.3,
            # whis=np.inf,
            sharey="row",
            # size=3, aspect=0.65,
            margin_titles=True,
        )

        g.set(clip_on=False)
        # remove original titles before adding custom ones
        [plt.setp(ax.texts, text="") for ax in g.axes.flat]
        g.set_titles(row_template="{row_name} Sources", col_template="{col_name}")
        g.set_ylabels("Decibels")

        all_artists = []

        # left_ax = g.facet_axis(2, 0)
        left_ax = g.facet_axis(2, 0)
        leg = left_ax.legend(
            title="Algorithms",
            frameon=True,
            framealpha=0.85,
            fontsize="x-small",
            loc="lower left",
            # bbox_to_anchor=[-0.08, 1.08],
        )
        leg.get_frame().set_linewidth(0.2)
        all_artists.append(leg)

        sns.despine(offset=10, trim=False, left=True, bottom=True)

        plt.tight_layout()

        """
        for c, lbl in enumerate(metric):
            g_ax = g.facet_axis(0, c)
            g_ax.set_ylabel(lbl)
        """

        for ext in ["pdf", "png"]:
            fig_fn = os.path.join(
                fig_dir, f"figure1_{m_name}_interf{n_interferers}_sinr{sinr}.{ext}"
            )
            plt.savefig(
                fig_fn, bbox_extra_artists=all_artists
            )  # , bbox_inches="tight")
        plt.close()

    if plot_flag:
        plt.show()
