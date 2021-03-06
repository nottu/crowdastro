"""Runs the Raykar algorithm on a simulated crowd classification task.

Matthew Alger
The Australian National University
2016
"""

import argparse
import collections
import csv
import logging

import matplotlib
import matplotlib.pyplot as plt
import numpy
import sklearn
import sklearn.cross_validation

from . import runners
from .. import __version__
from ..crowd.raykar import majority_vote
from ..plot import vertical_scatter_ba
from .results import Results


def main(input_csv_path, results_h5_path, overwrite=False, plot=False,
         seed=0, shuffle_seed=0):
    numpy.random.seed(seed)
    with open(input_csv_path, 'r') as f:
        reader = csv.reader(f)
        features = []
        labels = []
        for row in reader:
            label = row[-1] == '4'
            labels.append(label)
            feature = [float(i) if i != '?' else 0 for i in row[1:-1]]
            features.append(feature)
        features = numpy.array(features)
        labels = numpy.array(labels)

        n_splits = 20
        n_labellers = 5
        mask_rate = 0.5  # Lower = less masked.
        n_examples, n_params = features.shape
        n_params += 1  # Bias term.
        n_params += n_labellers * 2  # α and β.
        methods = ['Raykar', 'LR']
        model = '{} crowdastro.crowd.raykar.RaykarClassifier,'.format(
                        __version__) + \
                '{} sklearn.linear_model.LogisticRegression'.format(
                        sklearn.__version__)

        results = Results(results_h5_path, methods, n_splits, n_examples,
                          n_params, model)

        # Generate the crowd labels. For each labeller, assign a true positive
        # rate and a false positive rate. Then flip labels based on these.
        true_positive_rates = numpy.linspace(0.25, 0.75, n_labellers)
        numpy.random.shuffle(true_positive_rates)
        false_positive_rates = numpy.linspace(0.25, 0.75, n_labellers)
        numpy.random.shuffle(false_positive_rates)
        crowd_labels = numpy.tile(labels, (n_labellers, 1))
        for labeller in range(n_labellers):
            for i in range(n_examples):
                if labels[i]:
                    if numpy.random.random() > true_positive_rates[labeller]:
                        crowd_labels[labeller, i] = 0
                else:
                    if numpy.random.random() < false_positive_rates[labeller]:
                        crowd_labels[labeller, i] = 1
        # Randomly mask a percentage of the elements.
        mask = numpy.random.binomial(1, mask_rate, size=crowd_labels.shape)
        crowd_labels = numpy.ma.MaskedArray(crowd_labels, mask=mask)
        # Compute a majority vote of the crowd labels to use for LR.
        mv = majority_vote(crowd_labels)

        all_features = {
            'Raykar': features,
            'LR': features,
        }
        targets = {
            'LR': mv,
            'Raykar': crowd_labels,
        }

        ss = sklearn.cross_validation.ShuffleSplit(n_examples, n_iter=n_splits,
                test_size=0.25, random_state=shuffle_seed)
        for split_id, (train, test) in enumerate(ss):
            logging.info('Test {}/{}'.format(split_id + 1, n_splits))
            for method_id, method in enumerate(methods):
                logging.info('Method {} ({}/{})'.format(method, method_id + 1,
                                                        len(methods)))
                if method == 'LR':
                    runners.lr(results, method, split_id, all_features[method],
                               targets[method], sorted(test),
                               overwrite=overwrite)
                elif method == 'Raykar':
                    runners.raykar(results, method, split_id,
                                   all_features[method], targets[method],
                                   sorted(test), overwrite=overwrite,
                                   n_restarts=5)
                else:
                    raise ValueError('Unexpected method: {}'.format(method))

        if plot:
            matplotlib.rcParams['font.family'] = 'serif'
            matplotlib.rcParams['font.serif'] = ['Palatino Linotype']
            plt.figure(figsize=(4, 3))  # Shrink it a little for thesis.
            vertical_scatter_ba(results, labels, violin=True, minorticks=False)
            plt.ylim((0, 100))
            plt.subplots_adjust(left=0.15)
            plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='data/breast_cancer_wisconsin.csv',
                        help='Input breast cancer data CSV')
    parser.add_argument('--results', default='data/results_raykar.h5',
                        help='HDF5 results data file')
    parser.add_argument('--overwrite', action='store_true',
                        help='Overwrite existing results')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    parser.add_argument('--plot', action='store_true', help='Generate a plot')
    args = parser.parse_args()

    if args.verbose:
        logging.root.setLevel(logging.DEBUG)
    else:
        logging.root.setLevel(logging.INFO)

    main(args.input, args.results, overwrite=args.overwrite, plot=args.plot)
