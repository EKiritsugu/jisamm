"""
This package contains the main algorithms for
overdetermined independent vector analysis
"""

from . import default
from .auxiva_pca import auxiva_pca
from .fastiva import fastiva
from .five import five
from .ogive import ogive, ogive_demix, ogive_mix, ogive_switch
from .overiva import (auxiva, auxiva2, overiva, overiva_demix_bg,
                      overiva_ip2_block, overiva_ip2_param, overiva_ip_block,
                      overiva_ip_param)
from .pca import pca
from .projection_back import project_back
from .utils import cost_iva


from .ilrma_t_function import *

algos = {
    "auxiva": auxiva,
    "auxiva2": auxiva2,
    "overiva": overiva,
    "overiva-ip": overiva_ip_param,
    "overiva-ip2": overiva_ip2_param,
    "overiva-ip-block": overiva_ip_block,
    "overiva-ip2-block": overiva_ip2_block,
    "overiva-demix-bg": overiva_demix_bg,
    "five": five,
    "ogive": ogive,
    "ogive-mix": ogive_mix,
    "ogive-demix": ogive_demix,
    "ogive-switch": ogive_switch,
    "auxiva-pca": auxiva_pca,
    "pca": pca,
    "fastiva": fastiva,
}


algos_init = {
    "pca": pca,
}


def separate(
    X,
    algorithm="overiva",
    proj_back=True,
    return_filters=False,
    init=None,
    init_kwargs={},
    **kwargs
):

    n_frames, n_freq, n_chan = X.shape

    if init is not None:
        X0, W0 = algos_init[init](X, return_filters=True, **init_kwargs)
    else:
        X0 = X
        W0 = None

    
    import pyroomacoustics as pra
    if algorithm == 'ilrma-t-IP':
        Y = ilrma_t_iss_joint(X, proj_back=False, return_filters=True, **kwargs)
    elif algorithm == 'ilrma-t-iss-seq':
        Y = ilrma_t_iss_seq(X, proj_back=False, return_filters=True, **kwargs)
    elif algorithm == 'ilrma-t-iss-joint':
        Y = ilrma_t_iss_joint(X, proj_back=False, return_filters=True, **kwargs)
    elif algorithm == 'ilrma-IP':
        Y = pra.bss.ilrma(X, proj_back=False, return_filters=True, **kwargs)
    # elif algorithm == 'ilrma-iss':
    #     from ilrma_iss import ilrma_iss

    #     Y = ilrma_iss(X, proj_back=False, return_filters=True, **kwargs)
    # elif algorithm == 'auxiva':
    #     Y = pra.bss.auxiva(X, proj_back=False, return_filters=True, **kwargs)
    # elif algorithm == 'wpe+ilrma-IP':
    #     from nara_wpe.wpe import wpe

    #     Y = wpe(X.transpose(1, 2, 0),
    #             taps=taps,
    #             delay=delay,
    #             iterations=50,
    #             statistics_mode='full'
    #             ).transpose(2, 0, 1)
    #     Y = pra.bss.ilrma(Y, n_iter=50)
    # elif algorithm == 'wpe_6':
    #     Y = wpe_v(X,
    #             taps=taps,
    #             delay=delay,
    #             iterations=iterations,
    #             )
    # elif algorithm == 'my_ilrma_t':
    #     Y = my_ilrma_t(X, proj_back=False, return_filters=True, **kwargs)
    # elif algorithm == 'my2_ilrma_t':
    #     Y = my2_ilrma_t(X, proj_back=False, return_filters=True, **kwargs)
    # elif algorithm == 'my3_ilrma_t':
    #     Y = my3_ilrma_t(X, proj_back=False, return_filters=True, **kwargs)
    # elif algorithm == 'my4_ilrma_t':
    #     Y = my4_ilrma_t(X, proj_back=False, return_filters=True, **kwargs)
    # elif algorithm == 'my5_ilrma_t':
    #     Y = my5_ilrma_t(X, proj_back=False, return_filters=True, **kwargs)

    else:
        Y, W = algos[algorithm](X0, proj_back=False, return_filters=True, **kwargs)

    if proj_back:
        Y = project_back(Y, X[:, :, 0])

    if return_filters:
        if W0 is not None:
            W = W @ W0
        return Y, W
    else:
        return Y


is_single_source = {
    "auxiva": False,
    "auxiva2": False,
    "overiva": False,
    "overiva-ip": False,
    "overiva-ip2": False,
    "overiva-ip-block": False,
    "overiva-ip2-block": False,
    "overiva-demix-bg": False,
    "auxiva-pca": False,
    "pca": False,
    "five": True,
    "ogive": True,
    "ogive-mix": True,
    "ogive-demix": True,
    "ogive-switch": True,
    "fastiva": False,
}

# This is a list that indicates which algorithms
# can only work with two or more sources
is_dual_update = {
    "auxiva": False,
    "auxiva2": True,
    "overiva": False,
    "overiva-ip": False,
    "overiva-ip2": True,
    "overiva-ip-block": False,
    "overiva-ip2-block": True,
    "overiva-demix-bg": False,
    "auxiva-pca": True,
    "pca": False,
    "five": False,
    "ogive": False,
    "ogive-mix": False,
    "ogive-demix": False,
    "ogive-switch": False,
    "fastiva": False,
}

is_determined = {
    "auxiva": True,
    "auxiva2": True,
    "overiva": False,
    "overiva-ip": False,
    "overiva-ip2": False,
    "overiva-ip-block": False,
    "overiva-ip2-block": False,
    "overiva-demix-bg": False,
    "auxiva-pca": False,
    "pca": False,
    "five": False,
    "ogive": False,
    "ogive-mix": False,
    "ogive-demix": False,
    "ogive-switch": False,
    "fastiva": False,
    "ilrma-t-ip":True,
    "ilrma-t-iss-joint":True,
    "ilrma-t-iss-seq":True
}

is_overdetermined = {
    "auxiva": False,
    "auxiva2": False,
    "overiva": True,
    "overiva-ip": True,
    "overiva-ip2": True,
    "overiva-ip-block": True,
    "overiva-ip2-block": True,
    "overiva-demix-bg": True,
    "auxiva-pca": True,
    "pca": False,
    "five": True,
    "ogive": True,
    "ogive-mix": True,
    "ogive-demix": True,
    "ogive-switch": True,
    "fastiva": True,
        "ilrma-t-ip":False,
    "ilrma-t-iss-joint":False,
    "ilrma-t-iss-seq":False
}

is_iterative = {
    "auxiva": True,
    "auxiva2": True,
    "overiva": True,
    "overiva-ip": True,
    "overiva-ip2": True,
    "overiva-ip-block": True,
    "overiva-ip2-block": True,
    "overiva-demix-bg": True,
    "auxiva-pca": True,
    "pca": False,
    "five": True,
    "ogive": True,
    "ogive-mix": True,
    "ogive-demix": True,
    "ogive-switch": True,
    "fastiva": True,
        "ilrma-t-ip":True,
    "ilrma-t-iss-joint":True,
    "ilrma-t-iss-seq":True
}
