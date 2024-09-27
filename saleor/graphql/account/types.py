import uuid
from functools import partial
from typing import Optional, cast

import graphene
from django.contrib.auth import get_user_model
from graphene import relay
from graphql import GraphQLError
from promise import Promise

from saleor.graphql.account.sorters import InvitationsSortingInput
from saleor.graphql.core.filters import MetadataFilterBase, ObjectTypeFilter
from saleor.graphql.core.types.common import DateTimeRangeInput
from saleor.graphql.core.types.filter_input import FilterInputObjectType
from saleor.graphql.utils.filters import filter_range_field

from ...account import models
from ...checkout.utils import get_user_checkout
from ...core.exceptions import PermissionDenied
from ...graphql.meta.inputs import MetadataInput
from ...payment.interface import ListStoredPaymentMethodsRequestData
from ...permission.auth_filters import AuthorizationFilters
from ...permission.enums import AccountPermissions, AppPermission
from ...thumbnail.utils import (
    get_image_or_proxy_url,
    get_thumbnail_format,
    get_thumbnail_size,
)
from ..account.utils import check_is_owner_or_has_one_of_perms
from ..app.dataloaders import AppByIdLoader, get_app_promise
from ..app.types import App
from ..channel.dataloaders import ChannelBySlugLoader
from ..channel.types import Channel
from ..checkout.dataloaders import CheckoutByUserAndChannelLoader, CheckoutByUserLoader
from ..checkout.types import Checkout, CheckoutCountableConnection
from ..core import ResolveInfo
from ..core.connection import (
    CountableConnection,
    create_connection_slice,
    filter_connection_queryset,
)
from ..core.context import get_database_connection_name
from ..core.descriptions import (
    ADDED_IN_38,
    ADDED_IN_310,
    ADDED_IN_314,
    ADDED_IN_315,
    DEPRECATED_IN_3X_FIELD,
    PREVIEW_FEATURE,
)
from ..core.doc_category import DOC_CATEGORY_USERS
from ..core.enums import LanguageCodeEnum
from ..core.federation import federated_entity, resolve_federation_references
from ..core.fields import ConnectionField, FilterConnectionField, PermissionsField
from ..core.scalars import UUID
from ..core.tracing import traced_resolver
from ..core.types import (
    BaseInputObjectType,
    BaseObjectType,
    CountryDisplay,
    Image,
    ModelObjectType,
    NonNullList,
    Permission,
    ThumbnailField,
)
from ..core.utils import from_global_id_or_error, str_to_enum, to_global_id_or_none
from ..giftcard.dataloaders import GiftCardsByUserLoader
from ..meta.types import ObjectWithMetadata
from ..order.dataloaders import OrderLineByIdLoader
from ..order.resolvers import resolve_invitations, resolve_orders
from ..payment.types import StoredPaymentMethod
from ..plugins.dataloaders import get_plugin_manager_promise
from ..utils import format_permissions_for_display, get_user_or_app_from_context
from .dataloaders import (
    AccessibleChannelsByGroupIdLoader,
    AccessibleChannelsByUserIdLoader,
    CustomerEventsByUserLoader,
    RestrictedChannelAccessByUserIdLoader,
    ThumbnailByUserIdSizeAndFormatLoader,
)
from .enums import CountryCodeEnum, CustomerEventsEnum
from .utils import can_user_manage_group, get_groups_which_user_can_manage


def filter_created_at(qs, _, value):
    if value:
        return filter_range_field(qs, "invitations__created_at", value)
    return qs


def filter_expired_at(qs, _, value):
    if value:
        return filter_range_field(qs, "invitations__expired_at", value)
    return qs


class InvitationFilter(MetadataFilterBase):
    created_at = ObjectTypeFilter(
        input_class=DateTimeRangeInput, method=filter_created_at
    )
    expired_at = ObjectTypeFilter(
        input_class=DateTimeRangeInput, method=filter_expired_at
    )


class InvitationFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_USERS
        filterset_class = InvitationFilter


