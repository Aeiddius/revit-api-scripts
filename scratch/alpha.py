target_view_name = "UNIT 0301 A-2A RI"

x = "A0401 PNL A2"
y = x.split(" ", 1)

unit_no = y[0]
panel_type = y[1]

unit_no_new = unit_no[0] + target_view_name.split(" ")[1] + " " + panel_type
print(unit_no_new)