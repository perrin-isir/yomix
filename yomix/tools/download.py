# """
# Handles data import and export functionality and provides
# utility functions for saving and loading selections of
# data points.
# """

from bokeh.models import Button, CustomJS
import bokeh.models
import numpy as np


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


def relabel_selection_button(
    source: bokeh.models.ColumnDataSource,
    select_color_by: bokeh.models.Select,
    unique_dict: dict,
    obs_string: list,
    trigger_legend_refresh,
) -> tuple[bokeh.models.TextInput, bokeh.models.Button]:
    """
    Create a button that pops up a dialog to (re)label selected points
    within the currently active "Color by" field.

    The popup asks for a label name and the target field, then applies the
    label server-side (replacing any previous assignment of that label name
    so the selection is always an exact replacement, not an addition).
    Colors and the legend are refreshed automatically.

    Args:
        source : bokeh.models.ColumnDataSource
            Data source containing the data points.
        select_color_by : bokeh.models.Select
            The "Color by" dropdown — its current value determines which
            field is being labelled.
        unique_dict : dict
            Dictionary mapping field names to their unique values.
        obs_string : list
            Mutable list of categorical obs field names (user-created fields
            are appended here so the legend handles them).
        trigger_legend_refresh : callable
            Callable ``(field_name: str) -> None`` that clears the legend
            cache for *field_name* and rebuilds the legend widgets.

    Returns:
        Tuple containing:
            - **hidden_relay** (:class:`bokeh.models.TextInput`): Invisible
              relay widget (must be in the document layout).
            - **button** (:class:`bokeh.models.Button`): "Label selection" button.
    """

    hidden_relay = bokeh.models.TextInput(value="", visible=False, width=1)

    def apply_relabel(attr, old, new):
        if not new or "|" not in new:
            return
        field, label_name = new.split("|", 1)
        if field not in source.data:
            hidden_relay.value = ""
            return
        inds = list(source.selected.indices)
        if not inds:
            hidden_relay.value = ""
            return

        current_labels = list(source.data[field])

        for i in inds:
            current_labels[i] = label_name

        new_unique = sorted(set(current_labels))
        unique_dict[field] = new_unique

        # Compute colors directly in Python so the scatter plot updates
        # immediately without depending on a JS round-trip.
        n = len(new_unique)
        step = 1.0 / max(n - 1, 1) * 0.999999
        val_map = {new_unique[0]: -1.0}
        for i in range(1, n):
            val_map[new_unique[i]] = i * step - 1.0
        new_colors = np.array(
            [val_map.get(lbl, -1.0) for lbl in current_labels], dtype=np.float32
        )

        new_data = dict(source.data)
        new_data[field] = np.array(current_labels, dtype=object)
        new_data["color"] = new_colors
        source.data = new_data

        # Rebuild legend widgets for this field.
        trigger_legend_refresh(field)

        # Ensure the dropdown reflects the active field.
        if field not in list(select_color_by.options):
            select_color_by.options = [field] + list(select_color_by.options)
        if select_color_by.value != field:
            select_color_by.value = field

        hidden_relay.value = ""

    hidden_relay.on_change("value", apply_relabel)

    button = Button(label="Label selection", button_type="warning", width=112)

    js_callback = CustomJS(
        args=dict(relay=hidden_relay, color_by=select_color_by),
        code="""
        const currentField = color_by.value;
        if (!currentField) {
            alert('Please select a "Color by" field first.');
            return;
        }

        const overlay = document.createElement('div');
        overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;'
            + 'background:rgba(0,0,0,0.45);z-index:9999;'
            + 'display:flex;align-items:center;justify-content:center;';

        const box = document.createElement('div');
        box.style.cssText = 'background:#fff;padding:22px 24px;border-radius:8px;'
            + 'min-width:420px;font-family:sans-serif;'
            + 'box-shadow:0 4px 24px rgba(0,0,0,0.28);';
        box.innerHTML =
            '<p style="margin:0 0 12px;font-size:14px">'
            + '<b>Label name:</b>&nbsp;'
            + '<input id="ym_label_input" type="text" '
            + 'style="width:200px;padding:4px 6px;font-size:14px;'
            + 'border:1px solid #ccc;border-radius:3px;">'
            + '</p>'
            + '<p style="margin:0 0 18px;font-size:13px">'
            + 'Are you sure you want to label this selection inside '
            + '<b>' + currentField + '</b>?'
            + '</p>'
            + '<button id="ym_yes" style="background:#28a745;color:#fff;border:none;'
            + 'padding:7px 20px;cursor:pointer;border-radius:4px;'
            + 'margin-right:10px;font-size:13px;">YES</button>'
            + '<button id="ym_no" style="background:#dc3545;color:#fff;border:none;'
            + 'padding:7px 20px;cursor:pointer;border-radius:4px;font-size:13px;">'
            + 'NO</button>';

        overlay.appendChild(box);
        document.body.appendChild(overlay);
        const inp = box.querySelector('#ym_label_input');
        inp.focus();

        box.querySelector('#ym_yes').onclick = () => {
            const labelName = inp.value.trim();
            if (!labelName) { alert('Please enter a label name.'); return; }
            document.body.removeChild(overlay);
            relay.value = currentField + '|' + labelName;
        };
        box.querySelector('#ym_no').onclick = () => {
            document.body.removeChild(overlay);
        };
        inp.onkeydown = (e) => {
            if (e.key === 'Enter') box.querySelector('#ym_yes').click();
            if (e.key === 'Escape') box.querySelector('#ym_no').click();
        };
        """,
    )

    button.js_on_click(js_callback)
    return hidden_relay, button