class AddressInput(BaseInputObjectType):
    first_name = graphene.String(description="Given name.")
    last_name = graphene.String(description="Family name.")
    company_name = graphene.String(description="Company or organization.")
    street_address_1 = graphene.String(description="Address.")
    street_address_2 = graphene.String(description="Address.")
    city = graphene.String(description="City.")
    city_area = graphene.String(description="District.")
    postal_code = graphene.String(description="Postal code.")
    country = CountryCodeEnum(description="Country.")
    country_area = graphene.String(description="State or province.")
    phone = graphene.String(
        description=(
            "Phone number.\n\n"
            "Phone numbers are validated with Google's "
            "[libphonenumber](https://github.com/google/libphonenumber) library."
        )
    )

    metadata = graphene.List(
        graphene.NonNull(MetadataInput),
        description="Address public metadata." + ADDED_IN_315,
        required=False,
    )


@federated_entity("id")
class Address(ModelObjectType[models.Address]):
    id = graphene.GlobalID(required=True, description="The ID of the address.")
    first_name = graphene.String(
        required=True, description="The given name of the address."
    )
    last_name = graphene.String(
        required=True, description="The family name of the address."
    )
    company_name = graphene.String(
        required=True, description="Company or organization name."
    )
    street_address_1 = graphene.String(
        required=True, description="The first line of the address."
    )
    street_address_2 = graphene.String(
        required=True, description="The second line of the address."
    )
    city = graphene.String(required=True, description="The city of the address.")
    city_area = graphene.String(
        required=True, description="The district of the address."
    )
    postal_code = graphene.String(
        required=True, description="The postal code of the address."
    )
    country = graphene.Field(
        CountryDisplay, required=True, description="The country of the address."
    )
    country_area = graphene.String(
        required=True, description="The country area of the address."
    )
    phone = graphene.String(description="The phone number assigned the address.")
    is_default_shipping_address = graphene.Boolean(
        required=False, description="Address is user's default shipping address."
    )
    is_default_billing_address = graphene.Boolean(
        required=False, description="Address is user's default billing address."
    )

    class Meta:
        description = "Represents user address data."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Address
        metadata_since = ADDED_IN_310

    @staticmethod
    def resolve_country(root: models.Address, _info: ResolveInfo):
        return CountryDisplay(code=root.country.code, country=root.country.name)

    @staticmethod
    def resolve_is_default_shipping_address(root: models.Address, _info: ResolveInfo):
        """Look if the address is the default shipping address of the user.

        This field is added through annotation when using the
        `resolve_addresses` resolver. It's invalid for
        `resolve_default_shipping_address` and
        `resolve_default_billing_address`
        """
        if not hasattr(root, "user_default_shipping_address_pk"):
            return None

        user_default_shipping_address_pk = getattr(
            root, "user_default_shipping_address_pk"
        )
        if user_default_shipping_address_pk == root.pk:
            return True
        return False

    @staticmethod
    def resolve_is_default_billing_address(root: models.Address, _info: ResolveInfo):
        """Look if the address is the default billing address of the user.

        This field is added through annotation when using the
        `resolve_addresses` resolver. It's invalid for
        `resolve_default_shipping_address` and
        `resolve_default_billing_address`
        """
        if not hasattr(root, "user_default_billing_address_pk"):
            return None

        user_default_billing_address_pk = getattr(
            root, "user_default_billing_address_pk"
        )
        if user_default_billing_address_pk == root.pk:
            return True
        return False

    @staticmethod
    def __resolve_references(roots: list["Address"], info: ResolveInfo):
        from .resolvers import resolve_addresses

        app = get_app_promise(info.context).get()

        root_ids = [root.id for root in roots]
        addresses = {
            address.id: address for address in resolve_addresses(info, root_ids, app)
        }

        result = []
        for root_id in root_ids:
            _, root_id = from_global_id_or_error(root_id, Address)
            result.append(addresses.get(int(root_id)))

        return result


