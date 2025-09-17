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
