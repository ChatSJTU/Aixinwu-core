from decimal import Decimal
import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import requests
from authlib.jose import JWTClaims, jwt
from authlib.jose.errors import DecodeError, JoseError
from authlib.oidc.core import CodeIDToken
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db.models import QuerySet
from django.utils import timezone
from jwt import PyJWTError

from saleor.account.events import (
    consecutive_login_balance_event,
    first_login_balance_event,
)
from ...account.models import Group, User
from ...account.search import prepare_user_search_document_value
from ...account.utils import get_user_groups_permissions
from ...core.http_client import HTTPClient
from ...core.jwt import (
    JWT_ACCESS_TYPE,
    JWT_OWNER_FIELD,
    JWT_REFRESH_TYPE,
    PERMISSIONS_FIELD,
    jwt_decode,
    jwt_encode,
    jwt_user_payload,
)
from ...graphql.account.mutations.authentication.utils import (
    _does_token_match,
    _get_new_csrf_token,
)
from ...order.utils import match_orders_with_new_user
from ...permission.enums import get_permission_names, get_permissions_from_codenames
from ...permission.models import Permission
from ...site.models import Site, SiteStatistics
from ..error_codes import PluginErrorCode
from ..models import PluginConfiguration
from . import PLUGIN_ID
from .const import SALEOR_STAFF_PERMISSION
from .exceptions import AuthenticationError

if TYPE_CHECKING:
    from .dataclasses import OpenIDConnectConfig

JWKS_KEY = "oauth_jwks"
JWKS_CACHE_TIME = 60 * 60  # 1 hour
USER_INFO_DEFAULT_CACHE_TIME = 60 * 60  # 1 hour

OIDC_DEFAULT_CACHE_TIME = 60 * 60  # 1 hour


OAUTH_TOKEN_REFRESH_FIELD = "oauth_refresh_token"
CSRF_FIELD = "csrf_token"


logger = logging.getLogger(__name__)


def fetch_jwks(jwks_url) -> Optional[dict]:
    """Fetch JSON Web Key Sets from a provider.

    Fetched keys will be stored in the cache to the reduced amount of possible
    requests.
    :raises AuthenticationError
    """
    response = None
    try:
        response = HTTPClient.send_request("GET", jwks_url, allow_redirects=False)
        response.raise_for_status()
        jwks = response.json()
    except requests.exceptions.RequestException:
        logger.exception("Unable to fetch jwks from %s", jwks_url)
        raise AuthenticationError("Unable to finalize the authentication process.")
    except json.JSONDecodeError:
        content = response.content if response else "Unable to find the response"
        logger.exception(
            "Unable to decode the response from auth service with jwks. "
            "Response: %s",
            content,
        )
        raise AuthenticationError("Unable to finalize the authentication process.")
    keys = jwks.get("keys", [])
    if not keys:
        logger.warning("List of JWKS keys is empty")
    cache.set(JWKS_KEY, keys, JWKS_CACHE_TIME)
    return keys


def get_user_info_from_cache_or_fetch(
    user_info_url: str, access_token: str, exp_time: Optional[int]
) -> Optional[dict]:
    user_info_data = cache.get(f"{PLUGIN_ID}.{access_token}", None)

    if not user_info_data:
        user_info_data = get_user_info(user_info_url, access_token)
        cache_time = USER_INFO_DEFAULT_CACHE_TIME

        if exp_time:
            now_ts = int(datetime.now().timestamp())
            exp_delta = exp_time - now_ts
            cache_time = exp_delta if exp_delta > 0 else cache_time

        if user_info_data:
            cache.set(f"{PLUGIN_ID}.{access_token}", user_info_data, cache_time)

    # user_info_data is None when we were not able to use an access token to fetch
    # the user info data
    return user_info_data