class CustomerEvent(ModelObjectType[models.CustomerEvent]):
    id = graphene.GlobalID(required=True, description="The ID of the customer event.")
    date = graphene.types.datetime.DateTime(
        description="Date when event happened at in ISO 8601 format."
    )
    type = CustomerEventsEnum(description="Customer event type.")
    user = graphene.Field(lambda: User, description="User who performed the action.")
    app = graphene.Field(App, description="App that performed the action.")
    message = graphene.String(description="Content of the event.")
    count = graphene.Int(description="Number of objects concerned by the event.")
    order = graphene.Field(
        "saleor.graphql.order.types.Order", description="The concerned order."
    )
    order_line = graphene.Field(
        "saleor.graphql.order.types.OrderLine", description="The concerned order line."
    )

    class Meta:
        description = "History log of the customer."
        interfaces = [relay.Node]
        model = models.CustomerEvent
        doc_category = DOC_CATEGORY_USERS

    @staticmethod
    def resolve_user(root: models.CustomerEvent, info: ResolveInfo):
        user = info.context.user
        user = cast(User, user)
        if (
            user == root.user
            or user.has_perm(AccountPermissions.MANAGE_USERS)
            or user.has_perm(AccountPermissions.MANAGE_STAFF)
        ):
            return root.user
        raise PermissionDenied(
            permissions=[
                AccountPermissions.MANAGE_STAFF,
                AccountPermissions.MANAGE_USERS,
                AuthorizationFilters.OWNER,
            ]
        )

    @staticmethod
    def resolve_app(root: models.CustomerEvent, info: ResolveInfo):
        requestor = get_user_or_app_from_context(info.context)
        check_is_owner_or_has_one_of_perms(
            requestor, root.user, AppPermission.MANAGE_APPS
        )
        return AppByIdLoader(info.context).load(root.app_id) if root.app_id else None

    @staticmethod
    def resolve_message(root: models.CustomerEvent, _info: ResolveInfo):
        return root.parameters.get("message", None)

    @staticmethod
    def resolve_count(root: models.CustomerEvent, _info: ResolveInfo):
        return root.parameters.get("count", None)

    @staticmethod
    def resolve_order_line(root: models.CustomerEvent, info: ResolveInfo):
        if "order_line_pk" in root.parameters:
            return OrderLineByIdLoader(info.context).load(
                uuid.UUID(root.parameters["order_line_pk"])
            )
        return None


class UserPermission(Permission):
    source_permission_groups = NonNullList(
        "saleor.graphql.account.types.Group",
        description="List of user permission groups which contains this permission.",
        user_id=graphene.Argument(
            graphene.ID,
            description="ID of user whose groups should be returned.",
            required=True,
        ),
        required=False,
    )

    class Meta:
        description = "Represents user's permissions."
        doc_category = DOC_CATEGORY_USERS

    @staticmethod
    @traced_resolver
    def resolve_source_permission_groups(root: Permission, info: ResolveInfo, user_id):
        _type, user_id = from_global_id_or_error(user_id, only_type="User")
        groups = models.Group.objects.using(
            get_database_connection_name(info.context)
        ).filter(user__pk=user_id, permissions__name=root.name)
        return groups


@federated_entity("id")
class Invitation(ModelObjectType[models.Invitation]):
    id = graphene.GlobalID(required=True, description="The Id of the invitation")
    created_at = graphene.DateTime(description="Creation of the current invitation")
    expired_at = graphene.DateTime(description="Expiration of the current invitation")

    class Meta:
        description = "Represents invitation data."
        interfaces = [relay.Node]
        model = models.Invitation
        doc_category = DOC_CATEGORY_USERS


class InvitationCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_USERS
        node = Invitation


