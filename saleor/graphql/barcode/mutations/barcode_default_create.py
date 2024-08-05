from typing import Tuple

import graphene

from saleor.graphql.core.context import get_database_connection_name

from ....barcode import models
from ..types import Barcode
from ....permission.enums import BarcodePermissions
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_BARCODES
from ...core.fields import BaseField
from ...core.mutations import BaseMutation
from ...core.types.common import BarcodeError


class BarcodeDefaultCreate(BaseMutation):
    barcode = BaseField(Barcode, required=True, description="The returned barcode")
    created = graphene.Boolean(
        required=True, description="Whether this is created or not."
    )

    used_before = graphene.Boolean(
        required=True, description="Whether this has been used before."
    )

    class Arguments:
        number = graphene.Int(required=True, description="The number of the barcode.")

    class Meta:
        description = "Creates or get barcode"
        doc_category = DOC_CATEGORY_BARCODES
        permissions = (BarcodePermissions.MANAGE_BARCODE,)
        error_type_class = BarcodeError
        error_type_field = "barcode_errors"
        support_meta_field = False
        support_private_meta_field = False

    @classmethod
    def perform_mutation(cls, _root, _info: ResolveInfo, **data):
        number = data.get("number", 0)
        year_month = number // 100000
        sub = number % 100000
        barcode, created = models.Barcode.objects.using(
            get_database_connection_name(_info.context)
        ).get_or_create(year_month=year_month, sub=sub)

        used_before = barcode.used

        if not barcode.used:
            barcode.used = True
            barcode.save()

        return BarcodeDefaultCreate(
            barcode=barcode, created=created, used_before=used_before, errors=None
        )
