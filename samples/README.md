CMU ARCTIC Concat15
===================

This dataset contains 140 samples formed by concatening utterances from the
[CMU ARCTIC speech corpus](http://festvox.org/cmu_arctic/) [1]. The dataset is
male/female balanced and contains 7 of each. There are in addition 10 samples
for each speaker. A single sample was formed by concatenating samples from the
CMU ARCTIC corpus until the length exceeds 15 seconds.

The following speakers were selected

* female: axb, clb, eey, ljm, lnh, slp, slt,
* male: aew, ahw, aup, awb, bdl, fem, gka.

Use the dataset
---------------

A JSON file containing the metadata is provided. The file is structured as follows.

    {
      "fs": <sampling rate>,
      "files": [
        "first_file.wav",
        <all the other files>
      ],
      "sorted": {
        "male": {
            "aew": [
                "cmu_arctic_male_aew_1.wav",
                <rest of this speaker's files>
            ],
            <rest of the male speakers>
        },
        "female": {
            <all the female speakers similar to male speakers>
        }
      }
    }

There are two functions provided to help selecting the files, `sampling` and `wav_read_center`.
The first will select a number of distinct subset of speakers.

    sampling(num_subsets, num_speakers, metadata_file, gender_balanced=False, seed=None):

    This function will pick automatically and at random subsets
    speech samples from a list generated using this file.

    Parameters
    ----------
    num_subsets: int
        Number of subsets to create
    num_speakers: int
        Number of distinct speakers desired in a subset
    metadata_file: str
        Location of the metadata file
    gender_balanced: bool, optional
        If True, the subsets will have a the same number of male/female speakers
        when `num_speakers` is even, and one extra male, when `num_speakers` is odd.
        Default is `False`.
    seed: int, optional
        When a seed is provided, the random number generator is fixed to a deterministic
        state. This is useful for getting consistently the same set of speakers.
        The initial state of the random number generator is restored at the end of the function.
        When not provided, the random number generator is used without setting the seed.

    Returns
    -------
    A list of `num_subsets` lists of wav filenames, each containing `num_speakers` entries.

The second reads a bunch of wav files, adjust their length so that they're all the same size
and puts them in a numpy array.

    wav_read_center(wav_list, center=True, seed=None):

    Read a bunch of wav files, equalize their length
    and puts them in a numpy array

    Parameters
    ----------
    wav_list: list of str
        A list of file names, the file names should be of format wav and monaural
    center: bool, optional
        When True (default), the signals will be centered, otherwise, only their end will be zero padded
    seed: int
        Provides a seed for the random number generator. When this is provided,
        center option is ignored and the beginning of segments is placed at
        random within the maximum length available

    Returns
    -------
    ndarray (n_files, n_samples)
        A 2D array that contains one signal per row
    '''

So a typical use could be like this.

    from generate_samples import sampling, wav_read_center

    # Create 10 groups of 3 speakers, deterministic
    groups = sampling(10, 3, "metadata.json", seed=0)

    # Read all the sound files in the first group
    # shape: (n_signals, n_samples)
    signals = wav_read_center(groups[0])


Generate the dataset
--------------------

The dataset was generated with the `generate_samples.py` script which relies on
`numpy`, `scipy`, and `pyroomacoustics`.  It can be re-generated with the
following command.

    python ./generate_samples.py -s 7 -n 10 -d 15 [--cmudir /path/to/CMU/corpus]

If the `--cmudir` option is not provided, the whole CMU ARCTIC corpus will be
downloaded automatically. Also, the dataset will be cached in a file called `cmu_arctic.dat`.
This file takes about a gigabyte of disk space, so you might want to remove it when you're done.


References
----------

[1]	J. Kominek and A. W. Black, ["CMU ARCTIC databases for speech synthesis,"](http://festvox.org/cmu_arctic/cmu_arctic_report.pdf) CMU-LTI-03-177, 2003.
