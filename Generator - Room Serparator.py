# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, UV, ViewPlan, \
                              Element, CurveArray, SketchPlane, XYZ, \
                              FilteredElementCollector, BuiltInCategory

from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

from System.Collections.Generic import List

clr.AddReference('System')
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")

# For Outputting print to watch node
output = StringIO()
sys.stdout = output

# Scrict setup 
doc = DocumentManager.Instance.CurrentDBDocument
active_view = doc.ActiveView


def transaction(func):
    def wrapper(*args, **kwargs):
        TransactionManager.Instance.ForceCloseTransaction()
        TransactionManager.Instance.EnsureInTransaction(doc)
        func(*args, **kwargs)
        TransactionManager.Instance.TransactionTaskDone()
        # doc.Regenerate()
    return wrapper 

# importing lib
activate = IN[1] # type: ignore 
for script in IN[0]: # type: ignore
    exec(script)

# Functions and matrix definition
matrix: dict[str, any] = locals().get("matrix_a")
print_member: Callable[[any], None] = globals().get("print_member")
get_element  = globals().get("get_element")
get_elements = globals().get("get_elements")
get_element_via_parameter = globals().get("get_element_via_parameter")
get_view_range = globals().get("get_view_range")
get_num: Callable[[str], int] = globals().get("get_num")
get_parameter: Callable[[Element, str], str] = globals().get("get_parameter")
set_parameter: Callable[[Element, str, any], bool] = globals().get("set_parameter")
is_dependent: Callable[[ViewPlan], bool] = globals().get("is_dependent")

#==== Template ends here ====# 

# This script is intended to generate unit sheet views


# Parameters 
target_subgroup = "Tower B"
target_range = [1, 43]

def calculate_centroid(curve_array):
    # Create a list of points
    points = []
    
    for curve in curve_array:
        # Use the midpoint of each curve
        midpoint = curve.Evaluate(0.5, True)  # Midpoint at t=0.5
        points.append(midpoint)
    
    # Now calculate the centroid of these points (average of X, Y coordinates)
    sum_x = sum([point.X for point in points])
    sum_y = sum([point.Y for point in points])
    
    centroid_x = sum_x / len(points)
    centroid_y = sum_y / len(points)
    
    return UV(centroid_x, centroid_y)

# Body 
@transaction     
def start():
    # Delete all rooms
    rooms = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType().ToElements()
    for room in rooms:
        doc.Delete(room.Id)

    # Delete all room separator
    separators = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_RoomSeparationLines).WhereElementIsNotElementType().ToElements()
    for lines in separators:
            doc.Delete(lines.Id)

    # Get list of views
    for tower in ["A", "B"]:
        views = get_view_range("2. Presentation Views",
                                f"Tower {tower}",
                                "Device", # default, rooms exists in all views
                                target_range,
                                True)
        
        for target_view in views:  


            sketch_plane = SketchPlane.Create(doc, target_view.GenLevel.Id)
            crop_manager = target_view.GetCropRegionShapeManager()
            crop_shape = crop_manager.GetCropShape()
            curve_array = CurveArray()
            for curve in crop_shape[0].GetCurveLoopIterator():
                curve_array.Append(curve)
            doc.Create.NewRoomBoundaryLines(sketch_plane, curve_array, target_view)

            uv_point = calculate_centroid(curve_array)
            room = doc.Create.NewRoom(target_view.GenLevel, uv_point)

            view_name = target_view.Name.split(" ")
            # name = view_name[4].replace(")", "")
            # number = view_name[2] + view_name[3].replace("(", "")
            name = view_name[2].replace("-DP", "")
            number = view_name[1]
            set_parameter(room, "Name", name)
            set_parameter(room, "Number", number) 
            param = get_parameter(room, "Name") 
            print(param, room.Id)  
              
if activate:     
    start()   
OUT = output.getvalue()     