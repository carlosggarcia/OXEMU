"""
Generates the training points: cosmological parameters (inputs) and linear matter power
spectrum (targets).

Author: Arrykrishna Mootoovaloo
Collaborators: David, Pedro, Jaime
Date: March 2022
Email: arrykrish@gmail.com/a.mootoovaloo17@imperial.ac.uk/arrykrishna.mootoovaloo@physics.ox.ac.uk
Project: Emulator for computing the linear matter power spectrum
"""
import os
from typing import Tuple
import scipy.stats
import pandas as pd

# our scripts and functions
from oxemu.src.cosmology import PowerSpectrum
import oxemu.utils.helpers as hp
import oxemu.config as CONFIG


def generate_prior(dictionary: dict) -> dict:
    """Generates the entity of each parameter by using scipy.stats function.

    Args:
        dictionary (dict): A dictionary with the specifications of the prior.

    Returns:
        dict: the prior distribution of the parameter.
    """
    dist = getattr(scipy.stats, dictionary['distribution'])(*dictionary['specs'])

    return dist


def scale_lhs(fname: str = 'lhs_500', save: bool = True) -> list:
    """Scale the Latin Hypercube Samples according to the prior range.

    Args:
        fname (str, optional): The name of the LHS file. Defaults to 'lhs_500'.
        save (bool): Whether to save the scaled LHS samples. Defaults to True.

    Returns:
        list: A list of dictionaries with the scaled LHS samples.
    """

    # read the LHS samples
    if '.csv' in fname:
        path = os.path.join('data', fname)
    else:
        path = os.path.join('data', fname + '.csv')

    lhs = pd.read_csv(path, index_col=[0])

    # number of training points
    ncosmo = lhs.shape[0]

    # create an empty list to store the cosmologies
    cosmo_list = list()

    # create an empty list to store the distributions
    priors = {}

    for param in CONFIG.COSMO:
        priors[param] = generate_prior(CONFIG.PRIORS[param])

    for i in range(ncosmo):
        # get the cosmological parameters
        cosmo = lhs.iloc[i, :]

        # scale the cosmological parameters
        cosmo = {CONFIG.COSMO[k]: priors[CONFIG.COSMO[k]].ppf(cosmo[k]) for k in range(len(CONFIG.COSMO))}

        # append to the list
        cosmo_list.append(cosmo)

    if save:
        cosmos_df = pd.DataFrame(cosmo_list)
        hp.save_csv(cosmos_df, 'data', 'cosmologies')
        hp.save_list(cosmo_list, 'data', 'cosmologies')

    return cosmo_list


def pk_linear(fname: str, redshift: float = 0.0) -> Tuple[list, list]:
    """Generates the linear matter power spectrum.

    Args:
        fname (str): The name of the file.
        redshift (float): The redshift. Defaults to 0.0.

    Returns:
        Tuple[list, list]: A list of the cosmological parameters and
        correponding list of the linear matter power spectrum.
    """

    # scale the LHS points to the cosmological parameters
    cosmologies = scale_lhs(fname, save=True)

    # class to compute the linear matter power spectrum
    module = PowerSpectrum(CONFIG.Z_MIN, CONFIG.Z_MAX, CONFIG.K_MIN, CONFIG.K_MAX)

    pk_lin = list()

    for cosmo in cosmologies:

        pk_lin.append(module.pk_linear(cosmo, redshift))

    # save the results to a csv file
    pk_lin_df = pd.DataFrame(pk_lin)
    hp.save_csv(pk_lin_df, 'data', 'pk_linear')
    hp.save_list(pk_lin, 'data', 'pk_linear')

    return cosmologies, pk_lin
