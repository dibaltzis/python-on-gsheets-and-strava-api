from charts_helpers import ( 
    build_chart_request,
    get_contiguous_ranges,
    split_data_by_week,
    compute_y_axis_window,
    find_existing_chart_id,
    execute_request
)

# Main Chart class to handle chart creation and updating
class Chart:
    def __init__(self, chart_type, chart_name, chart_style, origin_sheet, target_sheet, x_column, y_column, options=None):
        self.chart_type = chart_type.upper()
        self.chart_name = chart_name
        self.chart_style = chart_style
        self.origin_sheet = origin_sheet
        self.target_sheet = target_sheet
        self.x_column = x_column.upper()
        self.y_column = y_column.upper()
        self.options = options or {}
    # Create or update chart in the target sheet
    def create_chart(
        self,
        service,
        spreadsheet_id,
        graph_pos_row,
        graph_pos_col,
        weekly=False,
    ) -> bool:
        values = self.origin_sheet.get_all_values()[1:]  # skip header
        if not values:
            print("No data available.")
            return False

        if not weekly:
            x_range, y_range, range_info = get_contiguous_ranges(self.origin_sheet, self.x_column, self.y_column)
            if not x_range or not y_range:
                print("No valid contiguous data range found.")
                return False

            y_min, y_max = compute_y_axis_window(self.origin_sheet, range_info)
            existing_id = find_existing_chart_id(service, spreadsheet_id, self.chart_name)

            if existing_id:
                update_request = build_chart_request(
                    chart_id=existing_id,
                    chart_name=self.chart_name,
                    chart_type=self.chart_type,
                    x_range=x_range,
                    y_range=y_range,
                    y_min=y_min,
                    y_max=y_max,
                    update=True
                )
                return execute_request(service, spreadsheet_id, update_request, self.chart_name)

            chart_request = build_chart_request(
                chart_name=self.chart_name,
                chart_type=self.chart_type,
                x_range=x_range,
                y_range=y_range,
                y_min=y_min,
                y_max=y_max,
                target_sheet_id=self.target_sheet.id,
                graph_pos_row=graph_pos_row,
                graph_pos_col=graph_pos_col
            )
            return execute_request(service, spreadsheet_id, chart_request, self.chart_name)

        # Weekly charts
        weekly_data = split_data_by_week(values, self.x_column, self.y_column)
        if not weekly_data:
            print("No valid weekly data found.")
            return False

        # Horizontal weekly charts
        col_spacing = 4  # number of columns between charts
        for x_range, y_range, week_start, week_end, week_num in weekly_data:
            range_info = {"y_col": y_range["startColumnIndex"]}
            y_min, y_max = compute_y_axis_window(self.origin_sheet, range_info)

            chart_col = graph_pos_col + (week_num - 1) * col_spacing  
            chart_name = "Week "+str(week_num)+" : "+str(week_start).replace("-","/")+" - "+str(week_end).replace("-","/")
            existing_id = find_existing_chart_id(service, spreadsheet_id, chart_name)
            
            if existing_id:
                update_request = build_chart_request(
                    chart_id=existing_id,
                    chart_name=chart_name,
                    chart_type=self.chart_type,
                    x_range={**x_range, "sheetId": self.origin_sheet.id},
                    y_range={**y_range, "sheetId": self.origin_sheet.id},
                    y_min=y_min,
                    y_max=y_max,
                    width_pixels=400,
                    height_pixels=400,
                    update=True
                )
                execute_request(service, spreadsheet_id, update_request, chart_name)
            else:
                chart_request = build_chart_request(
                    chart_name=chart_name,
                    chart_type=self.chart_type,
                    x_range={**x_range, "sheetId": self.origin_sheet.id},
                    y_range={**y_range, "sheetId": self.origin_sheet.id},
                    y_min=y_min,
                    y_max=y_max,
                    target_sheet_id=self.target_sheet.id,
                    width_pixels=400,
                    height_pixels=400,
                    graph_pos_row=graph_pos_row,  # same row
                    graph_pos_col=chart_col
                )
                execute_request(service, spreadsheet_id, chart_request, chart_name)
        return True
