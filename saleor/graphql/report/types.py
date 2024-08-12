import graphene
from dateutil.relativedelta import relativedelta

from ..core.types.base import BaseObjectType


class Granularity(graphene.Enum):
    DAILY = "TODAY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


def get_relative_delta(g: Granularity) -> relativedelta:
    if g == Granularity.DAILY:
        return relativedelta(days=1)
    elif g == Granularity.MONTHLY:
        return relativedelta(months=1)
    else:
        return relativedelta(years=1)


class BaseReport(BaseObjectType):
    collectionTotal = graphene.Int(
        description="The total collection in the current range.",
    )
    quantitiesTotal = graphene.Int(description="The items total in the range.")
    amountTotal = graphene.Float(description="The amount total in the range")
