# Build Google Sheets chart request
def build_chart_request(
    chart_name,
    chart_type,
    x_range,
    y_range,
    y_min,
    y_max,
    target_sheet_id=None,
    graph_pos_row=None,
    graph_pos_col=None,
    chart_id=None,
    update=False,
    width_pixels=800,
    height_pixels=400,
    offset_x=0,
    offset_y=0,
    legend_position="BOTTOM_LEGEND",
    x_axis_title="Date",
    y_axis_title="Weight"
):
    """
    Returns a Google Sheets chart request dictionary.
    If `update` is True, builds an update request, otherwise a new addChart request.
    """

    spec = {
        "title": chart_name,
        "basicChart": {
            "chartType": chart_type,
            "legendPosition": legend_position,
            "axis": [
                {"position": "BOTTOM_AXIS", "title": x_axis_title},
                {
                    "position": "LEFT_AXIS",
                    "title": y_axis_title,
                    "viewWindowOptions": {
                        "viewWindowMin": y_min,
                        "viewWindowMax": y_max
                    }
                }
            ],
            "domains": [
                {"domain": {"sourceRange": {"sources": [x_range]}}}
            ],
            "series": [
                {
                    "series": {"sourceRange": {"sources": [y_range]}},
                    "targetAxis": "LEFT_AXIS"
                }
            ]
        }
    }

    if update:
        if chart_id is None:
            raise ValueError("chart_id must be provided for an update request")
        return {
            "updateChartSpec": {
                "chartId": chart_id,
                "spec": spec
            }
        }

    # New chart request
    return {
        "addChart": {
            "chart": {
                "spec": spec,
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": target_sheet_id,
                            "rowIndex": graph_pos_row,
                            "columnIndex": graph_pos_col
                        },
                        "offsetXPixels": offset_x,
                        "offsetYPixels": offset_y,
                        "widthPixels": width_pixels,
                        "heightPixels": height_pixels
                    }
                }
            }
        }
    }
