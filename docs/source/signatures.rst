How are signatures computed ?
=============================

Here are the detailed steps to get the best features to distinguish two subsets (Either A vs B or A vs Rest):
#. For every feature, compute the wasserstein distance between the 2 subsets.
#. Sort the features by the descending wasserstein distance and keep the 100 best features.
#. For each feature, compute the cut, that distinguish our two subsets, with the best Matthews correlation coefficient.
#. Show the 20 features with the best MCC score.
