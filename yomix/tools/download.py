# """
# Handles data import and export functionality and provides
# utility functions for saving and loading selections of
# data points.
# """

from bokeh.models import Button, CustomJS
import bokeh.models


def csv_load_button(
    source: bokeh.models.ColumnDataSource,
) -> bokeh.models.Button:
    """
    Create a button to load previously selected points from a CSV file.

    Args:
        source (bokeh.models.ColumnDataSource):
            Data source with at least a ``"name"`` field, against which CSV
            entries will be matched.

    Returns:
        ``Load selection`` button (:class:`bokeh.models.Button`) :
            On click, it prompts
            for a  CSV file and updates ``source.selected.indices`` with the
            matched entries.

    """

    # source = ColumnDataSource(data=dict(x=[], y=[]))  # Example fields

    button = Button(label="Load selection", button_type="success", width=112)

    # JavaScript to load CSV file and update ColumnDataSource
    callback = CustomJS(
        args=dict(source=source),
        code="""
        // Create an invisible file input
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.csv';
        input.style.display = 'none';

        // When a file is selected
        input.onchange = (e) => {

            const data = source.data;
            data['name'].length;

            var names_to_index = {}

            for (let i = 1; i < data['name'].length; i++) {
                names_to_index[data['name'][i]] = i;
            }

            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (event) => {
                const text = event.target.result;

                const lines = text.trim().split('\\n');
                const headers = lines[1].split(',');

                var t = [];

                for (let i = 1; i < lines.length; i++) {
                    const name = lines[i].split('\t')[0];
                    t.push(names_to_index[name]);
                }

                source.selected.indices = t;
                source.change.emit();
            };
            reader.readAsText(file);
        };

        // Trigger the input
        document.body.appendChild(input);
        input.click();
        document.body.removeChild(input);
    """,
    )

    button.js_on_click(callback)
    return button


def add_label_button(
    source: bokeh.models.ColumnDataSource,
    select_color_by: bokeh.models.Select,
    unique_dict: dict,
) -> tuple[bokeh.models.TextInput, bokeh.models.Button]:
    """
    Create a text input and button to assign a custom label to selected points.

    The text input accepts the desired label name; clicking the button
    applies it to all currently selected points via a server-side callback,
    so the data update and legend rebuild are always in sync (no race
    conditions between client-side patches and server-side callbacks).

    The labels are stored in the ``"custom_label"`` field of the data
    source and can be visualised via the "Color by" dropdown menu.

    Args:
        source : bokeh.models.ColumnDataSource
            Data source containing the data points.
        select_color_by : bokeh.models.Select
            The "Color by" dropdown menu.
        unique_dict : dict
            Dictionary mapping field names to their unique values.

    Returns:
        Tuple containing:
            - **label_input** (:class:`bokeh.models.TextInput`): Text input for the label name.
            - **button** (:class:`bokeh.models.Button`): "(Re)label selection" button.
    """

    label_input = bokeh.models.TextInput(
        placeholder="Enter label name...",
        width=235,
    )

    button = Button(label="(Re)label selection", button_type="warning", width=120)

    def apply_label():
        label_name = label_input.value.strip()
        if not label_name:
            return
        inds = list(source.selected.indices)
        if not inds:
            return

        # Patch the data source server-side so the legend rebuild that follows
        # always reads the already-updated data (no client→server race condition).
        source.patch({"custom_label": [(i, label_name) for i in inds]})

        # Refresh unique_dict so redefine_custom_legend sees the new label set.
        unique_dict["custom_label"] = sorted(set(source.data["custom_label"].tolist()))

        # Ensure 'custom_label' is in the dropdown options.
        if "custom_label" not in list(select_color_by.options):
            select_color_by.options = ["custom_label"] + list(select_color_by.options)

        # Trigger legend rebuild.  Toggle away first so on_change fires even
        # when the dropdown was already showing 'custom_label'.
        if select_color_by.value == "custom_label":
            select_color_by.value = ""
        select_color_by.value = "custom_label"

    button.on_click(apply_label)
    return label_input, button


