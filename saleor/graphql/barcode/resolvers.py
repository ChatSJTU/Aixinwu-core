from ..core.context import get_database_connection_name
from ...permission.enums import BarcodePermissions
from ..account.utils import check_is_owner_or_has_one_of_perms
from ..core import ResolveInfo
from ..utils import get_user_or_app_from_context
from ...barcode.models import Barcode


def resolve_barcodes(info: ResolveInfo):
    requestor = get_user_or_app_from_context(info.context)
    check_is_owner_or_has_one_of_perms(
        requestor, None, BarcodePermissions.MANAGE_BARCODE
    )
    return Barcode.objects.using(get_database_connection_name(info.context))
