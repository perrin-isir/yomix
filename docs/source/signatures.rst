How are signatures computed ?
=============================

Here are the detailed steps to get the best features to distinguish two subsets (Either A vs B or A vs Rest):

#. For every feature, we compute the wasserstein distance between the 2 distributions (one for each subset).
#. We sort the features by the descending wasserstein distance and keep the 100 best features.
#. For each feature, we compute the cut with the best Matthews correlation coefficient to distinguish our two subsets,
#. Show the 20 features with the best MCC score.
