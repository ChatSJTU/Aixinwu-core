import graphene
from django.db import transaction

from ....barcode import models
from ....permission.enums import BarcodePermissions
from ...core import ResolveInfo
from ...core.context import get_database_connection_name
from ...core.doc_category import DOC_CATEGORY_BARCODES
from ...core.mutations import BaseMutation
from ...core.types.common import BarcodeError, NonNullList
from ..types import Barcode


class BarcodeBatchCreate(BaseMutation):
    barcodes = NonNullList(
        Barcode,
        required=True,
        description="Barcodes created",
    )

    class Arguments:
        count = graphene.Int(
            required=True,
        )

    class Meta:
        description = "Create barcodes."
        doc_category = DOC_CATEGORY_BARCODES
        permissions = (BarcodePermissions.MANAGE_BARCODE,)
        error_type_class = BarcodeError
        error_type_field = "barcode_errors"
        support_meta_field = False
        support_private_meta_field = False

    @classmethod
    def perform_mutation(cls, _root, _info: ResolveInfo, **data):
        count = data.pop("count")
        with transaction.atomic():
            barcodes = [
                models.Barcode.objects.using(
                    get_database_connection_name(_info.context)
                ).create()
                for _ in range(count)
            ]
            return BarcodeBatchCreate(barcodes=barcodes, errors=None)
