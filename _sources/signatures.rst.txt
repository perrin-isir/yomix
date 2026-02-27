=============================
How are signatures computed?
=============================

Signatures are computed using a **two-step filtering process** that identifies the **most discriminative features between two sample subsets** (Either A vs B or A vs Rest). This method combines distributional analysis with classification performance metrics to select features that are both statistically different and practically useful for distinguishing sample populations.

Step-by-Step Process
====================

* For every feature, compute the Wasserstein distance between the 2 distributions (one for each subset)
* Sort features by descending Wasserstein distance and keep the 100 best features
* For each of these 100 features, compute the cut with the best Matthews correlation coefficient to distinguish the two subsets
* Select and show the 20 features with the best MCC scores as the final signature

.. code-block:: text

    Input: Two sample subsets
           ↓
    Step 1: Wasserstein Distance Filtering
           ↓
    Rank all features by Wasserstein distance
           ↓
    Keep top 100 features
           ↓
    Step 2: MCC Refinement
           ↓
    Compute MCC for each feature
           ↓
    Select top 20 features by |MCC|
           ↓
    Output: Signature with 20 discriminative features

Step 1: Wasserstein Distance Filtering
======================================

Identify features with the most different distributions between two groups by measuring the "distance" between their probability distributions.
For two Gaussian distributions N(μ₁, σ₁²) and N(μ₂, σ₂²), the 2-Wasserstein distance is:

.. math::

   W₂ = \sqrt{(\mu₁ - \mu₂)² + (\sigma₁ - \sigma₂)²}

Implementation
--------------

.. code-block:: python

    def wasserstein_distance(mu1: float, sigma1: float, mu2: float, sigma2: float) -> float:
        """
        Compute the Wasserstein distance between two Gaussian distributions.
        
        Returns the L2 distance between distribution parameters.
        """
        mean_diff = mu1 - mu2
        std_diff = sigma1 - sigma2
        wasserstein = np.sqrt(mean_diff**2 + std_diff**2)
        return wasserstein

The algorithm first computes group statistics for each feature, calculating mean and standard deviation for Group A and Group B (either a specific subset or the remaining samples). It then calculates the Wasserstein distance between distributions for each feature, ranks all features in descending order by Wasserstein distance, and selects the top 100 features with the highest distributional differences.

Why Wasserstein Distance?
-------------------------

**Wasserstein distance captures both location and scale differences**, being sensitive to changes in both mean and variance. It provides intuitive interpretation where higher values indicate more separated distributions, offers computational efficiency through closed-form solutions for Gaussian distributions, and demonstrates robustness by being less sensitive to outliers compared to KL divergence, chi-squared distance, or total variation distance.

Step 2: Matthews Correlation Coefficient (MCC) Refinement
=========================================================

From the 100 pre-filtered features, identify the 20 that can most reliably distinguish between groups using optimal binary classification thresholds.

The Matthews Correlation Coefficient is defined as:

.. math::

   MCC = \frac{TP \times TN - FP \times FN}{\sqrt{(TP + FP)(TP + FN)(TN + FP)(TN + FN)}}

Where TP, TN, FP, and FN represent true positives, true negatives, false positives, and false negatives respectively. MCC ranges from -1 (perfect negative correlation) through 0 (random prediction) to +1 (perfect positive correlation).

Rank-Based Approach
-------------------

The algorithm converts all values to **ranks for scale-invariant comparison**, handling features with different expression scales without requiring normalization:

.. code-block:: python

    # Convert all values to ranks for scale-invariant comparison
    ranks = rankdata(all_scores, method="min", axis=1).astype(int)

For each feature, the algorithm tests multiple thresholds across the range of feature values, computes the confusion matrix for each threshold, calculates MCC at each threshold, and selects the threshold that maximizes |MCC|.

The computation is vectorized across all features and thresholds simultaneously:

