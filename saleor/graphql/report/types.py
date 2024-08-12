import graphene

from ..core.types.base import BaseObjectType


class BaseReport(BaseObjectType):
    collectionTotal = graphene.Int(
        description="The total collection in the current range.",
    )
    quantitiesTotal = graphene.Int(description="The items total in the range.")
    amountTotal = graphene.Float(description="The amount total in the range")
