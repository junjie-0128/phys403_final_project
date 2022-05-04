import numpy as np
import matplotlib.pyplot as plt
import argparse
import configparser

config = configparser.ConfigParser()
config.read('params.conf')
H0_INJECTED = float(config['simulation']['H_0_true'])
PRIOR_RANGE = [float(val) for val in config['physical']['H_0_prior'].split(sep=',')]

LC = "red"
ALPH = 0.3

parser = argparse.ArgumentParser(description="Generate our plots for the paper")
parser.add_argument("--posterior-files", nargs='+', help="The file containing information on posterior distributions as a function of number of detections. This file should be generated by a call to est_hubble.")
parser.add_argument("--output-directory", help="The directory to which plots should be saved")
parser.add_argument('--save-all', action='store_true', default=False, help="If specified, then plots of the posterior distribution on all data realizations will be saved. Otherwise, only the first is saved")
args = parser.parse_args()

def norm(p, dh):
    return np.sum(p) * dh

def mean(h, p, dh):
    return np.sum(h * p) * dh

def var(h, p, dh):
    mu = mean(h, p, dh)
    return np.sum((h - mu)**2 * p) * dh

n_realizations = len(args.posterior_files)
#keep track of the averages and standard deviations for each entry. This might end up being a ragged array, hence the list of numpy arrays
mus = [np.empty(0) for i in range(n_realizations)]
stds = [np.empty(0) for i in range(n_realizations)]
min_n_its = 0
#load the data from the specified files
for i, fname in enumerate(args.posterior_files):
    dat = np.loadtxt(fname)

    if i == 0 or dat.shape[0] < min_n_its:
        min_n_its = dat.shape[0]
    #initialize the arrays for the current realization
    mus[i] = np.empty(dat.shape[0])
    stds[i] = np.empty(dat.shape[0])

    #initialize arrays to store the pdf
    p = np.ones(dat.shape[1])
    h = np.linspace(PRIOR_RANGE[0], PRIOR_RANGE[1], dat.shape[1])
    dh = h[1] - h[0]

    #compute the mean and standard deviation for each number of detections in the given realization
    for j in range(dat.shape[0]):
        p *= dat[j]
        p /= norm(p, dh)
        mus[i][j] = mean(h, p, dh)
        stds[i][j] = np.sqrt(var(h, p, dh))

    #save the plot of the posterior distribution
    if i == 0 or args.save_all:
        fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(8, 6))
        for j in range(dat.shape[0]):
            ax1.plot(h, dat[j] / norm(dat[j], dh), color=LC, linewidth=0.5, alpha=0.5)
        ax2.plot(h, p, color=LC)
        ax2.set_xlabel("$H_0$ [km s$^{-1}$ Mpc$^{-1}]$", fontsize=14)
        ax1.set_ylabel("$p(H_0 | D)$", fontsize=14)
        ax2.set_ylabel("$p(H_0 | D)$ (cumulative)", fontsize=14)
        ax2.axvline(mus[i][-1], linestyle="--", color="black", linewidth=1.)
        ax2.axvline(mus[i][-1] - stds[i][-1], linestyle="--", color="black", linewidth=1.)
        ax2.axvline(mus[i][-1] + stds[i][-1], linestyle="--", color="black", linewidth=1.)
        ax2.axvline(H0_INJECTED, color="blue")
        plt.tight_layout()
        plt.savefig(args.output_directory + "/posterior_{}.pdf".format(i))

if min_n_its == 0:
    raise ValueError('At least one supplied posterior file must be nonempty')

#average the means and standard deviations over each instance
mu = np.zeros(min_n_its)
std = np.zeros(min_n_its)
mu_std = np.zeros(min_n_its)
std_std = np.zeros(min_n_its)
for j in range(min_n_its):
    #compute averages
    for row in mus:
        mu[j] += row[j]
    mu[j] /= n_realizations
    for row in stds:
        std[j] += row[j]
    std[j] /= n_realizations
    #compute variances
    for row in mus:
        mu_std[j] += (mu[j] - row[j])**2
    mu_std[j] = np.sqrt( mu_std[j] / (n_realizations-1) )
    for row in stds:
        std_std[j] += (std[j] - row[j])**2
    std_std[j] = np.sqrt( std_std[j] / (n_realizations-1) )

plt.figure(figsize=(8, 5))
plt.plot(std, color=LC)
plt.fill_between([i for i in range(min_n_its)], std-std_std, std+std_std, color=LC, alpha=ALPH)
plt.xlabel("Number of events", fontsize=14)
plt.ylabel("$\sigma_{H_0}$ [km s$^{-1}$ Mpc$^{-1}$]", fontsize=14)
plt.ylim(0., 35.)
plt.savefig(args.output_directory + "/std.pdf")

plt.figure(figsize=(8, 5))
plt.plot(mu - H0_INJECTED, color=LC)
plt.fill_between([i for i in range(min_n_its)], mu-H0_INJECTED-mu_std, mu-H0_INJECTED+mu_std, color=LC, alpha=ALPH)
plt.xlabel("Number of events", fontsize=14)
plt.ylabel("$\langle H_0 \\rangle - H_{0,{\\rm true}}$ [km s$^{-1}$ Mpc$^{-1}$]", fontsize=14)
plt.savefig(args.output_directory + "/diff.pdf")

plt.figure(figsize=(5, 5))
plt.scatter(mu, std, s=4., color="red")
plt.xlabel("$\langle H_0 \\rangle$ [km s$^{-1}$ Mpc$^{-1}$]", fontsize=14)
plt.ylabel("$\sigma_{H_0}$ [km s$^{-1}$ Mpc$^{-1}$]", fontsize=14)
plt.savefig(args.output_directory + "/correlation.pdf")