def download_selected_button(
    source: bokeh.models.ColumnDataSource,
    original_keys: list[str],
) -> bokeh.models.Button:
    """
    Create a button to download selected points as a CSV file.

    Args:
        source : bokeh.models.ColumnDataSource
            Data source containing the selected points to be downloaded.
        original_keys : list of str
            Column names to include in the downloaded CSV file.

    Returns:
        ``Save selected`` button (:class:`bokeh.models.Button`) :
            On click, it downloads the currently selected points as a CSV file.

    """

    button = Button(label="Save selected", button_type="success", width=112)
    button.js_on_click(
        CustomJS(
            args=dict(source=source, okeys=original_keys),
            code="""
        const inds = source.selected.indices;
        const data = source.data;
        if (inds.length === 0) {
            alert('No points selected!');
            return;
        }
        const columns = okeys;
        let csv = 'sep=\t\\n' + 'name\t' + columns.join('\t') + '\\n';
        for (let i = 0; i < inds.length; i++) {
            let row = [];
            row.push(data['name'][inds[i]]);
            for (let j = 0; j < columns.length; j++) {
                row.push(data[columns[j]][inds[i]]);
            }
            csv += row.join('\t') + '\\n';
        }
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'selected_points.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    """,
        )
    )
    return button


def save_labels_button(
    source: bokeh.models.ColumnDataSource,
) -> bokeh.models.Button:
    """
    Create a button to save custom labels to a CSV file.

    Args:
        source : bokeh.models.ColumnDataSource
            Data source containing the custom_label field.

    Returns:
        ``Save labels`` button (:class:`bokeh.models.Button`) :
            On click, it downloads all points with their custom labels as a CSV file.
    """

    button = Button(label="Save labels", button_type="primary", width=112)
    button.js_on_click(
        CustomJS(
            args=dict(source=source),
            code="""
        const data = source.data;
        const names = data['name'];
        const labels = data['custom_label'];
        
        // Check if there are any non-default labels
        const hasLabels = labels.some(l => l !== 'unlabeled');
        if (!hasLabels) {
            alert('No custom labels have been assigned yet!');
            return;
        }
        
        let csv = 'name\\tcustom_label\\n';
        for (let i = 0; i < names.length; i++) {
            csv += names[i] + '\\t' + labels[i] + '\\n';
        }
        
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'custom_labels.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        alert('Labels saved to custom_labels.csv');
    """,
        )
    )
    return button


def load_labels_button(
    source: bokeh.models.ColumnDataSource,
    select_color_by: bokeh.models.Select,
    unique_dict: dict,
) -> tuple[bokeh.models.TextInput, bokeh.models.Button]:
    """
    Create a button to load custom labels from a CSV file.

    The button opens a file picker in the browser.  The selected file's
    raw text is relayed to a hidden :class:`~bokeh.models.TextInput` which
    triggers a server-side Python callback that patches the data source and
    rebuilds the legend — avoiding the race condition that arises when both
    steps are performed purely client-side.

    Args:
        source : bokeh.models.ColumnDataSource
            Data source to update with loaded labels.
        select_color_by : bokeh.models.Select
            The "Color by" dropdown menu.
        unique_dict : dict
            Dictionary mapping field names to their unique values.

    Returns:
        Tuple containing:
            - **hidden_csv_input** (:class:`bokeh.models.TextInput`): Invisible relay widget (must be present in the document layout).
            - **button** (:class:`bokeh.models.Button`): "Load labels" button.
    """

    # Invisible relay: JS writes raw file content here; Python reads it.
    hidden_csv_input = bokeh.models.TextInput(value="", visible=False, width=1)

    def process_csv(attr, old, new):
        if not new:
            return
        lines = new.strip().split("\n")
        name_to_idx = {name: i for i, name in enumerate(source.data["name"])}
        patches = []
        for line in lines[1:]:  # skip header
            parts = line.split("\t")
            if len(parts) >= 2:
                name, label = parts[0], parts[1].strip()
                if name in name_to_idx:
                    patches.append((name_to_idx[name], label))
        if patches:
            source.patch({"custom_label": patches})
            unique_dict["custom_label"] = sorted(
                set(source.data["custom_label"].tolist())
            )
            if "custom_label" not in list(select_color_by.options):
                select_color_by.options = ["custom_label"] + list(
                    select_color_by.options
                )
            if select_color_by.value == "custom_label":
                select_color_by.value = ""
            select_color_by.value = "custom_label"
        # Reset relay so the same file can be reloaded if needed.
        hidden_csv_input.value = ""

    hidden_csv_input.on_change("value", process_csv)

    button = Button(label="Load labels", button_type="primary", width=112)

    callback = CustomJS(
        args=dict(relay=hidden_csv_input),
        code="""
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.csv,.tsv,.txt';
        input.style.display = 'none';

        input.onchange = (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (event) => {
                // Forward raw file content to the Python relay callback.
                relay.value = event.target.result;
            };
            reader.readAsText(file);
        };

        document.body.appendChild(input);
        input.click();
        document.body.removeChild(input);
        """,
    )

    button.js_on_click(callback)
    return hidden_csv_input, button
