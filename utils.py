import datetime

# ################################################
# Returns the date of the next given weekday after
# the given date. For example, the date of next Monday.
#
# NB: if it IS the day we're looking for, this returns 0.
# consider then doing onDay(foo, day + 1).
#
# Monday=0, Tuesday=1 .... Sunday=6
# ################################################


def onDay(date, day):
    """
    Returns the date of the next given weekday after
    the given date. For example, the date of next Monday.

    NB: if it IS the day we're looking for, this returns 0.
    consider then doing onDay(foo, day + 1).
    """
    days = (day - date.weekday() + 7) % 7
    return date + datetime.timedelta(days=days)