def create_new_field_button(
    source: bokeh.models.ColumnDataSource,
    select_color_by: bokeh.models.Select,
    unique_dict: dict,
    obs_string: list,
    trigger_legend_refresh,
) -> tuple[bokeh.models.TextInput, bokeh.models.Button]:
    """
    Create a button that pops up a dialog to create a new labelling field.

    The popup asks for a field name, then adds that field to the data source
    (initialised to ``"unlabeled"`` for all points), registers it with the
    legend system, and switches the "Color by" dropdown to it.

    Args:
        source : bokeh.models.ColumnDataSource
            Data source to extend with the new field.
        select_color_by : bokeh.models.Select
            The "Color by" dropdown — will be switched to the new field.
        unique_dict : dict
            Dictionary mapping field names to their unique values.
        obs_string : list
            Mutable list of categorical obs field names — the new field is
            appended here so the legend system treats it as categorical.
        trigger_legend_refresh : callable
            Callable ``(field_name: str) -> None`` that rebuilds the legend
            for a given field.

    Returns:
        Tuple containing:
            - **hidden_relay** (:class:`bokeh.models.TextInput`): Invisible
              relay widget (must be in the document layout).
            - **button** (:class:`bokeh.models.Button`): "Create new field" button.
    """

    hidden_relay = bokeh.models.TextInput(value="", visible=False, width=1)

    def create_field(attr, old, new):
        if not new:
            return
        field_name = new.strip()
        if not field_name:
            hidden_relay.value = ""
            return

        n = len(source.data["color"])
        new_field = np.full(n, "unlabeled", dtype=object)

        new_data = dict(source.data)
        new_data[field_name] = new_field
        source.data = new_data

        unique_dict[field_name] = ["unlabeled"]

        if field_name not in obs_string:
            obs_string.append(field_name)

        if field_name not in list(select_color_by.options):
            select_color_by.options = [field_name] + list(select_color_by.options)

        # Build legend and switch view to the new field.
        trigger_legend_refresh(field_name)
        select_color_by.value = field_name

        hidden_relay.value = ""

    hidden_relay.on_change("value", create_field)

    button = Button(label="Create new field", button_type="warning", width=112)

    js_callback = CustomJS(
        args=dict(relay=hidden_relay),
        code="""
        const overlay = document.createElement('div');
        overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;'
            + 'background:rgba(0,0,0,0.45);z-index:9999;'
            + 'display:flex;align-items:center;justify-content:center;';

        const box = document.createElement('div');
        box.style.cssText = 'background:#fff;padding:22px 24px;border-radius:8px;'
            + 'min-width:320px;font-family:sans-serif;'
            + 'box-shadow:0 4px 24px rgba(0,0,0,0.28);';
        box.innerHTML =
            '<p style="margin:0 0 18px;font-size:14px">'
            + '<b>Name new field:</b>&nbsp;'
            + '<input id="ym_field_input" type="text" '
            + 'style="width:180px;padding:4px 6px;font-size:14px;'
            + 'border:1px solid #ccc;border-radius:3px;">'
            + '</p>'
            + '<button id="ym_ok" style="background:#28a745;color:#fff;border:none;'
            + 'padding:7px 20px;cursor:pointer;border-radius:4px;'
            + 'margin-right:10px;font-size:13px;">OK</button>'
            + '<button id="ym_cancel" style="background:#dc3545;color:#fff;border:none;'
            + 'padding:7px 20px;cursor:pointer;border-radius:4px;font-size:13px;">'
            + 'Cancel</button>';

        overlay.appendChild(box);
        document.body.appendChild(overlay);
        const inp = box.querySelector('#ym_field_input');
        inp.focus();

        box.querySelector('#ym_ok').onclick = () => {
            const fieldName = inp.value.trim();
            if (!fieldName) { alert('Please enter a field name.'); return; }
            document.body.removeChild(overlay);
            relay.value = fieldName;
        };
        box.querySelector('#ym_cancel').onclick = () => {
            document.body.removeChild(overlay);
        };
        inp.onkeydown = (e) => {
            if (e.key === 'Enter') box.querySelector('#ym_ok').click();
            if (e.key === 'Escape') box.querySelector('#ym_cancel').click();
        };
        """,
    )

    button.js_on_click(js_callback)
    return hidden_relay, button


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
        ``Save selection`` button (:class:`bokeh.models.Button`) :
            On click, it downloads the currently selected points as a CSV file.

    """

    button = Button(label="Save selection", button_type="success", width=112)
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
    select_color_by: bokeh.models.Select,
) -> bokeh.models.Button:
    """
    Create a button to save the currently active field's labels to a CSV file.

    The saved CSV has the format ``name\\t<field_name>`` so it can be reloaded
    by :func:`load_labels_button` into the correct field.

    Args:
        source : bokeh.models.ColumnDataSource
            Data source containing the label fields.
        select_color_by : bokeh.models.Select
            The "Color by" dropdown — its current value names the field to save.

    Returns:
        ``Save field`` button (:class:`bokeh.models.Button`) :
            On click, downloads all points with their labels as a TSV/CSV file.
    """

    button = Button(label="Save field", button_type="success", width=112)
    button.js_on_click(
        CustomJS(
            args=dict(source=source, color_by=select_color_by),
            code="""
        const field = color_by.value;
        if (!field) {
            alert('Please select a "Color by" field to save.');
            return;
        }
        const data = source.data;
        const labels = data[field];
        if (!labels) {
            alert('Selected field not found in data.');
            return;
        }
        const names = data['name'];
        const hasContent = labels.some(
            l => l !== 'unlabeled' && l !== undefined && l !== null && l !== ''
        );
        if (!hasContent) {
            alert('No labels have been assigned in this field yet!');
            return;
        }
        let csv = 'name\\t' + field + '\\n';
        for (let i = 0; i < names.length; i++) {
            csv += names[i] + '\\t' + labels[i] + '\\n';
        }
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = field + '_labels.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        alert('Labels saved to ' + field + '_labels.csv');
    """,
        )
    )
    return button


def load_labels_button(
    source: bokeh.models.ColumnDataSource,
    select_color_by: bokeh.models.Select,
    unique_dict: dict,
    obs_string: list,
    trigger_legend_refresh,
) -> tuple[bokeh.models.TextInput, bokeh.models.Button]:
    """
    Create a button to load labels from a CSV file into the data source.

    The CSV must have the format ``name\\t<field_name>`` (tab-separated, first
    line is the header).  If the named field does not yet exist it is created
    and initialised to ``"unlabeled"`` before the loaded values are applied.

    The button opens a file picker in the browser.  The selected file's raw
    text is relayed to a hidden :class:`~bokeh.models.TextInput` which
    triggers a server-side Python callback that updates the data source,
    recomputes colors, and rebuilds the legend — avoiding the race condition
    that arises when these steps are performed purely client-side.

    Args:
        source : bokeh.models.ColumnDataSource
            Data source to update with loaded labels.
        select_color_by : bokeh.models.Select
            The "Color by" dropdown — will be switched to the loaded field.
        unique_dict : dict
            Dictionary mapping field names to their unique values.
        obs_string : list
            Mutable list of categorical obs field names — new fields are
            appended here so the legend handles them.
        trigger_legend_refresh : callable
            Callable ``(field_name: str) -> None`` that rebuilds the legend.

    Returns:
        Tuple containing:
            - **hidden_csv_input** (:class:`bokeh.models.TextInput`): Invisible relay
              widget (must be present in the document layout).
            - **button** (:class:`bokeh.models.Button`): "Load field" button.
    """

    # Invisible relay: JS writes raw file content here; Python reads it.
    hidden_csv_input = bokeh.models.TextInput(value="", visible=False, width=1)

    def process_csv(attr, old, new):
        if not new:
            return
        lines = new.strip().split("\n")
        if not lines:
            hidden_csv_input.value = ""
            return
        # Read field name from the header's second column.
        header_parts = lines[0].split("\t")
        if len(header_parts) < 2:
            hidden_csv_input.value = ""
            return
        field_name = header_parts[1].strip()

        n = len(source.data["color"])
        name_to_idx = {name: i for i, name in enumerate(source.data["name"])}

        # Start from existing labels or a blank slate.
        if field_name in source.data:
            old_labels = list(source.data[field_name])
        else:
            old_labels = ["unlabeled"] * n

        for line in lines[1:]:  # skip header
            parts = line.split("\t")
            if len(parts) >= 2:
                name, label = parts[0], parts[1].strip()
                if name in name_to_idx:
                    old_labels[name_to_idx[name]] = label

        new_labels = np.array(old_labels, dtype=object)
        new_unique = sorted(set(old_labels))
        unique_dict[field_name] = new_unique

        # Compute colors in Python for an immediate, reliable update.
        n_u = len(new_unique)
        step = 1.0 / max(n_u - 1, 1) * 0.999999
        val_map = {new_unique[0]: -1.0}
        for i in range(1, n_u):
            val_map[new_unique[i]] = i * step - 1.0
        new_colors = np.array(
            [val_map.get(lbl, -1.0) for lbl in old_labels], dtype=np.float32
        )

        new_data = dict(source.data)
        new_data[field_name] = new_labels
        new_data["color"] = new_colors
        source.data = new_data

        if field_name not in obs_string:
            obs_string.append(field_name)

        if field_name not in list(select_color_by.options):
            select_color_by.options = [field_name] + list(select_color_by.options)

        # Rebuild legend and switch view.
        trigger_legend_refresh(field_name)
        select_color_by.value = field_name

        # Reset relay so the same file can be reloaded if needed.
        hidden_csv_input.value = ""

    hidden_csv_input.on_change("value", process_csv)

    button = Button(label="Load field", button_type="success", width=112)

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
