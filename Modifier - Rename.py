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
activate = IN[1]  # type: ignore
for script in IN[0]:  # type: ignore
    exec(script)

# Functions and matrix definition
matrix: dict[str, any] = locals().get("matrix_a")
print_member: Callable[[any], None] = globals().get("print_member")
get_element = globals().get("get_element")
get_elements = globals().get("get_elements")
get_element_via_parameter = globals().get("get_element_via_parameter")
get_view_range = globals().get("get_view_range")
get_num: Callable[[str], int] = globals().get("get_num")
get_parameter: Callable[[Element, str], str] = globals().get("get_parameter")
set_parameter: Callable[[Element, str, any],
                        bool] = globals().get("set_parameter")
is_dependent: Callable[[ViewPlan], bool] = globals().get("is_dependent")

# ==== Template ends here ====#

# This script is intended to generate unit sheet views


# Parameters
target_range = [1, 2]
def capitalize_words(s):
    return ' '.join(word.capitalize() for word in s.split())

# Body
@transaction
def start():
 


    views = get_view_range("2. Presentation Views",
                           "a. Block C",
                           "Underground",
                           dependent_only=False)
 
    for view in views:
       
        view.Name = view.Name.replace("LEVEL ", "Level ")

if activate:
    start()
OUT = output.getvalue()
