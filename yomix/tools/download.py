from bokeh.models import Button, CustomJS

def download_selected_button(source):
    button = Button(label="Download Selected as CSV", button_type="success", width=235)
    button.js_on_click(CustomJS(args=dict(source=source), code="""
        const inds = source.selected.indices;
        const data = source.data;
        if (inds.length === 0) {
            alert('No points selected!');
            return;
        }
        const columns = Object.keys(data);
        let csv = columns.join(',') + '\\n';
        for (let i = 0; i < inds.length; i++) {
            let row = [];
            for (let j = 0; j < columns.length; j++) {
                row.push(data[columns[j]][inds[i]]);
            }
            csv += row.join(',') + '\\n';
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
    """))
    return button