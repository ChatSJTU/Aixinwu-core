from typing import cast

import graphene

from .....account import models
from .....permission.auth_filters import AuthorizationFilters
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import ModelDeleteMutation
from ....core.types.common import AccountError
from ....utils import get_user_or_app_from_context
from ...types import Invitation, User


class AccountInvitationDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the invitation code to delete."
        )

    class Meta:
        description = "Create a new address for the customer."
        doc_category = DOC_CATEGORY_USERS
        model = models.Invitation
        object_type = Invitation
        error_type_class = AccountError
        error_type_field = "account_errors"
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, external_reference=None, id=None
    ):
        user = get_user_or_app_from_context(info.context)
        user = cast(User, user)
        instance = cls.get_instance(
            info, external_reference=external_reference, id=id, user=user
        )

        cls.clean_instance(info, instance)
        db_id = instance.id
        instance.delete()

        instance.id = db_id
        return cls.success_response(instance)
