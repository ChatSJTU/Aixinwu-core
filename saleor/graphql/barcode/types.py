import graphene

from ..core import ResolveInfo
from ...barcode import models
from ...graphql.core.doc_category import DOC_CATEGORY_BARCODES
from ..core.connection import CountableConnection
from ..core.types import ModelObjectType


class Barcode(ModelObjectType[models.Barcode]):
    id = graphene.ID(required=True, description="The ID of the barcode")
    created_at = graphene.DateTime(
        required=False, description="The date and time when the barcode is created."
    )
    used = graphene.Boolean(
        required=False, description="Whether the barcode is used or not."
    )
    number = graphene.Int(required=False, description="the number of the barcode")

    class Meta:
        description = "Represents barcode."
        interfaces = [graphene.relay.Node]
        model = models.Barcode

    @staticmethod
    def get_number(root: models.Barcode, info: ResolveInfo):
        return root.year_month * 100000 + root.sub


class BarcodeCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_BARCODES
        node = Barcode