def get_user_info(user_info_url, access_token) -> Optional[dict]:
    try:
        response = HTTPClient.send_request(
            "GET",
            user_info_url,
            headers={"Authorization": f"Bearer {access_token}"},
            allow_redirects=False,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.warning(
            "Fetching OIDC user info failed. HTTP error occurred",
            extra={"user_info_url": user_info_url, "error": e},
        )
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(
            "Fetching OIDC user info failed",
            extra={"user_info_url": user_info_url, "error": e},
        )
        return None
    except json.JSONDecodeError as e:
        logger.warning(
            "Invalid OIDC user info response",
            extra={"user_info_url": user_info_url, "error": e},
        )
        return None


def decode_access_token(token, client_secret):
    try:
        return get_decoded_token(token, client_secret)
    except (JoseError, ValueError) as e:
        logger.info("Invalid OIDC access token format", extra={"error": e})
        return None


def assign_staff_to_default_group_and_update_permissions(
    user: "User", default_group_name: str
):
    """Assign staff user to the default permission group. and update user permissions.

    If the group doesn't exist, the new group without any assigned permissions and
    channels will be created.
    """
    default_group_name = (
        default_group_name.strip() if default_group_name else default_group_name
    )
    if default_group_name:
        group, _ = Group.objects.get_or_create(
            name=default_group_name, defaults={"restricted_access_to_channels": True}
        )
        user.groups.add(group)
    group_permissions = get_user_groups_permissions(user)
    user.effective_permissions |= group_permissions


def create_jwt_token(
    id_payload: CodeIDToken,
    user: User,
    access_token: str,
    permissions: Optional[list[str]],
    owner: str,
) -> str:
    additional_payload = {
        "exp": id_payload["exp"],
        "oauth_access_key": access_token,
    }
    if permissions is not None:
        additional_payload[PERMISSIONS_FIELD] = permissions

    jwt_payload = jwt_user_payload(
        user,
        JWT_ACCESS_TYPE,
        exp_delta=None,  # we pass exp from auth service, in additional_payload
        additional_payload=additional_payload,
        token_owner=owner,
    )
    return jwt_encode(jwt_payload)


def create_jwt_refresh_token(user: User, refresh_token: str, csrf: str, owner: str):
    additional_payload = {
        OAUTH_TOKEN_REFRESH_FIELD: refresh_token,
        CSRF_FIELD: csrf,
    }
    jwt_payload = jwt_user_payload(
        user,
        JWT_REFRESH_TYPE,
        # oauth_refresh_token has own expiration time. No need to duplicate it here
        exp_delta=None,
        additional_payload=additional_payload,
        token_owner=owner,
    )
    return jwt_encode(jwt_payload)


def get_decoded_token(token, token_secret, claims_cls=None):
    decoded_token = jwt.decode(token, token_secret, claims_cls=claims_cls)
    return decoded_token


def get_parsed_id_token(token_data, token_secret) -> CodeIDToken:
    decoded = jwt.decode(token_data, token_secret, claims_cls=CodeIDToken)
    assert isinstance(decoded, CodeIDToken)
    return decoded


def get_or_create_user_from_payload(
    payload: dict,
    email_domain: str,
    oauth_url: str,
) -> User:
    oidc_metadata_key = f"oidc:{oauth_url}"

    account = payload.get("sub")
    code = str(payload.get("code"))
    assert isinstance(account, str)

    user_email = account + email_domain
    get_kwargs = {"private_metadata__contains": {oidc_metadata_key: account}}

    defaults_create = {
        "is_active": True,
        "is_confirmed": True,
        "email": user_email,
        "account": account,
        "user_type": payload.get("user_type", "student"),
        "first_name": payload.get("name", ""),
        "last_name": payload.get("family_name", ""),
        "code": code,
        "private_metadata": {oidc_metadata_key: account},
        "password": make_password(None),
    }

    cache_key = oidc_metadata_key + ":" + str(account)

    user_id = cache.get(cache_key)

    if user_id:
        get_kwargs = {"id": user_id}
    try:
        user = User.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME).get(
            **get_kwargs
        )
    except User.DoesNotExist:
        user, _ = User.objects.get_or_create(
            email=user_email,
            defaults=defaults_create,
        )
        first_login_balance_event(user=user)
        consecutive_login_balance_event(
            user=user, delta=Decimal(settings.CONTINUOUS_BALANCE_ADD[0])
        )
        site, _ = Site.objects.get_or_create(id=settings.SITE_ID)

        if not site.domain or not site.name:
            site.name = settings.SITE_NAME
            site.domain = settings.SITE_DOMAIN
            site.save(update_fields=["name", "domain"])

        try:
            stat = site.stat
        except:
            stat = SiteStatistics.objects.get_or_create(site=site)

        stat.users += 1
        stat.save(update_fields=["users"])
        match_orders_with_new_user(user)
    except User.MultipleObjectsReturned:
        logger.warning("Multiple users returned for single OIDC sub ID")
        user, _ = User.objects.get_or_create(
            email=user_email,
            defaults=defaults_create,
        )

    site_settings = Site.objects.get_current().settings
    if not user.can_login(site_settings):  # it is true only if we fetch disabled user.
        raise AuthenticationError("Unable to log in.")

    _update_user_details(
        user=user,
        oidc_key=oidc_metadata_key,
        user_email=user_email,
        user_first_name=defaults_create["first_name"],
        user_last_name=defaults_create["last_name"],
        sub=account,  # type: ignore
        login_time=timezone.now(),
    )

    cache.set(cache_key, user.id, min(JWKS_CACHE_TIME, OIDC_DEFAULT_CACHE_TIME))
    return user


