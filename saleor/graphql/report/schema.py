import graphene

from ...permission.enums import (
    AccountPermissions,
    DonationPermissions,
    OrderPermissions,
)
from ..core import ResolveInfo
from ..core.doc_category import DOC_CATEGORY_REPORTS
from ..core.fields import PermissionsField
from ..core.types.base import BaseObjectType
from ..core.types.common import DateTimeRangeInput
from .resolvers import (
    resolve_customers_registered,
    resolve_donation_report,
    resolve_order_report,
)
from .types import BaseReport


class ReportQueries(BaseObjectType):
    orderReport = PermissionsField(
        BaseReport,
        date=DateTimeRangeInput(required=True),
        description="Order Report",
        doc_category=DOC_CATEGORY_REPORTS,
        permissions=[OrderPermissions.MANAGE_ORDERS],
    )

    customerReport = PermissionsField(
        graphene.Int,
        date=DateTimeRangeInput(required=True),
        permissions=[AccountPermissions.MANAGE_USERS],
    )

    donationReport = PermissionsField(
        BaseReport,
        date=DateTimeRangeInput(required=True),
        description="Donation Report",
        doc_category=DOC_CATEGORY_REPORTS,
        permissions=[DonationPermissions.MANAGE_DONATIONS],
    )

    @staticmethod
    def resolve_orderReport(_root, info: ResolveInfo, *, date: DateTimeRangeInput):
        return resolve_order_report(info, date)

    @staticmethod
    def resolve_customerReport(_root, info: ResolveInfo, *, date: DateTimeRangeInput):
        return resolve_customers_registered(info, date)

    @staticmethod
    def resolve_donationReport(_root, info: ResolveInfo, *, date: DateTimeRangeInput):
        return resolve_donation_report(info, date)
