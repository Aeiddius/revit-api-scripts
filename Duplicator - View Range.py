# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, Level, ViewPlan, ViewDuplicateOption, CurveLoop, FilteredElementCollector

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
        TransactionManager.Instance.EnsureInTransaction(doc)
        func(*args, **kwargs)
        TransactionManager.Instance.TransactionTaskDone()
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

class Discipline:
    def __init__(self, family_id, template_id):
        self.family_id = ElementId(family_id)
        self.template_id = ElementId(template_id)

# Parameters
target_group = "2. Presentation Views"
target_subgroup = "c. Tower B"
view_template_id = 6564374
view_family_type_id = 9052421 # device parking
prefix = "RI"

# Body 
@transaction    
def start():

    # levels = FilteredElementCollector(doc).OfClass(Level).ToElements()
    source_views = get_view_range(target_group, target_subgroup, "Parking Device")
    target_views = get_view_range(target_group, target_subgroup, "Parking Rough-Ins")

    for sview, tview in zip(source_views, target_views):
        if sview.Name.replace("-DP", "") == tview.Name.replace("-RI", ""):
            view_range = sview.GetViewRange()
            tview.SetViewRange(view_range)
            print(view_range)

 
         
if activate:   
    start()  
 
OUT = output.getvalue()  