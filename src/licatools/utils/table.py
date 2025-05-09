
from astropy.table import Table

def tcn(table: Table, colnum: int) -> str:
    """Get Table Column Name"""
    result = None
    try:
        result = table.columns[colnum].name
    except AttributeError:
        # Quantity and Time objects as columns don't have a .name attribute
        result = table.columns[colnum].__dict__['info'].name
    return result

def tcu(table: Table, colnum: int) -> str:
    """Get Table Column Unit"""
    result = None
    try:
        result = table.columns[colnum].unit
    except AttributeError:
        # Time objects as columns don't have a .unit attribute
        # However, the expression below gives None as result
        result = table.columns[colnum].__dict__['info'].unit
    return result

