from bokeh.models import Button, CustomJS

def download_selected_button(source, original_keys):
    button = Button(label="Download selected as CSV", button_type="success", width=235)
    button.js_on_click(CustomJS(args=dict(source=source, okeys=original_keys), code="""
        const inds = source.selected.indices;
        const data = source.data;
        if (inds.length === 0) {
            alert('No points selected!');
            return;
        }
        const columns = okeys;
        let csv = 'index,name,' + columns.join(',') + '\\n';
        for (let i = 0; i < inds.length; i++) {
            let row = [];
            row.push(data['index'][inds[i]]);
            row.push(data['name'][inds[i]]);
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