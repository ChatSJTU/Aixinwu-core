from datetime import timedelta

import pillow_avif  # noqa: F401 # imported for side effects
from openpyxl.utils.datetime import to_excel, to_ISO8601

from .celeryconf import app as celery_app

__all__ = ["celery_app"]
__version__ = "3.18.14"


class PatchedSubscriberExecutionContext:
    __slots__ = "exe_context", "errors"

    def __init__(self, exe_context):
        self.exe_context = exe_context
        self.errors = self.exe_context.errors

    def reset(self):
        self.errors = []

    def __getattr__(self, name):
        return getattr(self.exe_context, name)


_major, _minor, _ = __version__.split(".", 2)
schema_version = f"{_major}.{_minor}"
user_agent_version = f"Saleor/{schema_version}"


def patched_openpyxl_set_attributes(cell, styled=None):
    coordinate = cell.coordinate
    attrs = {"r": coordinate}
    if styled:
        attrs["s"] = f"{cell.style_id}"

    if cell.data_type == "s":
        attrs["t"] = "inlineStr"
    elif cell.data_type != "f":
        attrs["t"] = cell.data_type

    value = cell._value

    if cell.data_type == "d":
        if hasattr(value, "tzinfo") and value.tzinfo is not None:
            # raise TypeError(
            #     "Excel does not support timezones in datetimes. "
            #     "The tzinfo in the datetime/time object must be set to None."
            # )
            value = value.replace(tzinfo=None)

        if cell.parent.parent.iso_dates and not isinstance(value, timedelta):
            value = to_ISO8601(value)
        else:
            attrs["t"] = "n"
            value = to_excel(value, cell.parent.parent.epoch)

    if cell.hyperlink:
        cell.parent._hyperlinks.append(cell.hyperlink)

    return value, attrs
