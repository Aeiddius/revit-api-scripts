import clr
from io import StringIO
from typing import Optional

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import XYZ


class Offset:

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


class UnitDetail:

    def __init__(self,
                 min: int,
                 max: int,
                 pos={},
                 exclude=[],
                 ortn: str = "",
                 sheet: str = "",
                 sheet_data={}
                 ):
        self.min = min
        self.max = max
        self.pos = pos
        self.exclude = exclude
        self.ortn = ortn

        self.sheet = sheet
        self.sheet_data = sheet_data


matrix_a = {
    # Level 2A
    "01 A-2BR.3": UnitDetail(2, 2, ),
    "02 A-2AR": UnitDetail(2, 37, {}, [4]),
    "03 A-1BR": UnitDetail(2, 35, ),
    "04 A-1B": UnitDetail(2, 35, ),
    "05 A-2A": UnitDetail(2, 34, ),
    "06 A-2B": UnitDetail(2, 34, ),
    "07 A-2BR": UnitDetail(2, 38, {35:"06", 36:"05", 37:"05", 38:"04"}, [3, 4, 32]),
    "08 A-2AR.1": UnitDetail(2, 2, ),
    "09 A-2C": UnitDetail(2, 2, ),
    
    # Level 3
    "01 A-2BR.4": UnitDetail(3, 32, {}, [4]),
    "07 A-2BR.4": UnitDetail(3, 32, {}, [4]),
    "08 A-2AR": UnitDetail(3, 38, {35:"07", 36:"06", 37:"06", 38:"05"}, [4]),
    "09 A-2A": UnitDetail(3, 4, {4:"11"}),
    "10 A-2B": UnitDetail(3, 4, {4:"12"}),

    # Level 4
    "01 A-1D": UnitDetail(4, 4, ),
    "02 A-3K": UnitDetail(4, 4, ),
    "07 A-1D": UnitDetail(4, 4, ),
    "08 A-3K": UnitDetail(4, 4, ),
    "09 A-1AR": UnitDetail(4, 36, {35:"08", 36:"07"}, [32]),
    "10 A-1A": UnitDetail(4, 4, ),

    # Level 32
    "09 A-3E": UnitDetail(32, 32, ),
    "10 A-2B.1": UnitDetail(32, 32, ),

    # Level 33A
    "01 A-2BR": UnitDetail(33, 37, ),
    "10 A-1C": UnitDetail(33, 36, {35: "09", 36: "08"}),
    "11 A-2D.3": UnitDetail(33, 36, {35:"10", 36:"09"}),

    # Level 35A
    "05 A-3B": UnitDetail(35, 35, ),

    # Level 36A
    "03 A-3F": UnitDetail(36, 36, ),
    "04 A-2B.1": UnitDetail(36, 36, ),

    # Level 37A
    "03 A-3G": UnitDetail(37, 37, ),
    "04 A-2D.1": UnitDetail(37, 37, ),
    "07 A-3D": UnitDetail(37, 39, {38:"06", 39:"05"}),
    "08 A-2D.1": UnitDetail(37, 39, {38:"07", 39:"06"}),

    # Level 38A
    "01 A-2BR.1": UnitDetail(38, 38, ),
    "02 A-3H": UnitDetail(38, 38, ),
    "03 A-2D.2": UnitDetail(38, 39, ),

    # Level 39A
    "01 A-2DR.1": UnitDetail(39, 39, ),
    "02 A-3A": UnitDetail(39, 43, {43:"01"}),
    "04 A-3BR": UnitDetail(39, 39, ),

    # Level 40A
    "01 A-2DR": UnitDetail(40, 42, ),
    "03 A-2D": UnitDetail(40, 42, ),
    "04 A-2BR.2": UnitDetail(40, 40, ),
    "05 A-3J": UnitDetail(40, 40, ),
    "06 A-2D": UnitDetail(40, 42, ),

    # Level 41A
    "04 A-2DR": UnitDetail(41, 42, ),
    "05 A-3DR": UnitDetail(41, 43, {42: "03", 43: "03"}),

    # Level 43A
    "02 A-3C": UnitDetail(43, 43, ),
    "04 A-3C": UnitDetail(43, 43, ),
}

