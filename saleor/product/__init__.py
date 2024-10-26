default_app_config = "saleor.product.app.ProductAppConfig"


class ProductMediaTypes:
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"

    CHOICES = [
        (IMAGE, "An uploaded image or an URL to an image"),
        (VIDEO, "A URL to an external video"),
    ]


class ProductTypeKind:
    NORMAL = "normal"
    GIFT_CARD = "gift_card"

    CHOICES = [
        (NORMAL, "A standard product type."),
        (GIFT_CARD, "A gift card product type."),
    ]


class ProductEvents:
    PRODUCT_CREATED = "product_created"
    PRODUCT_DELETED = "product_deleted"

    CHOICES = [
        (PRODUCT_CREATED, "A product gets created."),
        (PRODUCT_DELETED, "A product gets deleted."),
    ]


class ProductVariantEvents:
    PRODUCT_VARIANT_UPDATED = "product_variant updated"
    PRODUCT_VARIANT_CREATED = "product_variant created"
    PRODUCT_VARIANT_DELETED = "product_variant deleted"

    CHOICES = [
        (PRODUCT_VARIANT_CREATED, "A product variant get created."),
        (PRODUCT_VARIANT_UPDATED, "A product variant get updated."),
        (PRODUCT_VARIANT_DELETED, "A product variant get deleted."),
    ]
