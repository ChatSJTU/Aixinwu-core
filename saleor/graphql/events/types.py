import graphene
from ..core import ResolveInfo
from ..core.connection import CountableConnection
from ..core.doc_category import DOC_CATEGORY_EVENTS
from ..core.types.model import ModelObjectType
from ...account import models


class BalanceEvent(ModelObjectType[models.BalanceEvent]):
    id = graphene.ID(required=True, description="The ID of the balance event.")
    account = graphene.String(description="User account of a balance event.")
    balance = graphene.Float(description="Balance of a balance event.")
    type = graphene.String(description="Type of a balance event.")
    name = graphene.String(description="User name of a balance event.")
    code = graphene.String(description="Code of the customer.")

    class Meta:
        description = "Represents balance events."
        interfaces = [graphene.relay.Node]
        model = models.BalanceEvent

    @staticmethod
    def resolve_id(root, info: ResolveInfo):
        return graphene.Node.to_global_id("BalanceEvent", root.pk)

    @staticmethod
    def resolve_balance(root, info: ResolveInfo):
        return root.balance

    @staticmethod
    def resolve_type(root, info: ResolveInfo):
        return root.type

    @staticmethod
    def resolve_account(root, info: ResolveInfo):
        return root.user.account

    @staticmethod
    def resolve_name(root, info: ResolveInfo):
        return root.user.first_name

    @staticmethod
    def resolve_code(root, info: ResolveInfo):
        return root.user.code


class BalanceEventCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_EVENTS
        node = BalanceEvent
