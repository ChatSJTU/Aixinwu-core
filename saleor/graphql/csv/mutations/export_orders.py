import graphene

from ....csv import ExportType
from ....csv import models as csv_models
from ....csv.events import export_started_event
from ....csv.tasks import export_orders_task
from ....permission.enums import OrderPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.types import BaseInputObjectType, ExportError, NonNullList
from ...core.utils import WebhookEventInfo
from ...order.filters import OrderFilterInput
from ...order.types import Order
from ..enums import ExportScope, FileTypeEnum, OrderFieldEnum
from .base_export import BaseExportMutation


class ExportOrdersInput(BaseInputObjectType):
    scope = ExportScope(
        description="Determine which orders should be exported.", required=True
    )
    filter = OrderFilterInput(
        description="Filtering options for orders.", required=False
    )
    ids = NonNullList(
        graphene.ID,
        description="List of orders IDs to export.",
        required=False,
    )
    fields = NonNullList(
        OrderFieldEnum,
        description="List of order fields witch should be exported.",
    )
    file_type = FileTypeEnum(description="Type of exported file.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class ExportOrders(BaseExportMutation):
    class Arguments:
        input = ExportOrdersInput(
            required=True, description="Fields required to export orders data."
        )

    class Meta:
        description = "Export orders to csv file."
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = ExportError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.NOTIFY_USER,
                description="A notification for the exported file.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.ORDER_EXPORT_COMPLETED,
                description="A notification for the exported file.",
            ),
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input
    ):
        scope = cls.get_scope(input, Order)
        fields = input["fields"]
        file_type = input["file_type"]

        app = get_app_promise(info.context).get()

        export_file = csv_models.ExportFile.objects.create(
            app=app, user=info.context.user, export_type=ExportType.ORDER
        )
        export_started_event(export_file=export_file, app=app, user=info.context.user)
        export_orders_task.delay(export_file.pk, scope, fields, file_type)

        export_file.refresh_from_db()
        return cls(export_file=export_file)
