import numpy as np
import bokeh.models
import bokeh.layouts
import sys
from scipy.stats import rankdata


def signature_buttons(
    adata,
    offset_text_feature_color,
    offset_label,
    hidden_checkbox_A,
    hidden_checkbox_B,
    label_signature,
):

    def wasserstein_distance(mu1, sigma1, mu2, sigma2):
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

    def compute_signature(adata, means, stds, obs_indices_A, obs_indices_B=None):
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

        def all_mcc(scores1, scores2):
            l1 = scores1.shape[1]
            l2 = scores2.shape[1]

            scores1.sort(axis=1)
            scores2.sort(axis=1)

            all_scores = np.hstack((scores1, scores2))

            ranks = rankdata(all_scores, method="min", axis=1).astype(int)

            all_scores.sort(axis=1)

            ranks1 = ranks[:, :l1]
            ranks2 = ranks[:, l1:]

            def matthews_c(a_, b_, c_, d_, l1_, l2_):

                max_value = np.maximum(l1_, l2_)
                tp = a_ / max_value
                fp = b_ / max_value
                fn = c_ / max_value
                tn = d_ / max_value

                denominator = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)

                mcc = (tp * tn - fp * fn) / np.sqrt(denominator)
                return mcc

            def searchsorted2d(a_, b_):
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
        
        # Sort by absolute MCC
        sorted_by_mcc = np.argsort(np.abs(mccs.flatten()))[::-1]
        sorted_features_mcc = selected_features[sorted_by_mcc]

        # Build dictionaries for signed and absolute MCC
        mcc_dict = dict(zip(selected_features, mccs.flatten()))
        mcc_dict_abs = dict(zip(selected_features, np.abs(mccs).flatten()))

        # -------------------------------------------------
        # Generate signatures for sizes [1, 3, 10, 20, 25]
        # -------------------------------------------------
        signature_sizes = [1, 3 , 10 ,20]
        signatures_dict = {}

        for size in signature_sizes:
            top_feats = sorted_features_mcc[:size]
            up_or_down_d = {
                ft: ("-" if mcc_dict[ft] > 0.0 else "+") for ft in top_feats
            }

            # Store in a tuple, but you can adjust format as needed
            signatures_dict[size] = (
                top_feats,                         # array of top feature indices
                {ft: mcc_dict_abs[ft] for ft in top_feats},  # dict of abs(MCC)
                up_or_down_d                                # dict: feature -> '+' or '-'
            )

        return signatures_dict

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
    def sign_A_vs_rest(ad, obs_indices, dv, ms_sign, sign_nr, label_sign, benchmark_name="BenchmarkRun"):
        import time
        import os
        import pandas as pd
        import numpy as np
        from sklearn.svm import SVC
        from sklearn.metrics import (
            matthews_corrcoef,
            precision_score,
            recall_score,
            f1_score
        )
        from sklearn.model_selection import train_test_split
        from scipy.sparse import vstack

        if len(obs_indices) == 0 or len(obs_indices) == ad.n_obs:
            print("Skipping: empty or full group.")
            return

        label_key = ad.obs["labels"].iloc[obs_indices[0]] if "labels" in ad.obs else "Unknown_Label"

        if ms_sign:
            ms_sign.title = f"Signature: {label_key}"
        if label_sign:
            label_sign.title = f"Label: {label_key}"

        start_time = time.time()

        signatures_dict = compute_signature(
            ad,
            ad.var["mean_values_local_yomix"],
            ad.var["standard_deviations_local_yomix"],
            obs_indices,
            None,
        )

        elapsed_time = time.time() - start_time
        print(f" Signature computation time: {elapsed_time:.2f}s")

        # Store full results
        all_results = {}

        for size, (gene_indices, mcc_dict_abs, up_or_down_dict) in signatures_dict.items():
            print(f" Signature size: {size}")
            gene_indices = np.array(gene_indices)
            ad_subset_genes = ad[:, gene_indices]

            subset_A = ad_subset_genes[obs_indices, :]
            rest_indices_bool = ~ad.obs.index.isin(ad.obs.index[obs_indices])
            rest = ad_subset_genes[rest_indices_bool, :]

            X_A = subset_A.X
            X_rest = rest.X
            X = vstack([X_A, X_rest])
            y = np.concatenate((np.ones(X_A.shape[0]), np.zeros(X_rest.shape[0])))

            mcc_scores, precision_scores, recall_scores, f1_scores = [], [], [], []
            n_runs = 10

            for run in range(n_runs):
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.3, stratify=y, random_state=run
                )
                clf = SVC(kernel='linear', class_weight='balanced', C=1.0, random_state=run)
                clf.fit(X_train, y_train)
                y_pred = clf.predict(X_test)

                mcc_scores.append(matthews_corrcoef(y_test, y_pred))
                precision_scores.append(precision_score(y_test, y_pred))
                recall_scores.append(recall_score(y_test, y_pred))
                f1_scores.append(f1_score(y_test, y_pred))

            all_results[size] = {
                "MCC_Mean": np.mean(mcc_scores),
                "MCC_Std": np.std(mcc_scores),
                "Precision_Mean": np.mean(precision_scores),
                "Precision_Std": np.std(precision_scores),
                "Recall_Mean": np.mean(recall_scores),
                "Recall_Std": np.std(recall_scores),
                "F1_Mean": np.mean(f1_scores),
                "F1_Std": np.std(f1_scores)
            }

            print(f"✅ Size {size}: MCC={np.mean(mcc_scores):.4f}, F1={np.mean(f1_scores):.4f}")

        # === Format as Flattened CSV Row ===
        flattened_row = {"Benchmark": benchmark_name, "DE_Time_Taken": elapsed_time}
        for size in [1, 3, 10, 20]:
            metrics = all_results.get(size)
            if metrics:
                flattened_row.update({
                    f"{size}_features_mcc": metrics["MCC_Mean"],
                    f"{size}_features_mcc_std": metrics["MCC_Std"],
                    f"{size}_features_precision": metrics["Precision_Mean"],
                    f"{size}_features_precision_std": metrics["Precision_Std"],
                    f"{size}_features_recall": metrics["Recall_Mean"],
                    f"{size}_features_recall_std": metrics["Recall_Std"],
                    f"{size}_features_f1": metrics["F1_Mean"],
                    f"{size}_features_f1_std": metrics["F1_Std"]
                })

        df_new = pd.DataFrame([flattened_row])
        csv_path = '/home/nisma/Benchmark_Signature_Stats1.csv'

        if os.path.exists(csv_path):
            df_existing = pd.read_csv(csv_path)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new

        df_combined.to_csv(csv_path, index=False)
        print(f"📝 CSV updated at: {csv_path}")

        return csv_path



    def sign_A_vs_B(ad, obs_indices_A, obs_indices_B, dv, ms_sign, sign_nr, label_sign):
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
        if of_text != "":
            label_signature.visible = True

    multiselect_signature.on_change(
        "value", lambda attr, old, new: multiselect_function(new)
    )

    def label_function(feature_list):
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
