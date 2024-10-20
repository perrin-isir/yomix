import numpy as np
import bokeh.models
import bokeh.layouts
import sys


def signature_buttons(
    adata, offset_text_feature_color, hidden_checkbox_A, hidden_checkbox_B
):

    def var_mean_values(adata) -> np.ndarray:
        return np.squeeze(np.asarray(np.mean(adata.X, axis=0)))

    def var_standard_deviations(adata) -> np.ndarray:
        return np.squeeze(np.asarray(np.std(adata.X, axis=0)))

    adata.var["mean_values_local_yomix"] = var_mean_values(adata)
    adata.var["standard_deviations_local_yomix"] = var_standard_deviations(adata)
    adata.var_names_make_unique()
    adata.obs_names_make_unique()

    def matthews_coef(confusion_m):
        tp = confusion_m[0, 0]
        fp = confusion_m[0, 1]
        fn = confusion_m[1, 0]
        tn = confusion_m[1, 1]

        # normalizing confusion_matrix
        max_value = max(tp, fp, fn, tn)
        if max_value != 0:
            tp /= max_value
            fp /= max_value
            fn /= max_value
            tn /= max_value

        denominator = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
        if denominator == 0:
            return np.nan

        mcc = (tp * tn - fp * fn) / np.sqrt(denominator)
        return mcc

    def wasserstein_distance(mu1, sigma1, mu2, sigma2):
        mean_diff = mu1 - mu2
        std_diff = sigma1 - sigma2
        wasserstein = np.sqrt(mean_diff**2 + std_diff**2)
        return wasserstein

    def find_intersection_gaussians(mu1, sigma1, mu2, sigma2):
        # find intersections between two Gaussian probability density functions
        if sigma1 < 0.0 or sigma2 < 0.0:
            sys.exit("Error: negative standard deviation.")

        if sigma2 == 0:
            sigma2 = 1e-8

        if sigma1 == 0:
            sigma1 = 1e-8

        if sigma1 == sigma2:
            x = (mu1 + mu2) / 2
            return x, x

        else:
            a = 1 / (2 * sigma1**2) - 1 / (2 * sigma2**2)
            b = mu2 / (sigma2**2) - mu1 / (sigma1**2)
            c = (
                mu1**2 / (2 * sigma1**2)
                - mu2**2 / (2 * sigma2**2)
                - np.log(sigma2)
                + np.log(sigma1)
            )

            discr = b**2 - 4 * a * c
            x1 = (-b + np.sqrt(discr)) / (2 * a)
            x2 = (-b - np.sqrt(discr)) / (2 * a)

            return x1, x2

    def gaussian_pdf(x, mu, sigma):
        var = sigma**2
        return (
            1.0 / (np.sqrt(2.0 * np.pi * var)) * np.exp(-((x - mu) ** 2) / (2.0 * var))
        )

    def compute_signature(adata, means, stds, obs_indices_A, obs_indices_B=None):
        # STEP 1: sort features using Wasserstein distances

        # TODO: vectorize this
        dist_list = []
        mu1_list = []
        mu2_list = []
        sigma1_list = []
        sigma2_list = []
        for i in range(adata.n_vars):
            a2 = adata.X[obs_indices_A, i]
            mu2 = a2.mean()
            sigma2 = a2.std()
            if obs_indices_B is None:
                mu = means.iloc[i]
                sigma1 = stds.iloc[i]
                mu1 = (mu * adata.n_obs - mu2 * len(obs_indices_A)) / (
                    adata.n_obs - len(obs_indices_A)
                )
            else:
                a1 = adata.X[obs_indices_B, i]
                mu1 = a1.mean()
                sigma1 = a1.std()
            dist_h = wasserstein_distance(mu1, sigma1, mu2, sigma2)
            mu1_list.append(mu1)  # mean on subset B or rest
            mu2_list.append(mu2)  # mean on subset A
            sigma1_list.append(sigma1)
            sigma2_list.append(sigma2)
            dist_list.append(dist_h)

        sorted_features = np.argsort(dist_list)[::-1]

        # STEP 2: create random subset

        if obs_indices_B is None:
            # rest_indices = np.setdiff1d(np.arange(adata.n_obs), obs_indices_A)
            ref_array = np.arange(adata.n_obs)
            rest_indices = np.arange(adata.n_obs)[~np.in1d(ref_array, obs_indices_A)]
        else:
            rest_indices = obs_indices_B
        target_size = 1000
        divisor = max((len(obs_indices_A) + len(rest_indices)) / target_size, 1.0)

        size_A = max(int(len(obs_indices_A) / divisor), 1)
        size_B = max(int(len(rest_indices) / divisor), 1)
        samples_A = np.random.choice(obs_indices_A, size_A, replace=False)
        samples_B = np.random.choice(rest_indices, size_B, replace=False)
        intersection = np.intersect1d(samples_A, samples_B)
        samples_A = np.setdiff1d(samples_A, intersection)
        samples_B = np.setdiff1d(samples_B, intersection)
        size_A = len(samples_A)
        size_B = len(samples_B)
        all_samples = np.hstack((samples_A, samples_B))

        # Keep only 100 features:
        selected_features = sorted_features[:100]

        small_data = adata[all_samples, selected_features].copy()
        # small_data = adata[all_samples, selected_features]
        small_data.obs["new_label_must_not_be_an_existing_column"] = [
            "label_1"
        ] * size_A + ["label_0"] * size_B

        # STEP 3: compute MCC scores
        mcc_scores = []
        for i in range(small_data.n_vars):
            mu1 = mu1_list[selected_features[i]]
            sigma1 = sigma1_list[selected_features[i]]
            mu2 = mu2_list[selected_features[i]]
            sigma2 = sigma2_list[selected_features[i]]
            cut1, cut2 = find_intersection_gaussians(mu1, sigma1, mu2, sigma2)

            if sigma1 == sigma2:
                cut = cut1
            elif cut1 is not None and cut2 is not None:
                cut_1 = min(cut1, cut2)
                cut_2 = max(cut1, cut2)

            TP = 0
            TN = 0
            FP = 0
            FN = 0

            for index, cell in enumerate(small_data.obs.itertuples()):
                feature_value = small_data.X[index, i]

                if sigma1 == sigma2 and mu1 < mu2 and feature_value < cut:
                    result_classification = "label_0"
                elif sigma1 == sigma2 and mu1 < mu2 and feature_value >= cut:
                    result_classification = "label_1"
                elif sigma1 == sigma2 and mu2 <= mu1 and feature_value < cut:
                    result_classification = "label_1"
                elif sigma1 == sigma2 and mu2 <= mu1 and feature_value >= cut:
                    result_classification = "label_0"

                elif sigma1 < sigma2 and feature_value < cut_1:
                    result_classification = "label_1"
                elif sigma1 < sigma2 and feature_value > cut_2:
                    result_classification = "label_1"
                elif (
                    sigma1 < sigma2
                    and cut_1 <= feature_value
                    and feature_value <= cut_2
                ):
                    result_classification = "label_0"

                elif sigma2 < sigma1 and feature_value < cut_1:
                    result_classification = "label_0"
                elif sigma2 < sigma1 and feature_value > cut_2:
                    result_classification = "label_0"
                elif (
                    sigma2 < sigma1
                    and cut_1 <= feature_value
                    and feature_value <= cut_2
                ):
                    result_classification = "label_1"

                # Comparing classification results with labels
                if (
                    cell.new_label_must_not_be_an_existing_column == "label_1"
                    and result_classification == "label_1"
                ):
                    # True Positive
                    TP += 1
                elif (
                    cell.new_label_must_not_be_an_existing_column == "label_1"
                    and result_classification == "label_0"
                ):
                    # False Negative
                    FN += 1
                elif (
                    cell.new_label_must_not_be_an_existing_column == "label_0"
                    and result_classification == "label_1"
                ):
                    # False Positive
                    FP += 1
                else:
                    # True Negative
                    TN += 1

            confusion_matrix = np.array([[TP, FP], [FN, TN]])
            mcc = matthews_coef(confusion_matrix)
            mcc_scores.append(mcc)

        mcc_dict = dict(map(lambda i, j: (i, j), selected_features, mcc_scores))
        new_sorted_features = selected_features[np.argsort(mcc_scores)[::-1]]

        # # STEP 4 : correlation filtering

        # corr_df_original = np.abs(
        #     pd.DataFrame(adata[obs_indices_A, new_sorted_features].X).corr())
        # # TODO: merge with indices B
        # threshold = np.quantile(corr_df_original, 0.5)
        # # threshold = 0.2
        # corr_df = corr_df_original < threshold
        # # np.fill_diagonal(corr_df.values, True)

        # findex = 0
        # # nindex = 1
        # nindex = 0

        # while findex < len(new_sorted_features):
        #     if corr_df[findex][:nindex].min() == False:
        #         corr_df.drop(columns=[findex], inplace=True)
        #         corr_df.drop([findex], inplace=True)
        #         findex += 1
        #     else:
        #         findex += 1
        #         nindex += 1

        # filtered_features = new_sorted_features[corr_df.axes[0].values]
        # rest_features = new_sorted_features[
        #     ~np.in1d(new_sorted_features, filtered_features)]
        # new_sorted_features = np.hstack((filtered_features, rest_features))

        new_sorted_features = new_sorted_features[:20]
        up_or_down_dict = {}
        for ft in new_sorted_features:
            if mu1_list[ft] > mu2_list[ft]:
                up_or_down_dict[ft] = "-"
            else:
                up_or_down_dict[ft] = "+"

        # del small_data.obs["new_label_must_not_be_an_existing_column"]
        return new_sorted_features, mcc_dict, up_or_down_dict

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

    def sign_A_vs_rest(ad, obs_indices, dv, ms_sign, sign_nr):
        if len(obs_indices) > 0 and len(obs_indices) < ad.n_obs:
            ms_sign.title = "..."
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

    def sign_A_vs_B(ad, obs_indices_A, obs_indices_B, dv, ms_sign, sign_nr):
        if (
            len(obs_indices_A) > 0
            and len(obs_indices_A) < ad.n_obs
            and len(obs_indices_B) > 0
            and len(obs_indices_B) < ad.n_obs
        ):
            ms_sign.title = "..."
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

    def multiselect_function(feature_list):
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

    multiselect_signature.on_change(
        "value", lambda attr, old, new: multiselect_function(new)
    )

    tooltip1=bokeh.models.Tooltip(content="Requires setting the subset A", position="right")
    help_button1 = bokeh.models.HelpButton(tooltip=tooltip1, margin=(3, 0, 3, 0))
    bt_sign1 = bokeh.models.Button(label="Compute signature (A vs. rest)", width=190, margin=(5, 0, 5, 5))

    bt_sign1.on_click(
        lambda event: sign_A_vs_rest(
            adata,
            hidden_checkbox_A.active,
            div_signature_list,
            multiselect_signature,
            signature_nr,
        )
    )

    tooltip2=bokeh.models.Tooltip(content="Requires setting the subsets A and B", position="right")
    help_button2 = bokeh.models.HelpButton(tooltip=tooltip2, margin=(3, 0, 3, 0))
    bt_sign2 = bokeh.models.Button(label="Compute signature (A vs. B)", width=190, margin=(5, 0, 5, 5))

    bt_sign2.on_click(
        lambda event: sign_A_vs_B(
            adata,
            hidden_checkbox_A.active,
            hidden_checkbox_B.active,
            div_signature_list,
            multiselect_signature,
            signature_nr,
        )
    )

    return bt_sign1, bt_sign2, help_button1, help_button2, multiselect_signature, div_signature_list, signature_nr
