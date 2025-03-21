from collections import ChainMap

from . import OrderExportFields


def get_order_export_fields_and_headers(
    fields: list[str],
) -> tuple[list[str], list[str]]:
    """Get export fields from fields and prepare headers mapping.

    Based on given fields headers from export info, export fields set and
    headers mapping is prepared.
    """
    export_fields = ["order__id"]
    file_headers = ["id"]

    if not fields:
        return export_fields, file_headers

    fields_mapping = dict(
        ChainMap(*reversed(OrderExportFields.HEADERS_TO_FIELDS_MAPPING.values()))
    )

    for field in fields:
        lookup_field = fields_mapping[field]
        if lookup_field and lookup_field not in export_fields:
            export_fields.append(lookup_field)
            file_headers.append(field)

    return export_fields, file_headers
