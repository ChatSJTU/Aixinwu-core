from ...csv import ExportEvents, FileTypes
from ..core.doc_category import DOC_CATEGORY_PRODUCTS
from ..core.enums import to_enum
from ..core.types import BaseEnum

ExportEventEnum = to_enum(ExportEvents)
FileTypeEnum = to_enum(FileTypes)


class ExportScope(BaseEnum):
    ALL = "all"
    IDS = "ids"
    FILTER = "filter"

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS

    @property
    def description(self):
        # pylint: disable=no-member
        description_mapping = {
            ExportScope.ALL.name: "Export all products.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            ExportScope.IDS.name: "Export products with given ids.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            ExportScope.FILTER.name: "Export the filtered products.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
        }
        if self.name in description_mapping:
            return description_mapping[self.name]
        raise ValueError(f"Unsupported enum value: {self.value}")


class ProductFieldEnum(BaseEnum):
    NAME = "name"
    DESCRIPTION = "description"
    PRODUCT_TYPE = "product type"
    CATEGORY = "category"
    PRODUCT_WEIGHT = "product weight"
    COLLECTIONS = "collections"
    CHARGE_TAXES = "charge taxes"  # deprecated; remove in Saleor 4.0
    PRODUCT_MEDIA = "product media"
    VARIANT_ID = "variant id"
    VARIANT_SKU = "variant sku"
    VARIANT_WEIGHT = "variant weight"
    VARIANT_MEDIA = "variant media"

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class OrderFieldEnum(BaseEnum):
    NUMBER = "number"
    USER_FIRST_NAME = "user first name"
    USER_ACCOUNT = "user account"
    USER_EMAIL = "user email"
    USER_CODE = "user code"
    USER_TYPE = "user type"
    ORDERLINE_PRODUCT_NAME = "orderline product name"
    ORDERLINE_QUANTITY = "orderline quantity"
    ORDERLINE_TOTAL_PRICE_GROSS_AMOUNT = "orderline total price gross amount"
    TOTAL_GROSS_AMOUNT = "total gross amount"
    CREATED_AT = "created at"
    CUSTOMER_NOTE = "customer note"
    STATUS = "status"
    CHARGE_STATUS = "charge status"
    ADDRESS_FIRST_NAME = "address first name"
    ADDRESS_PHONE = "address phone"
    ADDRESS_STREET_ADDRESS_1 = "address street address 1"