def get_domain_from_email(email: str):
    """Return domain from the email."""
    _user, delim, domain = email.rpartition("@")
    return domain if delim else None


def _update_continuous_days(user: User, login_time: datetime, fields_to_save: set):
    delta = login_time.day - user.last_login.day
    if delta > 1:
        user.continuous = 0
    if delta >= 1:
        user.continuous += 1
        if user.continuous <= len(settings.CONTINUOUS_BALANCE_ADD):
            balance_delta = Decimal(
                settings.CONTINUOUS_BALANCE_ADD[user.continuous - 1]
            )
        else:
            balance_delta = Decimal(settings.CONTINUOUS_BALANCE_ADD[-1])
        user.balance += Decimal(balance_delta)
        consecutive_login_balance_event(user=user, delta=balance_delta)
        fields_to_save.add("balance")
    elif delta > 1:
        user.continuous = 1
    user.last_login = login_time

    fields_to_save.update({"continuous", "last_login"})


def update_continuous_days(user: User):
    fields_to_save = set()
    _update_continuous_days(user, datetime.now(), fields_to_save)
    user.save(update_fields=fields_to_save)


def _update_user_details(
    user: User,
    oidc_key: str,
    user_email: str,
    user_first_name: str,
    user_last_name: str,
    sub: str,
    login_time: datetime,
):
    user_sub = user.get_value_from_private_metadata(oidc_key)
    fields_to_save = set()
    if user_sub != sub:
        user.store_value_in_private_metadata({oidc_key: sub})
        fields_to_save.add("private_metadata")

    if user.email != user_email:
        if User.objects.filter(email=user_email).exists():
            logger.warning(
                "Unable to update user email as the new one already exists in DB",
                extra={"oidc_key": oidc_key},
            )
            return
        user.email = user_email
        match_orders_with_new_user(user)
        fields_to_save.update({"email", "search_document"})

    _update_continuous_days(user, login_time, fields_to_save)

    if user.first_name != user_first_name:
        user.first_name = user_first_name
        fields_to_save.update({"first_name", "search_document"})

    if user.last_name != user_last_name:
        user.last_name = user_last_name
        fields_to_save.update({"last_name", "search_document"})

    if "search_document" in fields_to_save:
        user.search_document = prepare_user_search_document_value(
            user, attach_addresses_data=False
        )

    if fields_to_save:
        user.save(update_fields=fields_to_save)


def get_staff_user_domains(
    config: "OpenIDConnectConfig",
):
    """Return staff user domains for given gateway configuration."""
    staff_domains = config.staff_user_domains
    return (
        [domain.strip().lower() for domain in staff_domains.split(",")]
        if staff_domains
        else []
    )


def get_user_from_token(claims: CodeIDToken) -> User:
    user_email = claims.get("email")
    if not user_email:
        raise AuthenticationError("Missing user's email.")

    site_settings = Site.objects.get_current().settings
    user = User.objects.filter(email=user_email).first()
    if not user or not user.can_login(site_settings):
        raise AuthenticationError("User does not exist.")
    return user


def is_owner_of_token_valid(token: str, owner: str) -> bool:
    try:
        payload = jwt_decode(token, verify_expiration=False)
        return payload.get(JWT_OWNER_FIELD, "") == owner
    except Exception:
        return False


def create_tokens_from_oauth_payload(
    token_data: dict,
    user: User,
    claims: CodeIDToken,
    permissions: Optional[list[str]],
    owner: str,
):
    refresh_token = token_data.get("refresh_token")
    access_token = token_data.get("access_token", "")

    tokens = {
        "token": create_jwt_token(claims, user, access_token, permissions, owner),
    }
    if refresh_token:
        csrf_token = _get_new_csrf_token()
        tokens["refresh_token"] = create_jwt_refresh_token(
            user, refresh_token, csrf_token, owner
        )
        tokens["csrf_token"] = csrf_token
    return tokens