matrix_b = {
    # Level 1B
    "161 BL-A FLEX": UnitDetail(1, 1, {}, []),
    "162 BL-B FLEX": UnitDetail(1, 1, {}, []),
    "163 BL-C FLEX": UnitDetail(1, 1, {}, []),
    "164 BL-D FLEX": UnitDetail(1, 1, {}, []),
    "165 BL-E FLEX": UnitDetail(1, 1, {}, []),
    "166 BL-F FLEX": UnitDetail(1, 1, {}, []),
    "167 BL-G FLEX": UnitDetail(1, 1, {}, []),
    "168 BL-H FLEX": UnitDetail(1, 1, {}, []),
    "169 BL-HR FLEX": UnitDetail(1, 1, {}, []),
    "170 BL-J FLEX": UnitDetail(1, 1, {}, []),
    "171 BL-K FLEX": UnitDetail(1, 1, {}, []),
    "172 BL-KR FLEX": UnitDetail(1, 1, {}, []),

    # Level 2B
    "161 BL-A RESI": UnitDetail(2, 2, {}, []),
    "162 BL-B RESI": UnitDetail(2, 2, {}, []),
    "163 BL-C RESI": UnitDetail(2, 2, {}, []),
    "164 BL-D RESI": UnitDetail(2, 2, {}, []),
    "165 BL-E RESI": UnitDetail(2, 2, {}, []),
    "166 BL-F RESI": UnitDetail(2, 2, {}, []),
    "167 BL-G RESI": UnitDetail(2, 2, {}, []),
    "168 BL-H RESI": UnitDetail(2, 2, {}, []),
    "169 BL-HR RESI": UnitDetail(2, 2, {}, []),
    "170 BL-J RESI": UnitDetail(2, 2, {}, []),
    "171 BL-K RESI": UnitDetail(2, 2, {}, []),
    "172 BL-KR RESI": UnitDetail(2, 2, {}, []),

    "01 BPR-1C": UnitDetail(2, 9, {}, [], ortn="Unit"),
    "02 BPR-2C ADA": UnitDetail(2, 4, {}, [], ortn="Unit"),
    "03 BPR-2BR": UnitDetail(2, 9, {}, [], ortn="Unit"),
    "04 BPR-2E": UnitDetail(2, 9, {}, [], ortn="Unit"),
    "05 BPR-2BR": UnitDetail(2, 9, {}, [], ortn="Unit"),
    "06 BPR-2B": UnitDetail(2, 9, {}, [], ortn="Unit"),
    "07 BPR-2BR": UnitDetail(2, 9, {}, [], ortn="Unit"),
    "08 BPR-2B": UnitDetail(2, 9, {}, [], ortn="Unit"),
    "09 OFFICE": UnitDetail(2, 2, {}, [], ortn="Unit"),
    "10 BPR-3B": UnitDetail(2, 8, {}, [], ortn="Unit"),
    "11 BPR-2D": UnitDetail(2, 8, {}, [], ortn="Unit"),
    "12 BPR-2AR": UnitDetail(2, 9, {}, [], ortn="Unit"),
    "13 BPR-1E": UnitDetail(2, 2, {}, [], ortn="Unit"),

    # Level 3B-4B
    "09 BPR-1D": UnitDetail(3, 9, {}, [], ortn="Unit"),
    "13 BPR-2A": UnitDetail(3, 9, {}, [], ortn="Unit"),
    "14 BPR-1A": UnitDetail(3, 9, {}, [], ortn="Unit"),
    "15 BPR-3A": UnitDetail(3, 9, {}, [], ortn="Unit"),
    "16 BPR-1B ADA": UnitDetail(3, 4, {}, [], ortn="Unit"),

    # Level 5B-8B
    "02 BPR-2C": UnitDetail(5, 9, {}, [], ortn="Unit"),
    "16 BPR-1B": UnitDetail(5, 9, {}, [], ortn="Unit"),

    # Level 9B
    "10 BPR-3B ADA": UnitDetail(9, 9, {}, [], ortn="Unit"),
    "11 BPR-2D ADA": UnitDetail(9, 9, {}, [], ortn="Unit"),

    # Level 10B
    "01 BTW-2B": UnitDetail(10, 32, {}, [], ortn="Unit"),
    "02 BTW-2AR": UnitDetail(10, 32, {}, [], ortn="Unit"),
    "03 BTW-2C": UnitDetail(10, 32, {}, [], ortn="Unit"),
    "04 BTW-2AR": UnitDetail(10, 32, {}, [], ortn="Unit"),
    "05 BTW-2C": UnitDetail(10, 32, {}, [], ortn="Unit"),
    "06 BTW-1A": UnitDetail(10, 32, {}, [], ortn="Unit"),
    "07 BTW-3A": UnitDetail(10, 32, {}, [], ortn="Unit"),
    "08 BTW-1AR": UnitDetail(10, 10, {}, [], ortn="Unit"),
    "09 BTW-2BR": UnitDetail(10, 32, {}, [], ortn="Unit"),
    "10 BTW-2A": UnitDetail(10, 32, {}, [], ortn="Unit"),
    "11 BTW-2CR": UnitDetail(10, 32, {}, [], ortn="Unit"),
    "12 BTW-1B": UnitDetail(10, 32, {}, [], ortn="Unit"),

    # Level 11B
    "08 BTW-1C": UnitDetail(10, 32, {}, [], ortn="Unit"),

}
