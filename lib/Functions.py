import clr
from io import StringIO
from typing import Optional

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, FilteredElementCollector, ViewPlan, BuiltInCategory

clr.AddReference('System')
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")


def print_member(obj: any) -> None:
    for i in dir(obj):
        print(i)

def get_element(id):
    doc = globals().get("doc")
    if isinstance(id, str) or isinstance(id, int):
        return doc.GetElement(ElementId(id))
    elif isinstance(id, ElementId):
        return doc.GetElement(id)
    return None

def get_elements(ids):
    doc = globals().get("doc")
    elements = []
    if all(isinstance(item, ElementId) for item in ids):
        for id in ids:
            elements.append(doc.GetElement(id))
    if all(isinstance(item, int) for item in ids):
        for id in ids:
            x = doc.GetElement(ElementId(id))
            elements.append(x)
    return elements

def get_element_via_parameter(elements, parameter_name, parameter_value):
    result = []
    for el in elements:
        param_ViewType = el.GetParameters(parameter_name)[0]
        if param_ViewType.AsValueString() == parameter_value:
            result.append(el)
            continue
    return result

def collect_elements(base_view, categories=[]):
    doc = globals().get("doc")
    element_collector = FilteredElementCollector(doc, base_view.Id)
    elements_filtered = []
    include_categories = [int(i) for i in categories]

    # elements filter
    for e in element_collector.WhereElementIsNotElementType().ToElements():
        category = e.Category
        if not category or (category and category.Id.IntegerValue not in include_categories): continue
        elements_filtered.append(e)
    return elements_filtered

def get_parameter(element, parameter: str) -> str:
    param = element.LookupParameter(parameter)
    val = param.AsValueString()
    
    if not param:
        param.Dispose()
        return None
    param.Dispose()
    return val

def set_parameter(element, parameter: str, value: any) -> bool:
    param = element.LookupParameter(parameter)
    if not param:
        param.Dispose()
        return None
    res = param.Set(value)
    param.Dispose()
    return res

def get_num(str: str) -> int:
  """
  gets the only number in a string. used to get floor level in strings

  :param str: the string which may have a number.
  """
  value = ''.join(char for char in str if char.isdigit()).strip()
  if not value:
      return None
  return int(value)

def is_dependent(view: ViewPlan) -> bool:
    """
    Function to check if view is dependent or not

    :param view: view plan of any type
    """
    if "Dependent on" in view.LookupParameter("Dependency").AsValueString():
        return True
    return False

def get_view_range(
        target_group: str,
        target_subgroup: str,
        target_family_type: str,
        range_value=None,
        dependent_only: bool = False,
        disable_subgroup_filter: bool = False,
    ) -> list[ViewPlan]:
    """
    Function to get list of views

    :param view_group: first order view grouping.
                       1. Working Views, 2. Presentation Views,
                       3. Utility Views, 4. Dynamo
    :param target_view_type: second order view grouping.
    :param target_family_type: A string representing the target family type.
    :param range_value: target range. includes min and max value. exactly two integers.
    """
    doc = globals().get("doc")

    result: list[ViewPlan] = []
    view_list: list[ViewPlan] = FilteredElementCollector(doc).OfClass(ViewPlan).ToElements()
    for view in view_list:
        # Filters
        if view.IsTemplate == True: continue
        if view.LookupParameter("View Group").AsValueString() != target_group: continue
        if not disable_subgroup_filter:
            if view.LookupParameter("View Sub-Group").AsValueString() != target_subgroup: continue
        if view.LookupParameter("Type").AsValueString() != target_family_type: continue
        if dependent_only==False and is_dependent(view): continue
        if dependent_only==True and not is_dependent(view): continue

        # Exception check
        if range_value and len(range_value) != 2:
            raise ValueError("range_value must be a list of exactly two integers")

        # Range value
        if range_value:
          min_range = range_value[0]
          max_range = range_value[1]

          level = get_num(view.GenLevel.Name)
          if min_range <= level <= max_range:
              result.append(view)
              continue
        else:
          result.append(view)
          continue
          
    return result

def is_category_this(element: any, category: BuiltInCategory):
    if not element: return False
    if not element.Category: return False
    return element.Category.Id.IntegerValue == int(category)