@federated_entity("id")
@federated_entity("email")
class User(ModelObjectType[models.User]):
    from ..order.filters import OrderFilterInput
    from ..order.sorters import OrderSortingInput

    id = graphene.GlobalID(required=True, description="The ID of the user.")
    email = graphene.String(required=True, description="The email address of the user.")
    account = graphene.String(
        required=True, description="The name of the user IODC account."
    )
    user_type = graphene.String(
        required=True, description="The type of the user. Defined by the OIDC provider"
    )
    balance = graphene.Float(required=True, description="The balance of the user.")
    code = graphene.String(required=True, description="The code of a user.")
    continuous = graphene.Int(
        required=True, description="The continous login days of the user."
    )
    first_name = graphene.String(
        required=True, description="The given name of the address."
    )
    last_name = graphene.String(
        required=True, description="The family name of the address."
    )
    is_staff = graphene.Boolean(
        required=True, description="Determine if the user is a staff admin."
    )
    is_active = graphene.Boolean(
        required=True, description="Determine if the user is active."
    )
    is_confirmed = graphene.Boolean(
        required=True,
        description="Determines if user has confirmed email." + ADDED_IN_315,
    )
    addresses = NonNullList(
        Address, description="List of all user's addresses.", required=True
    )
    checkout = graphene.Field(
        Checkout,
        description="Returns the last open checkout of this user.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} "
            "Use the `checkoutTokens` field to fetch the user checkouts."
        ),
    )
    checkout_tokens = NonNullList(
        UUID,
        description="Returns the checkout UUID's assigned to this user.",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        deprecation_reason=(f"{DEPRECATED_IN_3X_FIELD} Use `checkoutIds` instead."),
    )
    checkout_ids = NonNullList(
        graphene.ID,
        description="Returns the checkout ID's assigned to this user.",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
    )
    checkouts = ConnectionField(
        CheckoutCountableConnection,
        description="Returns checkouts assigned to this user." + ADDED_IN_38,
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
    )
    gift_cards = ConnectionField(
        "saleor.graphql.giftcard.types.GiftCardCountableConnection",
        description="List of the user gift cards.",
    )
    note = PermissionsField(
        graphene.String,
        description="A note about the customer.",
        permissions=[AccountPermissions.MANAGE_USERS, AccountPermissions.MANAGE_STAFF],
    )
    orders = FilterConnectionField(
        "saleor.graphql.order.types.OrderCountableConnection",
        sort_by=OrderSortingInput(description="Sort orders."),
        filter=OrderFilterInput(description="Filtering options for orders."),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description=(
            "List of user's orders. Requires one of the following permissions: "
            f"{AccountPermissions.MANAGE_STAFF.name}, "
            f"{AuthorizationFilters.OWNER.name}."
        ),
    )
    user_permissions = NonNullList(
        UserPermission, description="List of user's permissions."
    )
    permission_groups = NonNullList(
        "saleor.graphql.account.types.Group",
        description="List of user's permission groups.",
    )
    editable_groups = NonNullList(
        "saleor.graphql.account.types.Group",
        description="List of user's permission groups which user can manage.",
    )
    accessible_channels = NonNullList(
        Channel,
        description=(
            "List of channels the user has access to. The sum of channels from all "
            "user groups. If at least one group has `restrictedAccessToChannels` "
            "set to False - all channels are returned." + ADDED_IN_314 + PREVIEW_FEATURE
        ),
    )
    restricted_access_to_channels = graphene.Boolean(
        required=True,
        description=(
            "Determine if user have restricted access to channels. False if at least "
            "one user group has `restrictedAccessToChannels` set to False."
        )
        + ADDED_IN_314
        + PREVIEW_FEATURE,
    )
    avatar = ThumbnailField(description="The avatar of the user.")
    events = PermissionsField(
        NonNullList(CustomerEvent),
        description="List of events associated with the user.",
        permissions=[AccountPermissions.MANAGE_USERS, AccountPermissions.MANAGE_STAFF],
    )
    invitations = FilterConnectionField(
        InvitationCountableConnection,
        sort_by=InvitationsSortingInput(description="Sort invitations."),
        filter=InvitationFilterInput(description="Filtering options for invitations."),
        description=(
            "List of user's invitations. Requires one of the following permissions: "
            f"{AuthorizationFilters.AUTHENTICATED_USER}."
        ),
    )
    stored_payment_sources = NonNullList(
        "saleor.graphql.payment.types.PaymentSource",
        description=(
            "List of stored payment sources. The field returns a list of payment "
            "sources stored for payment plugins."
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
    )
    language_code = graphene.Field(
        LanguageCodeEnum, description="User language code.", required=True
    )
    default_shipping_address = graphene.Field(
        Address, description="The default shipping address of the user."
    )
    default_billing_address = graphene.Field(
        Address, description="The default billing address of the user."
    )
    external_reference = graphene.String(
        description=f"External ID of this user. {ADDED_IN_310}", required=False
    )

    last_login = graphene.DateTime(
        description="The date when the user last time log in to the system."
    )
    date_joined = graphene.DateTime(
        required=True, description="The data when the user create account."
    )
    updated_at = graphene.DateTime(
        required=True,
        description="The data when the user last update the account information.",
    )
    stored_payment_methods = NonNullList(
        StoredPaymentMethod,
        description=(
            "Returns a list of user's stored payment methods that can be used in "
            "provided channel. The field returns a list of stored payment methods by "
            "payment apps. When `amount` is not provided, 0 will be used as default "
            "value." + ADDED_IN_315 + PREVIEW_FEATURE
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned.",
            required=True,
        ),
    )

    class Meta:
        description = "Represents user data."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = get_user_model()
        doc_category = DOC_CATEGORY_USERS

    @staticmethod
    def resolve_addresses(root: models.User, _info: ResolveInfo):
        return root.addresses.annotate_default(root).all()  # type: ignore[attr-defined] # mypy does not properly recognize the related manager # noqa: E501

    @staticmethod
    def resolve_checkout(root: models.User, _info: ResolveInfo):
        return get_user_checkout(root)

    @staticmethod
    @traced_resolver
    def resolve_checkout_tokens(root: models.User, info: ResolveInfo, channel=None):
        def return_checkout_tokens(checkouts):
            if not checkouts:
                return []
            checkout_global_ids = []
            for checkout in checkouts:
                checkout_global_ids.append(checkout.token)
            return checkout_global_ids

        if not channel:
            return (
                CheckoutByUserLoader(info.context)
                .load(root.id)
                .then(return_checkout_tokens)
            )
        return (
            CheckoutByUserAndChannelLoader(info.context)
            .load((root.id, channel))
            .then(return_checkout_tokens)
        )

    @staticmethod
    @traced_resolver
    def resolve_checkout_ids(root: models.User, info: ResolveInfo, channel=None):
        def return_checkout_ids(checkouts):
            if not checkouts:
                return []
            checkout_global_ids = []
            for checkout in checkouts:
                checkout_global_ids.append(to_global_id_or_none(checkout))
            return checkout_global_ids

        if not channel:
            return (
                CheckoutByUserLoader(info.context)
                .load(root.id)
                .then(return_checkout_ids)
            )
        return (
            CheckoutByUserAndChannelLoader(info.context)
            .load((root.id, channel))
            .then(return_checkout_ids)
        )

    @staticmethod
    def resolve_checkouts(root: models.User, info: ResolveInfo, **kwargs):
        def _resolve_checkouts(checkouts):
            return create_connection_slice(
                checkouts, info, kwargs, CheckoutCountableConnection
            )

        if channel := kwargs.get("channel"):
            return (
                CheckoutByUserAndChannelLoader(info.context)
                .load((root.id, channel))
                .then(_resolve_checkouts)
            )
        return CheckoutByUserLoader(info.context).load(root.id).then(_resolve_checkouts)

    @staticmethod
    def resolve_gift_cards(root: models.User, info: ResolveInfo, **kwargs):
        from ..giftcard.types import GiftCardCountableConnection

        def _resolve_gift_cards(gift_cards):
            return create_connection_slice(
                gift_cards, info, kwargs, GiftCardCountableConnection
            )

        return (
            GiftCardsByUserLoader(info.context).load(root.id).then(_resolve_gift_cards)
        )

    @staticmethod
    def resolve_invitations(root: models.User, info: ResolveInfo, **kwargs):
        qs = resolve_invitations(info)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, InvitationCountableConnection)

    @staticmethod
    def resolve_user_permissions(root: models.User, _info: ResolveInfo):
        from .resolvers import resolve_permissions

        return resolve_permissions(root)

    @staticmethod
    def resolve_permission_groups(root: models.User, info: ResolveInfo):
        return root.groups.using(get_database_connection_name(info.context)).all()

    @staticmethod
    def resolve_editable_groups(root: models.User, _info: ResolveInfo):
        return get_groups_which_user_can_manage(root)

    @staticmethod
    def resolve_accessible_channels(root: models.Group, info: ResolveInfo):
        # Sum of channels from all user groups. If at least one group has
        # `restrictedAccessToChannels` set to False - all channels are returned
        return AccessibleChannelsByUserIdLoader(info.context).load(root.id)

    @staticmethod
    def resolve_restricted_access_to_channels(root: models.Group, info: ResolveInfo):
        # Returns False if at least one user group has `restrictedAccessToChannels`
        # set to False
        return RestrictedChannelAccessByUserIdLoader(info.context).load(root.id)

    @staticmethod
    def resolve_note(root: models.User, _info: ResolveInfo):
        return root.note

    @staticmethod
    def resolve_last_login(root: models.User, _info: ResolveInfo):
        return root.last_login

    @staticmethod
    def resolve_continous(root: models.User, _info: ResolveInfo):
        return root.continuous

    @staticmethod
    def resolve_events(root: models.User, info: ResolveInfo):
        return CustomerEventsByUserLoader(info.context).load(root.id)

    @staticmethod
    def resolve_orders(root: models.User, info: ResolveInfo, *, channel=None, **kwargs):
        from ..order.types import OrderCountableConnection

        user_or_app = get_user_or_app_from_context(info.context)
        if not user_or_app or (
            root != user_or_app
            and not user_or_app.has_perm(OrderPermissions.MANAGE_ORDERS)
        ):
            raise PermissionDenied(
                permissions=[
                    AuthorizationFilters.OWNER,
                    OrderPermissions.MANAGE_ORDERS,
                ]
            )
        requester = user_or_app

        from ..core.connection import filter_connection_queryset
        from ..order.schema import (
            OrderCountableConnection,
            OrderSortField,
            search_string_in_kwargs,
            sort_field_from_kwargs,
        )

        if sort_field_from_kwargs(kwargs) == OrderSortField.RANK:
            # sort by RANK can be used only with search filter
            if not search_string_in_kwargs(kwargs):
                raise GraphQLError(
                    "Sorting by RANK is available only when using a search filter."
                )
        if search_string_in_kwargs(kwargs) and not sort_field_from_kwargs(kwargs):
            # default to sorting by RANK if search is used
            # and no explicit sorting is requested
            product_type = info.schema.get_type("OrderSortingInput")
            kwargs["sort_by"] = product_type.create_container(
                {"direction": "-", "field": ["search_rank", "id"]}
            )

        database_connection_name = get_database_connection_name(info.context)
        qs = models.Order.objects.using(database_connection_name).non_draft()
        qs = qs.filter(user_id=root.id)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, OrderCountableConnection)

    @staticmethod
    def resolve_avatar(
        root: models.User,
        info: ResolveInfo,
        size: Optional[int] = None,
        format: Optional[str] = None,
    ):
        if not root.avatar:
            return

        if size == 0:
            return Image(url=root.avatar.url, alt=None)

        format = get_thumbnail_format(format)
        selected_size = get_thumbnail_size(size)

        def _resolve_avatar(thumbnail):
            url = get_image_or_proxy_url(
                thumbnail, str(root.uuid), "User", selected_size, format
            )
            return Image(url=url, alt=None)

        return (
            ThumbnailByUserIdSizeAndFormatLoader(info.context)
            .load((root.id, selected_size, format))
            .then(_resolve_avatar)
        )

    @staticmethod
    def resolve_stored_payment_sources(
        root: models.User, info: ResolveInfo, channel=None
    ):
        from .resolvers import resolve_payment_sources

        if root == info.context.user:
            return get_plugin_manager_promise(info.context).then(
                partial(resolve_payment_sources, info, root, channel_slug=channel)
            )

        raise PermissionDenied(permissions=[AuthorizationFilters.OWNER])

    @staticmethod
    def resolve_language_code(root, _info: ResolveInfo):
        return LanguageCodeEnum[str_to_enum(root.language_code)]

    @staticmethod
    def __resolve_references(roots: list["User"], info: ResolveInfo):
        from .resolvers import resolve_users

        ids = set()
        emails = set()
        for root in roots:
            if root.id is not None:
                ids.add(root.id)
            else:
                emails.add(root.email)

        users = list(resolve_users(info, ids=ids, emails=emails))
        users_by_id = {user.id: user for user in users}
        users_by_email = {user.email: user for user in users}

        results = []
        for root in roots:
            if root.id is not None:
                _, user_id = from_global_id_or_error(root.id, User)
                results.append(users_by_id.get(int(user_id)))
            else:
                results.append(users_by_email.get(root.email))
        return results

    @staticmethod
    def resolve_stored_payment_methods(
        root: models.User,
        info: ResolveInfo,
        channel: str,
    ):
        requestor = get_user_or_app_from_context(info.context)
        if not requestor or requestor.id != root.id:
            return []

        def get_stored_payment_methods(data):
            channel_obj, manager = data
            request_data = ListStoredPaymentMethodsRequestData(
                user=root,
                channel=channel_obj,
            )
            return manager.list_stored_payment_methods(request_data)

        return Promise.all(
            [
                ChannelBySlugLoader(info.context).load(channel),
                get_plugin_manager_promise(info.context),
            ]
        ).then(get_stored_payment_methods)


class UserCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_USERS
        node = User


class ChoiceValue(graphene.ObjectType):
    raw = graphene.String(description="The raw name of the choice.")
    verbose = graphene.String(description="The verbose name of the choice.")


FORMAT_FILED_DESCRIPTION = (
    "\n\nMany fields in the JSON refer to address fields by one-letter "
    "abbreviations. These are defined as follows:\n\n"
    "- `N`: Name\n"
    "- `O`: Organisation\n"
    "- `A`: Street Address Line(s)\n"
    "- `D`: Dependent locality (may be an inner-city district or a suburb)\n"
    "- `C`: City or Locality\n"
    "- `S`: Administrative area such as a state, province, island etc\n"
    "- `Z`: Zip or postal code\n"
    "- `X`: Sorting code\n\n"
    "[Click here for more information.](https://github.com/google/libaddressinput/wiki/AddressValidationMetadata)"
)


class AddressValidationData(BaseObjectType):
    country_code = graphene.String(
        required=True, description="The country code of the address validation rule."
    )
    country_name = graphene.String(
        required=True, description="The country name of the address validation rule."
    )
    address_format = graphene.String(
        required=True,
        description=(
            "The address format of the address validation rule."
            + FORMAT_FILED_DESCRIPTION
        ),
    )
    address_latin_format = graphene.String(
        required=True,
        description=(
            "The latin address format of the address validation rule."
            + FORMAT_FILED_DESCRIPTION
        ),
    )
    allowed_fields = NonNullList(
        graphene.String,
        required=True,
        description="The allowed fields to use in address.",
    )
    required_fields = NonNullList(
        graphene.String,
        required=True,
        description="The required fields to create a valid address.",
    )
    upper_fields = NonNullList(
        graphene.String,
        required=True,
        description=(
            "The list of fields that should be in upper case for address "
            "validation rule."
        ),
    )
    country_area_type = graphene.String(
        required=True,
        description=(
            "The formal name of the county area of the address validation rule."
        ),
    )
    country_area_choices = NonNullList(
        ChoiceValue,
        required=True,
        description=(
            "The available choices for the country area of the address validation rule."
        ),
    )
    city_type = graphene.String(
        required=True,
        description="The formal name of the city of the address validation rule.",
    )
    city_choices = NonNullList(
        ChoiceValue,
        required=True,
        description=(
            "The available choices for the city of the address validation rule."
        ),
    )
    city_area_type = graphene.String(
        required=True,
        description="The formal name of the city area of the address validation rule.",
    )
    city_area_choices = NonNullList(
        ChoiceValue,
        required=True,
        description=(
            "The available choices for the city area of the address validation rule."
        ),
    )
    postal_code_type = graphene.String(
        required=True,
        description=(
            "The formal name of the postal code of the address validation rule."
        ),
    )
    postal_code_matchers = NonNullList(
        graphene.String,
        required=True,
        description=("The regular expression for postal code validation."),
    )
    postal_code_examples = NonNullList(
        graphene.String,
        required=True,
        description="The example postal code of the address validation rule.",
    )
    postal_code_prefix = graphene.String(
        required=True,
        description="The postal code prefix of the address validation rule.",
    )

    class Meta:
        description = "Represents address validation rules for a country."
        doc_category = DOC_CATEGORY_USERS


