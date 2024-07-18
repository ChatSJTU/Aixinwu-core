import graphene

from ...permission.enums import BarcodePermissions
from ..barcode.resolvers import resolve_barcodes
from ..core import ResolveInfo
from ..core.connection import (
    create_connection_slice,
    filter_connection_queryset,
)
from ..core.doc_category import DOC_CATEGORY_BARCODES
from ..core.fields import FilterConnectionField
from .filters import BarcodeFilterInput
from .sorters import BarcodeSortingInput
from .types import BarcodeCountableConnection


class BarcodeQueries(graphene.ObjectType):
    barcodes = FilterConnectionField(
        BarcodeCountableConnection,
        description="Donations made by the user or collected by users if requested by staff.",
        sort_by=BarcodeSortingInput(description="Sort orders."),
        filter=BarcodeFilterInput(description="Filtering options for orders."),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        doc_category=DOC_CATEGORY_BARCODES,
        permission=[BarcodePermissions.MANAGE_BARCODE],
    )

    @staticmethod
    def resolve_barcodes(_root, info: ResolveInfo, **kwargs):
        qs = resolve_barcodes(info)
        qs = filter_connection_queryset(qs, kwargs, info.context)
        return create_connection_slice(qs, info, kwargs, BarcodeCountableConnection)
