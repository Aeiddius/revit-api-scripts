# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, Level, ViewPlan, FilledRegion, CurveLoop, FilteredElementCollector

from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

from System.Collections.Generic import List
clr.AddReference("System.Core")
from System.Linq import Enumerable

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
target_subgroup = "b. Tower A"
target_discipline = {
    "Key Plan": Discipline(3933275, 3858363),
    # "Key Plan": Discipline(3933275, 3858363) ,
    # "Crop": Discipline(5891600, 5891630) ,
    # "Device": Discipline(1969664, 5907457) ,
    # "Lighting": Discipline(1583644, 3806795),
} # discipline / view family plan id / view template id

prefix = {
    "Lighting": "L",
    "Device": "DP",
}
# Body 
@transaction    
def start():
    view = get_element(3831030)
    group = get_element(8367867)
    # detail_1 = get_element(8525369)
    # detail_2 = get_element(8556910)

    # # ids = group.ShowAttachedDetailGroups(view, detail_1.Id)
    # available = group.GetAvailableAttachedDetailGroupTypeIds()
    # for i in list(available):
    #     elem = get_element(i)
    #     y = get_parameter(elem, "Type Name")
    #     print(y)

    set_parameter(group, "Workset", 784)

    
if activate:  
    start()  
OUT = output.getvalue()  