class StaffNotificationRecipient(graphene.ObjectType):
    id = graphene.ID(
        required=True, description="The ID of the staff notification recipient."
    )
    user = graphene.Field(
        User,
        description="Returns a user subscribed to email notifications.",
        required=False,
    )
    email = graphene.String(
        description=(
            "Returns email address of a user subscribed to email notifications."
        ),
        required=False,
    )
    active = graphene.Boolean(description="Determines if a notification active.")

    class Meta:
        description = (
            "Represents a recipient of email notifications send by Saleor, "
            "such as notifications about new orders. Notifications can be "
            "assigned to staff users or arbitrary email addresses."
        )
        interfaces = [relay.Node]
        model = models.StaffNotificationRecipient

    @staticmethod
    def get_node(info: ResolveInfo, id):
        try:
            return models.StaffNotificationRecipient.objects.using(
                get_database_connection_name(info.context)
            ).get(pk=id)
        except models.StaffNotificationRecipient.DoesNotExist:
            return None

    @staticmethod
    def resolve_user(root: models.StaffNotificationRecipient, info: ResolveInfo):
        user = info.context.user
        user = cast(models.User, user)
        if user == root.user or user.has_perm(AccountPermissions.MANAGE_STAFF):
            return root.user
        raise PermissionDenied(
            permissions=[AccountPermissions.MANAGE_STAFF, AuthorizationFilters.OWNER]
        )

    @staticmethod
    def resolve_email(root: models.StaffNotificationRecipient, _info: ResolveInfo):
        return root.get_email()


