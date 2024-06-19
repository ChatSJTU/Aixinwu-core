import graphene

from saleor.account.events import change_balance_event

from .....account import models
from .....account.search import prepare_user_search_document_value
from .....account.utils import (
    remove_the_oldest_user_address_if_address_limit_is_reached,
)
from .....core.tracing import traced_atomic_transaction
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....account.types import Address, AddressInput, User
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import ModelMutation
from ....core.types import AccountError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise


class BalanceUpdate(ModelMutation):
    user = graphene.Field(
        User, description="A user instance for which the address was created."
    )

    class Arguments:
        user_id = graphene.ID(
            description="ID of a user to create address for.", required=True
        )
        balance = graphene.Float(
            description="Fields required to create address.", required=True
        )

    class Meta:
        description = "Update user's balance."
        doc_category = DOC_CATEGORY_USERS
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"
        model = models.User
        object_type = User
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.ADDRESS_CREATED,
                description="A new address was created.",
            ),
        ]

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        user_id = data["user_id"]
        user = cls.get_node_or_error(info, user_id, field="user_id", only_type=User)
        balance = data["balance"]
        instance = user
        with traced_atomic_transaction():
            user.balance = balance
            user.save(update_fields=["balance"])
            cls.post_save_action(info, instance, data)
            response = cls.success_response(instance)
            response.user = user

        return response

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        change_balance_event(user=instance, balance=cleaned_input["balance"])
