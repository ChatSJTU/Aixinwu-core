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
from ..core.types.common import DateRangeInput, NonNullList
from .resolvers import (
    resolve_customers_registered,
    resolve_donation_reports,
    resolve_order_reports,
)
from .types import BaseReport, Granularity


class ReportQueries(BaseObjectType):
    orderReports = PermissionsField(
        NonNullList(
            BaseReport,
        ),
        date=DateRangeInput(required=True),
        granularity=Granularity(required=True),
        description="Order Report",
        doc_category=DOC_CATEGORY_REPORTS,
        permissions=[OrderPermissions.MANAGE_ORDERS],
    )

    customerReports = PermissionsField(
        NonNullList(graphene.Int),
        date=DateRangeInput(required=True),
        granularity=Granularity(required=True),
        permissions=[AccountPermissions.MANAGE_USERS],
    )

    donationReports = PermissionsField(
        NonNullList(BaseReport),
        date=DateRangeInput(required=True),
        granularity=Granularity(required=True),
        description="Donation Report",
        doc_category=DOC_CATEGORY_REPORTS,
        permissions=[DonationPermissions.MANAGE_DONATIONS],
    )

    @staticmethod
    def resolve_orderReports(
        _root, info: ResolveInfo, *, date: DateRangeInput, granularity: Granularity
    ):
        return resolve_order_reports(info, date, granularity)

    @staticmethod
    def resolve_customerReports(
        _root, info: ResolveInfo, *, date: DateRangeInput, granularity: Granularity
    ):
        return resolve_customers_registered(info, date, granularity)

    @staticmethod
    def resolve_donationReports(
        _root, info: ResolveInfo, *, date: DateRangeInput, granularity: Granularity
    ):
        return resolve_donation_reports(info, date, granularity)