@federated_entity("id")
class Group(ModelObjectType[models.Group]):
    id = graphene.GlobalID(required=True, description="The ID of the group.")
    name = graphene.String(required=True, description="The name of the group.")
    users = PermissionsField(
        NonNullList(User),
        description="List of group users",
        permissions=[
            AccountPermissions.MANAGE_STAFF,
        ],
    )
    permissions = NonNullList(Permission, description="List of group permissions")
    user_can_manage = graphene.Boolean(
        required=True,
        description=(
            "True, if the currently authenticated user has rights to manage a group."
        ),
    )
    accessible_channels = NonNullList(
        Channel,
        description="List of channels the group has access to."
        + ADDED_IN_314
        + PREVIEW_FEATURE,
    )
    restricted_access_to_channels = graphene.Boolean(
        required=True,
        description="Determine if the group have restricted access to channels."
        + ADDED_IN_314
        + PREVIEW_FEATURE,
    )

    class Meta:
        description = "Represents permission group data."
        interfaces = [relay.Node]
        model = models.Group
        doc_category = DOC_CATEGORY_USERS

    @staticmethod
    def resolve_users(root: models.Group, _info: ResolveInfo):
        return root.user_set.all()

    @staticmethod
    def resolve_permissions(root: models.Group, _info: ResolveInfo):
        permissions = root.permissions.prefetch_related("content_type").order_by(
            "codename"
        )
        return format_permissions_for_display(permissions)

    @staticmethod
    def resolve_user_can_manage(root: models.Group, info: ResolveInfo) -> bool:
        user = info.context.user
        if not user:
            return False
        return can_user_manage_group(info, user, root)

    @staticmethod
    def resolve_accessible_channels(root: models.Group, info: ResolveInfo):
        return AccessibleChannelsByGroupIdLoader(info.context).load(root.id)

    @staticmethod
    def __resolve_references(roots: list["Group"], info: ResolveInfo):
        from .resolvers import resolve_permission_groups

        requestor = get_user_or_app_from_context(info.context)
        if not requestor or not requestor.has_perm(AccountPermissions.MANAGE_STAFF):
            qs = models.Group.objects.none()
        else:
            qs = resolve_permission_groups(info)

        return resolve_federation_references(Group, roots, qs)


class GroupCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_USERS
        node = Group
