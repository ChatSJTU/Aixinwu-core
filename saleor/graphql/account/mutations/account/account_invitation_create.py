from typing import cast

import graphene

from .....account import models
from .....permission.auth_filters import AuthorizationFilters
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import ModelMutation
from ....core.types.common import AccountError
from ....utils import get_user_or_app_from_context
from ...types import Invitation, User


class AccountInvitationCreate(ModelMutation):
    invitation = graphene.Field(Invitation, description="Invitation")

    class Meta:
        description = "Create a new invitation for the customer."
        doc_category = DOC_CATEGORY_USERS
        model = models.Invitation
        object_type = Invitation
        error_type_class = AccountError
        error_type_field = "account_errors"
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, *, input_cls=None):
        user = get_user_or_app_from_context(info.context)
        user = cast(User, user)
        return {"user": user}
