# """
# The computation itself, handled by the internal `compute_signature` function,
# uses a two-step process:

# 1. Features are first ranked by the Wasserstein distance between their
#    distributions in the two groups being compared. The top 100 features
#    from this ranking are retained for further analysis.

# 2. This list is then refined using the Matthews Correlation Coefficient (MCC)
#    to select the 20 most robust and discriminative features for the final
#    signature.
# """

import numpy as np
import bokeh.models
import sys
from scipy.stats import rankdata
import anndata


def signature_buttons(
    adata: anndata.AnnData,
    offset_text_feature_color: bokeh.models.TextInput,
    offset_label: bokeh.models.TextInput,
    hidden_checkbox_A: bokeh.models.CheckboxGroup,
    hidden_checkbox_B: bokeh.models.CheckboxGroup,
    label_signature: bokeh.models.MultiSelect,
) -> tuple[
    bokeh.models.Button,
    bokeh.models.Button,
    bokeh.models.HelpButton,
    bokeh.models.HelpButton,
    bokeh.models.MultiSelect,
    bokeh.models.Div,
    list,
]:
    """
    Create the UI elements e.g., buttons, help tooltips, and
    a multi-select widget that allow users to compute differential feature
    signatures between interactively defined cell subsets. It provides options
    to compare "Subset A vs. Rest" and "Subset A vs. Subset B".

    Args:
        adata (anndata.AnnData):
            Annotated data matrix of shape `n_obs` x `n_vars`.
        offset_text_feature_color (bokeh.models.TextInput):
            Text input for entering feature names to color samples in the scatter plot.
        offset_label (bokeh.models.TextInput):
            Hidden text input that stores the group labels for generating
            violin/heatmap plots
        hidden_checkbox_A (bokeh.models.CheckboxGroup):
            Widget storing "Subset A" sample indices.
        hidden_checkbox_B (bokeh.models.CheckboxGroup):
            Widget storing "Subset B" sample indices.
        label_signature : bokeh.models.MultiSelect
            Widget listing available group labels including Subset A and Subset B or Rest.

    Returns:
        Tuple containing the Bokeh components created by this function
            - **bt_sign1** (:class:`bokeh.models.Button`): Button to compute "A vs. Rest".
            - **bt_sign2** (:class:`bokeh.models.Button`): Button to compute "A vs. B".
            - **help_button1** (:class:`bokeh.models.HelpButton`): Help tooltip for `bt_sign1`.
            - **help_button2** (:class:`bokeh.models.HelpButton`): Help tooltip for `bt_sign2`.
            - **multiselect_signature** (:class:`bokeh.models.MultiSelect`): Widget to display the ranked features of the computed signature.
            - **div_signature_list** (:class:`bokeh.models.Div`): Div element to display the signature title and a summary of top features.
            - **signature_nr** (:class:`list`): List containing a single integer used to number the computed signatures sequentially.
    """  # noqa: E501

    def wasserstein_distance(
        mu1: float, sigma1: float, mu2: float, sigma2: float
    ) -> float:
        """
        Compute the Wasserstein distance between two Gaussian distributions.

        Parameters:
            mu1 : float
                Mean of the first distribution.
            sigma1 : float
                Standard deviation of the first distribution.
            mu2 : float
                Mean of the second distribution.
            sigma2 : float
                Standard deviation of the second distribution.

        Returns
            float
                The Wasserstein distance between the two distributions.
        """
        mean_diff = mu1 - mu2
        std_diff = sigma1 - sigma2
        wasserstein = np.sqrt(mean_diff**2 + std_diff**2)
        return wasserstein

    def find_intersection_gaussians(mu1, sigma1, mu2, sigma2):
        # find intersections between two Gaussian probability density functions
        if sigma1 < 0.0 or sigma2 < 0.0:
            sys.exit("Error: negative standard deviation.")

        if sigma2 < 1e-8:
            sigma2 = 1e-8

        if sigma1 < 1e-8:
            sigma1 = 1e-8

        if np.abs(sigma1 - sigma2) < 1e-8:
            x = (mu1 + mu2) / 2
            return x, x

        else:
            sig1square = sigma1**2
            sig2square = sigma2**2
            a = sig2square / 2 - sig1square / 2
            b = sig1square * mu2 - sig2square * mu1
            c = (
                sig2square * mu1**2 / 2
                - sig1square * mu2**2 / 2
                - sig1square * sig2square * (np.log(sigma2) - np.log(sigma1))
            )

            discr = b**2 - 4 * a * c
            if np.abs(discr) < 1e-8:
                discr = 0.0
            x1 = (-b + np.sqrt(discr)) / (2 * a)
            x2 = (-b - np.sqrt(discr)) / (2 * a)

            return x1, x2

    def gaussian_pdf(x, mu, sigma):
        var = sigma**2
        return (
            1.0 / (np.sqrt(2.0 * np.pi * var)) * np.exp(-((x - mu) ** 2) / (2.0 * var))
        )

    def compute_signature(
        adata: anndata.AnnData,
        means: np.ndarray,
        stds: np.ndarray,
        obs_indices_A: list[int],
        obs_indices_B: list[int] = None,
    ) -> tuple[np.ndarray, dict, dict]:
        """
        Find the 20 best features to distinguish two subsets of data using Wasserstein
        distance and MCC.

        Parameters:
            adata : anndata.AnnData
                Annotated data matrix.
            means : np.ndarray
                Mean values for each feature.
            stds : np.ndarray
                Standard deviations for each feature.
            obs_indices_A : list[int]
                Indices of observations in group A.
            obs_indices_B : list[int], optional
                Indices of observations in group B. If None, compare A vs. rest.

        Returns:
            tuple
                - new_selected_features: np.ndarray
                    Indices of the top discriminative features.
                - mcc_dict_abs: dict
                    Dictionary mapping feature indices to absolute MCC scores.
                - up_or_down_d: dict
                    Dictionary mapping feature indices to "+" or "-" depending on
                    correlation sign.
        """
        # STEP 1: sort features using Wasserstein distances

        a2 = adata.X[obs_indices_A, :]
        mu2_array = a2.mean(axis=0)
        sigma2_array = a2.std(axis=0)
        if obs_indices_B is None:
            mu = means
            sigma1_array = stds.to_numpy()
            mu1_array = (
                (mu * adata.n_obs - mu2_array * len(obs_indices_A))
                / (adata.n_obs - len(obs_indices_A))
            ).to_numpy()
        else:
            a1 = adata.X[obs_indices_B, :]
            mu1_array = a1.mean(axis=0)
            sigma1_array = a1.std(axis=0)
        sigma1_array[sigma1_array < 1e-8] = 1e-8
        sigma2_array[sigma2_array < 1e-8] = 1e-8
        dist_list = wasserstein_distance(
            mu1_array, sigma1_array, mu2_array, sigma2_array
        )

        sorted_features = np.argsort(dist_list)[::-1]

        if obs_indices_B is None:
            ref_array = np.arange(adata.n_obs)
            rest_indices = np.arange(adata.n_obs)[~np.in1d(ref_array, obs_indices_A)]
        else:
            rest_indices = obs_indices_B

        samples_A = obs_indices_A
        samples_B = rest_indices

        # Keep only 100 features:
        selected_features = sorted_features[:100]

        def all_mcc(scores1: np.ndarray, scores2: np.ndarray) -> np.ndarray:
            """
            Compute Matthews Correlation Coefficient (MCC) scores for all
            features between two groups.

            Parameters
            ----------
            scores1 : np.ndarray
                Array of feature values for group 1 (shape: n_features x n_samples1).
            scores2 : np.ndarray
                Array of feature values for group 2 (shape: n_features x n_samples2).

            Returns
            -------
            np.ndarray
                Array of MCC scores, the length of the array is the number of features.
            """
            l1 = scores1.shape[1]
            l2 = scores2.shape[1]

            scores1.sort(axis=1)
            scores2.sort(axis=1)

            all_scores = np.hstack((scores1, scores2))

            ranks = rankdata(all_scores, method="min", axis=1).astype(int)

            all_scores.sort(axis=1)

            ranks1 = ranks[:, :l1]
            ranks2 = ranks[:, l1:]

            def matthews_c(
                a_: np.ndarray,
                b_: np.ndarray,
                c_: np.ndarray,
                d_: np.ndarray,
                l1_: int,
                l2_: int,
            ) -> np.ndarray:
                """
                Compute the Matthews Correlation Coefficient given confusion matrices
                values.

                Parameters:
                    a_ : np.ndarray
                        True positives for each feature.
                    b_ : np.ndarray
                        False positives for each feature.
                    c_ : np.ndarray
                        False negatives for each feature.
                    d_ : np.ndarray
                        True negatives for each feature.
                    l1_ : int
                        Number of samples in group 1.
                    l2_ : int
                        Number of samples in group 2.

                Returns:
                    np.ndarray
                        Array of MCC values for each feature.
                """
                max_value = np.maximum(l1_, l2_)
                tp = a_ / max_value
                fp = b_ / max_value
                fn = c_ / max_value
                tn = d_ / max_value

                denominator = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)

                mcc = (tp * tn - fp * fn) / np.sqrt(denominator)
                return mcc

            def searchsorted2d(a_, b_):
                """Vectorized search_sorted

                Parameters:
                    a_ : np.ndarray
                        Array of sorted values (shape: n_features x n_samples1).
                    b_ : np.ndarray
                        Array of values to search for (shape: n_features x n_samples2).

                Returns:
                    np.ndarray
                        Array of indices where elements of b_ should be inserted into
                        a_ to maintain order.
                """
                m, n = a_.shape
                max_num = np.maximum(a_.max(), b_.max()) + 1
                r = max_num * np.arange(a_.shape[0])[:, None]
                p_ = np.searchsorted((a_ + r).ravel(), (b_ + r).ravel()).reshape(m, -1)
                return p_ - n * (np.arange(m)[:, None])

            maxis = np.maximum(np.max(ranks1, axis=1), np.max(ranks2, axis=1))
            rng = (
                np.repeat(np.arange(l1 + l2), scores1.shape[0]).reshape(l1 + l2, -1).T
                + 1
            ).clip(max=maxis[:, None])

            a = np.minimum(searchsorted2d(ranks1, rng)[:, 1:], l1)
            b = l1 - a
            c = np.minimum(searchsorted2d(ranks2, rng)[:, 1:], l2)
            d = l2 - c

            results = matthews_c(a, b, c, d, l1, l2)

            idx = l1 + l2 - 2 - np.abs(results[:, ::-1]).argmax(axis=1)

            first_axis_range = (np.arange(scores1.shape[0]),)
            mccscores = results[first_axis_range, idx]
            # cuts = (
            #     all_scores[first_axis_range, idx] +
            #     all_scores[first_axis_range, idx + 1]
            #     ) / 2.
            # return mccscores, cuts
            return mccscores

        sc1 = adata[samples_A, selected_features].copy().X.T
        sc2 = adata[samples_B, selected_features].copy().X.T
        mccs = all_mcc(sc1, sc2)
        new_selected_features = selected_features[
            np.argsort(np.abs(mccs.flatten()))[::-1]
        ]
        mcc_dict = dict(map(lambda i, j: (i, j), selected_features, mccs.flatten()))
        mcc_dict_abs = dict(
            map(lambda i, j: (i, j), selected_features, np.abs(mccs).flatten())
        )
        new_selected_features = new_selected_features[:20]
        up_or_down_d = {
            ft: ("-" if mcc_dict[ft] > 0.0 else "+") for ft in new_selected_features
        }
        return new_selected_features, mcc_dict_abs, up_or_down_d

    # TODO remove redundancy (shrink_test is defined twice)
    def shrink_text(s_in, size):
        true_size = max(size, 3)
        if len(s_in) > true_size:
            new_s = ""
            l1 = true_size // 2
            l2 = true_size - l1 - 3
            new_s += s_in[:l1]
            new_s += "..."
            new_s += s_in[-l2:]
        else:
            new_s = s_in
        return new_s

    def sign_A_vs_rest(
        ad: anndata.AnnData,
        obs_indices: list[int],
        dv: bokeh.models.Div,
        ms_sign: bokeh.models.MultiSelect,
        sign_nr: list[int],
        label_sign: bokeh.models.MultiSelect,
    ) -> None:
        """
        Compute a feature signature distinguishing two groups using Wasserstein
        distance and MCC.

        Parameters
            adata : anndata.AnnData
                Annotated data matrix.
            means : np.ndarray
                Mean values for each feature.
            stds : np.ndarray
                Standard deviations for each feature.
            obs_indices_A : list[int]
                Indices of observations in group A.
            obs_indices_B : list[int], optional
                Indices of observations in group B. If None, compare A vs. rest.

        Returns
            tuple
                - new_selected_features: np.ndarray
                    Indices of the top discriminative features.
                - mcc_dict_abs: dict
                    Dictionary mapping feature indices to absolute MCC scores.
                - up_or_down_d: dict
                    Dictionary mapping feature indices to "+" or "-" depending on
                    correlation sign.
        """
        if len(obs_indices) > 0 and len(obs_indices) < ad.n_obs:
            ms_sign.title = "..."
            label_sign.title = "..."
            outputs, mcc_dict, up_or_down_dict = compute_signature(
                ad,
                ad.var["mean_values_local_yomix"],
                ad.var["standard_deviations_local_yomix"],
                obs_indices,
                None,
            )
            sign_nr[0] += 1
            dv.text = (
                "Signature #"
                + str(sign_nr[0])
                + ": "
                + ", ".join(['<b>"' + elt + '"</b>' for elt in ad.var_names[outputs]])
            )
            ms_sign.options = [
                (
                    up_or_down_dict[outp] + ad.var_names[outp],
                    up_or_down_dict[outp]
                    + " (MCC:{:.3f}) ".format(mcc_dict[outp])
                    + shrink_text(ad.var_names[outp], 25),
                )
                for outp in outputs
            ]
            ms_sign.title = "Signature #" + str(sign_nr[0])

            unique_labels = []
            unique_labels.append(("[  Subset A  ]", "[  Subset A  ]"))
            unique_labels.append(("[  Rest  ]", "[  Rest  ]"))
            unique_labels += [
                (lbl + ">>yomix>>" + lbl_elt, shrink_text(lbl + " > " + lbl_elt, 35))
                for (lbl, lbl_elt) in ad.uns["all_labels"]
            ]

            # Update label_sign options
            label_sign.options = unique_labels
            label_sign.size = min(len(label_sign.options), 20)
            # finalize label_sign
            label_sign.title = "Groups"
            label_sign.value = ["[  Subset A  ]", "[  Rest  ]"]

    def sign_A_vs_B(
        ad: anndata.AnnData,
        obs_indices_A: list[int],
        obs_indices_B: list[int],
        dv: bokeh.models.Div,
        ms_sign: bokeh.models.MultiSelect,
        sign_nr: list[int],
        label_sign: bokeh.models.MultiSelect,
    ) -> None:
        """
        Compute and display the feature signature for "Subset A vs. Subset B".

        Parameters:
            ad : anndata.AnnData
                Annotated data matrix.
            obs_indices_A : list[int]
                Indices of observations in subset A.
            obs_indices_B : list[int]
                Indices of observations in subset B.
            dv : bokeh.models.Div
                Div widget to display the signature summary.
            ms_sign : bokeh.models.MultiSelect
                MultiSelect widget to display the ranked features.
            sign_nr : list[int]
                List containing a single integer used to number the computed signatures.
            label_sign : bokeh.models.MultiSelect
                Widget for selecting group labels.

        Returns:
            None
        """
        if (
            len(obs_indices_A) > 0
            and len(obs_indices_A) < ad.n_obs
            and len(obs_indices_B) > 0
            and len(obs_indices_B) < ad.n_obs
        ):
            ms_sign.title = "..."
            label_sign.title = "..."
            outputs, mcc_dict, up_or_down_dict = compute_signature(
                ad,
                ad.var["mean_values_local_yomix"],
                ad.var["standard_deviations_local_yomix"],
                obs_indices_A,
                obs_indices_B,
            )
            sign_nr[0] += 1
            dv.text = (
                "Signature #"
                + str(sign_nr[0])
                + ": "
                + ", ".join(['<b>"' + elt + '"</b>' for elt in ad.var_names[outputs]])
            )
            ms_sign.options = [
                (
                    up_or_down_dict[outp] + ad.var_names[outp],
                    up_or_down_dict[outp]
                    + " (MCC:{:.3f}) ".format(mcc_dict[outp])
                    + shrink_text(ad.var_names[outp], 25),
                )
                for outp in outputs
            ]
            ms_sign.title = "Signature #" + str(sign_nr[0])

            unique_labels = []
            unique_labels.append(("[  Subset A  ]", "[  Subset A  ]"))
            unique_labels.append(("[  Subset B  ]", "[  Subset B  ]"))
            unique_labels += [
                (lbl + ">>yomix>>" + lbl_elt, shrink_text(lbl + " > " + lbl_elt, 35))
                for (lbl, lbl_elt) in ad.uns["all_labels"]
            ]

            # Update label_sign options
            label_sign.options = unique_labels
            label_sign.size = len(label_sign.options)

            # finalize label_sign
            label_sign.title = "Groups"
            label_sign.value = ["[  Subset A  ]", "[  Subset B  ]"]

    div_signature_list = bokeh.models.Div(
        width=235, height=50, height_policy="fixed", text="Signature #0:"
    )
    signature_nr = [0]
    options = []
    multiselect_signature = bokeh.models.MultiSelect(
        title="Signature #0",
        options=options,
        width=235,
        max_width=235,
        size=20,
        width_policy="max",
    )

    def multiselect_function(feature_list: list[str]) -> None:
        """
        Update the feature color input and groups widget based on
        selected features.

        Parameters:
            feature_list : list[str]
                List of selected feature names.

        Returns:
            None
        """
        of_text = ""
        for i in range(len(feature_list)):
            if feature_list[i][0] == "+":
                if i == 0:
                    of_text += feature_list[i][1:]
                else:
                    of_text += "  +  " + feature_list[i][1:]
            else:  # feature_list[i][0] == "-"
                of_text += "  -  " + feature_list[i][1:]
        offset_text_feature_color.value = of_text
        if of_text != "":
            label_signature.visible = True

    multiselect_signature.on_change(
        "value", lambda attr, old, new: multiselect_function(new)
    )

    def label_function(feature_list: list[str]) -> None:
        """
        Update the label input widget based on selected group labels.

        Parameters:
            feature_list : list[str]
                List of selected group labels.

        Returns:
            None
        """
        of_text = ""
        for i in range(len(feature_list)):
            of_text += feature_list[i] + "//yomix//"
        offset_label.value = of_text

    label_signature.on_change("value", lambda attr, old, new: label_function(new))

    tooltip1 = bokeh.models.Tooltip(
        content="Requires setting subset A.\u00A0\u00A0", position="right"
    )
    help_button1 = bokeh.models.HelpButton(tooltip=tooltip1, margin=(3, 0, 3, 0))
    bt_sign1 = bokeh.models.Button(
        label="Compute signature (A vs. rest)", width=190, margin=(5, 0, 5, 5)
    )

    bt_sign1.on_click(
        lambda event: sign_A_vs_rest(
            adata,
            hidden_checkbox_A.active,
            div_signature_list,
            multiselect_signature,
            signature_nr,
            label_signature,
        )
    )

    tooltip2 = bokeh.models.Tooltip(
        content="Requires setting subsets A and B.\u00A0\u00A0", position="right"
    )
    help_button2 = bokeh.models.HelpButton(tooltip=tooltip2, margin=(3, 0, 3, 0))
    bt_sign2 = bokeh.models.Button(
        label="Compute signature (A vs. B)", width=190, margin=(5, 0, 5, 5)
    )

    bt_sign2.on_click(
        lambda event: sign_A_vs_B(
            adata,
            hidden_checkbox_A.active,
            hidden_checkbox_B.active,
            div_signature_list,
            multiselect_signature,
            signature_nr,
            label_signature,
        )
    )

    return (
        bt_sign1,
        bt_sign2,
        help_button1,
        help_button2,
        multiselect_signature,
        div_signature_list,
        signature_nr,
    )
