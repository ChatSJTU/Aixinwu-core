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
    PRODUCT_UPDATED = "product_updated"

    CHOICES = [
        (PRODUCT_CREATED, "A product gets created."),
        (PRODUCT_DELETED, "A product gets deleted."),
        (PRODUCT_UPDATED, "A product gets updated."),
    ]


class ProductVariantEvents:
    PRODUCT_VARIANT_UPDATED = "product_variant_updated"
    PRODUCT_VARIANT_CREATED = "product_variant_created"
    PRODUCT_VARIANT_DELETED = "product_variant_deleted"
    PRODUCT_VARIANT_PRICE_UPDATED = "product_variant_price_updated"
    PRODUCT_VARIANT_STOCK_CHANGED = "product_variant_stock_changed"

    CHOICES = [
        (PRODUCT_VARIANT_CREATED, "A product variant get created."),
        (PRODUCT_VARIANT_UPDATED, "A product variant get updated."),
        (PRODUCT_VARIANT_DELETED, "A product variant get deleted."),
        (PRODUCT_VARIANT_PRICE_UPDATED, "The price of a product variant has changed."),
        (PRODUCT_VARIANT_STOCK_CHANGED, "The stock of a product variant has changed."),
    ]
