# Import
import clr
import sys
import os

sys.path.append(os.getenv(r'LOCALAPPDATA') + '\python-3.9.12-embed-amd64\Lib\site-packages')
import pyperclip 

from io import StringIO
from collections.abc import Callable
from pprint import pprint

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, ViewSheet, ViewPlan, \
    Element, Viewport, BuiltInCategory, XYZ, \
    FilteredElementCollector
from Autodesk.Revit.DB.Electrical import PanelScheduleView, PanelScheduleSheetInstance

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
matrix_a: dict[str, any] = locals().get("matrix_a")
matrix_b: dict[str, any] = locals().get("matrix_b")
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
is_category_this = globals().get("is_category_this")
collect_elements = globals().get("collect_elements")

# ==== Template ends here ====#

# This script is intended to generate unit sheet views


# Parameters
# Parameters
matrix = {
    "A": matrix_a,
    "B": matrix_b
}

# Functions

@transaction
def start():
    # active_view      

    target = ["1108"]

    views = get_view_range("3. Utility Views", "a. Key Plan", "Key Plan B", dependent_only=True)
    keyplan_dict = {}
    for view in views:
        number = view.Name.split(" ")[2]
        if number not in keyplan_dict:
            keyplan_dict[number] = view

    for num in target:
        kp_view = keyplan_dict[num]
 
        new_id = kp_view.Duplicate(ViewDuplicateOption.AsDependent)
        duplicated_view = doc.GetElement(new_id)
        duplicated_view.CropBoxVisible = False
        duplicated_view.CropBoxActive = True
        duplicated_view.Name = kp_view.Name.rsplit("-", 1)[0] + "-W"
        set_parameter(duplicated_view, "View Sub-Group", "") 
        pyperclip.copy(duplicated_view.Name)

if activate:
    start()
OUT = output.getvalue() 
   

# s ss s    s   s s  s     
  