def validate_refresh_token(refresh_token, data):
    csrf_token = data.get("csrfToken")
    if not refresh_token:
        raise ValidationError(
            {
                "refreshToken": ValidationError(
                    "Missing token.", code=PluginErrorCode.NOT_FOUND.value
                )
            }
        )

    try:
        refresh_payload = jwt_decode(refresh_token, verify_expiration=True)
    except PyJWTError:
        raise ValidationError(
            {
                "refreshToken": ValidationError(
                    "Unable to decode the refresh token.",
                    code=PluginErrorCode.INVALID.value,
                )
            }
        )

    if not data.get("refreshToken"):
        if not refresh_payload.get(CSRF_FIELD):
            raise ValidationError(
                {
                    CSRF_FIELD: ValidationError(
                        "Missing CSRF token in refresh payload.",
                        code=PluginErrorCode.INVALID.value,
                    )
                }
            )
        if not csrf_token:
            raise ValidationError(
                {
                    "csrfToken": ValidationError(
                        "CSRF token needs to be provided.",
                        code=PluginErrorCode.INVALID.value,
                    )
                }
            )
        is_valid = _does_token_match(csrf_token, refresh_payload[CSRF_FIELD])
        if not is_valid:
            raise ValidationError(
                {
                    "csrfToken": ValidationError(
                        "CSRF token doesn't match.",
                        code=PluginErrorCode.INVALID.value,
                    )
                }
            )


def get_incorrect_or_missing_urls(urls: dict) -> list[str]:
    validator = URLValidator()
    incorrect_urls = []
    for field, url in urls.items():
        try:
            validator(url)
        except ValidationError:
            incorrect_urls.append(field)
    return incorrect_urls


def get_incorrect_fields(plugin_configuration: "PluginConfiguration"):
    """Return missing or incorrect configuration fields for OpenIDConnectPlugin."""
    configuration = plugin_configuration.configuration
    configuration = {item["name"]: item["value"] for item in configuration}
    incorrect_fields = []
    if plugin_configuration.active:
        urls_to_validate = {}
        if any(
            [configuration["oauth_authorization_url"], configuration["oauth_token_url"]]
        ):
            urls_to_validate.update(
                {
                    "json_web_key_set_url": configuration["json_web_key_set_url"],
                    "oauth_authorization_url": configuration["oauth_authorization_url"],
                    "oauth_token_url": configuration["oauth_token_url"],
                }
            )

        elif configuration["user_info_url"]:
            urls_to_validate.update(
                {
                    "json_web_key_set_url": configuration["json_web_key_set_url"],
                    "user_info_url": configuration["user_info_url"],
                }
            )
        else:
            incorrect_fields.extend(
                [
                    "json_web_key_set_url",
                    "oauth_authorization_url",
                    "oauth_token_url",
                    "user_info_url",
                ]
            )

        incorrect_fields.extend(get_incorrect_or_missing_urls(urls_to_validate))
        if not configuration["client_id"]:
            incorrect_fields.append("client_id")
        if not configuration["client_secret"]:
            incorrect_fields.append("client_secret")
        return incorrect_fields


def get_saleor_permissions_qs_from_scope(scope: str) -> QuerySet[Permission]:
    scope_list = scope.lower().strip().split()
    return get_saleor_permissions_from_list(scope_list)


def get_saleor_permissions_from_list(permissions: list) -> QuerySet[Permission]:
    saleor_permissions_str = [s for s in permissions if s.startswith("saleor:")]
    if SALEOR_STAFF_PERMISSION in saleor_permissions_str:
        saleor_permissions_str.remove(SALEOR_STAFF_PERMISSION)
    if not saleor_permissions_str:
        return Permission.objects.none()

    permission_codenames = list(
        map(lambda perm: perm.replace("saleor:", ""), saleor_permissions_str)
    )
    permissions = get_permissions_from_codenames(permission_codenames)
    return permissions


def get_saleor_permission_names(permissions: QuerySet) -> list[str]:
    permission_names = get_permission_names(permissions)
    return list(permission_names)