.. code-block:: python

    def all_mcc(scores1: np.ndarray, scores2: np.ndarray) -> np.ndarray:
        """
        Compute optimal MCC scores for all features using vectorized operations.
        
        For each feature, finds the threshold that maximizes |MCC|.
        """
        # Rank all values for scale invariance
        ranks = rankdata(all_scores, method="min", axis=1)
        
        # Vectorized computation of confusion matrices across all thresholds
        a = np.minimum(searchsorted2d(ranks1, rng)[:, 1:], l1)  # True Positives
        b = l1 - a                                              # False Positives
        c = np.minimum(searchsorted2d(ranks2, rng)[:, 1:], l2)  # False Negatives  
        d = l2 - c                                              # True Negatives
        
        # Compute MCC for all thresholds
        results = matthews_c(a, b, c, d, l1, l2)
        
        # Select threshold with maximum |MCC|
        idx = l1 + l2 - 2 - np.abs(results[:, ::-1]).argmax(axis=1)
        return results[np.arange(scores1.shape[0]), idx]

Why MCC?
--------

**MCC finds optimal thresholds by maximizing true correlation between predicted and actual classifications**, making it more robust to imbalanced datasets and class distribution skews compared to accuracy, precision, or recall.

Output Interpretation
=====================

The algorithm returns the 20 most discriminative feature indices, quantitative MCC scores measuring discriminative power, and direction indicators showing whether features are upregulated ("+") or downregulated ("-") in Group A versus Group B.

.. code-block:: python

    # Example output interpretation
    signature_features = ["Gene_A", "Gene_B", "Gene_C"]
    mcc_scores = [0.85, 0.72, 0.68]
    directions = ["+", "-", "+"]

    # Interpretation:
    # Gene_A: Highly upregulated in Group A (MCC = 0.85)
    # Gene_B: Moderately downregulated in Group A (MCC = 0.72) 
    # Gene_C: Moderately upregulated in Group A (MCC = 0.68)

Algorithm Advantages
====================

The two-stage filtering prevents multiple testing issues by reducing the search space from all features to just 100, then to 20, implemented as ``selected_features = sorted_features[:100]`` followed by ``new_selected_features = new_selected_features[:20]``. The Wasserstein distance captures both mean and variance differences through ``mean_diff = mu1 - mu2`` and ``std_diff = sigma1 - sigma2``, enabling detection of distributional changes beyond simple fold-change analysis. The algorithm uses vectorized operations throughout the MCC computation with ``ranks = rankdata(all_scores, method="min", axis=1)`` and processes all features simultaneously rather than using loops. The rank-based approach eliminates preprocessing requirements since ``rankdata()`` provides inherent scale invariance without needing log-transformation or z-scoring steps. 

Finally, the algorithm produces interpretable feature signatures with directionality indicators (``"+"`` or ``"-"``) and quantitative MCC scores formatted as ``"(MCC:{:.3f})"``, including feature names from ``ad.var_names[outputs]`` with their discriminative power, enabling us to identify both upregulated and downregulated markers for experimental follow-up.

Usage Examples
==============

A vs Rest Comparison
--------------------

.. code-block:: python

    # Compare subset A against all remaining samples
    signature, mcc_dict, directions = compute_signature(
        adata=adata,
        means=global_means,
        stds=global_stds, 
        obs_indices_A=subset_A_indices,
        obs_indices_B=None  # Compare against rest
    )

A vs B Comparison
-----------------

.. code-block:: python

    # Compare two specific subsets
    signature, mcc_dict, directions = compute_signature(
        adata=adata,
        means=global_means,
        stds=global_stds,
        obs_indices_A=subset_A_indices,
        obs_indices_B=subset_B_indices
    )

Wasserstein Distance Interpretation
----------------------------------

High values (> 1.0) indicate strong distributional differences, medium values (0.3-1.0) suggest moderate differences, while low values (< 0.3) represent subtle differences between groups.

MCC Score Interpretation
-----------------------

Absolute MCC values above 0.8 indicate excellent discriminative power, values above 0.5 suggest good discriminative power, values above 0.3 represent moderate discriminative power, and values below 0.3 indicate poor discriminative ability.
