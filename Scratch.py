# Import
import clr
import sys
from io import StringIO
from collections.abc import Callable

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, BuiltInParameter, SectionType, ViewPlan, FilledRegion, CurveLoop, FilteredElementCollector
from Autodesk.Revit.DB.Electrical import PanelScheduleView, ElectricalSystem 
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


a2_spares = [
    [14, 1],
    [10, 6],
    [11, 6],
    [12, 6],
    [13, 6],
    [14, 6],
    [15, 6], 
] 

a1_spares = [
    [14, 1],

] 

a2_double_pole = [14, 1]
a1_double_pole = [[14, 1]]
 
# Body 
@transaction    
def start():
    template_a1 = get_element(7178103)
    template_a2 = get_element(7123164)
    # PanelScheduleView.CreateInstanceView(doc, template_a1.Id, ElementId(8693954))
    
    ps_view = get_element(8697420)
    for sp in a1_spares:
        r = sp[0]
        c = sp[1]
        ps_view.AddSpare(r, c)

        es = ps_view.GetCircuitByCell(r, c)
        set_parameter(es, "Load Name", "SPARE")
        if sp in a1_double_pole:
            set_parameter(es, "Number of Poles", 2)

 
if activate:    
    start()
OUT = output.getvalue()       