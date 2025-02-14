from saleor.account.models import User
from . import ProductEvents, ProductVariantEvents
from .models import Product, ProductEvent, ProductVariant, ProductVariantChannelListing, ProductVariantEvent
from saleor.product import models

def product_create_event(user: User, product: Product):
    ProductEvent.objects.create(
        user=user, 
        product_name=product.name, 
        product=product, 
        type=ProductEvents.PRODUCT_CREATED,
        message=f"用户 {user.account or user.first_name} 创建了商品 {product.name}"
    )


def product_delete_event(user, product):
    ProductEvent.objects.create(
        user=user, 
        product_name=product.name, 
        type=ProductEvents.PRODUCT_DELETED,
        message=f"用户 {user.account or user.first_name} 删除了商品 {product.name}",
    )


def product_bulk_create_events(user, products):
    ProductEvent.objects.bulk_create(
        [
            ProductEvent(
                user=user, 
                product=product, 
                product_name=product.name, 
                type=ProductEvents.PRODUCT_CREATED,
                message=f"用户 {user.account or user.first_name} 创建了商品 {product.name}"
            )
            for product in products
        ]
    )


def product_bulk_delete_events(user, products):
    ProductEvent.objects.bulk_create(
        [
            ProductEvent(
                user=user, 
                product_name=product.name, 
                type=ProductEvents.PRODUCT_DELETED,
                message=f"用户 {user.account or user.first_name} 删除了商品 {product.name}"
            )
            for product in products
        ]
    )


def product_variant_create_event(user, variant: ProductVariant):
    ProductVariantEvent.objects.create(
        user=user,
        product_variant=variant,
        product_variant_name=variant.name,
        type=ProductVariantEvents.PRODUCT_VARIANT_CREATED,
        message=f"用户 {user.account or user.first_name} 创建了商品 {variant.product.name} 的品种 {variant.name}",
    )


def product_variant_delete_event(user, variant):
    ProductVariantEvent.objects.create(
        user=user,
        product_variant_name=variant.name,
        type=ProductVariantEvents.PRODUCT_VARIANT_DELETED,
        message=f"用户 {user.account or user.first_name} 删除了商品 {variant.product.name} 的品种 {variant.name}",
    )


def product_variant_stock_changed_event(user, variant, stock, order, reason):
    ProductVariantEvent.objects.create(
        user=user,
        product_variant=variant,
        product_variant_name=variant.name,
        stock_changed=stock,
        order=order,
        type=ProductVariantEvents.PRODUCT_VARIANT_STOCK_CHANGED,
        message=f"{variant.product.name} {variant.name} 库存变动 {stock:+}（原因：{reason}）",
    )


def product_variant_bulk_create_events(user, variants):
    ProductVariantEvent.objects.bulk_create(
        [
            ProductVariantEvent(
                user=user,
                product_variant=variant,
                product_variant_name=variant.name,
                type=ProductVariantEvents.PRODUCT_VARIANT_CREATED,
                message=f"用户 {user.account or user.first_name} 创建了商品 {variant.product.name} 的品种 {variant.name}",
            )
            for variant in variants
        ]
    )


def product_variant_bulk_delete_events(user, variants):
    ProductVariantEvent.objects.bulk_create(
        [
            ProductVariantEvent(
                user=user,
                product_variant_name=variant.name,
                type=ProductVariantEvents.PRODUCT_VARIANT_DELETED,
                message=f"用户 {user.account or user.first_name} 删除了商品 {variant.product.name} 的品种 {variant.name}",
            )
            for variant in variants
        ]
    )


def product_variant_stock_bulk_update_events(user, variants, stocks, reason):
    ProductVariantEvent.objects.bulk_create(
        [
            ProductVariantEvent(
                user=user,
                product_variant=variant,
                product_variant_name=variant.name,
                stock_changed=stock,
                type=ProductVariantEvents.PRODUCT_VARIANT_STOCK_CHANGED,
                message=f"{variant.product.name} {variant.name} 库存变动 {stock:+}（原因：{reason}）",
            )
            for variant, stock in zip(variants, stocks)
        ]
    )

def product_variant_price_bulk_update_events(user, listings: list[models.ProductVariantChannelListing], reason):
    ProductVariantEvent.objects.bulk_create(
        [
            ProductVariantEvent(
                user=user,
                product_variant=listing.variant,
                product_variant_name=listing.variant.name,
                type=ProductVariantEvents.PRODUCT_VARIANT_PRICE_UPDATED,
                message=f"{listing.variant.product.name} {listing.variant.name} 在 {listing.channel.name} 的价格更新为 {listing.price_amount}（原因：{reason}）",
            )
            for listing in listings
        ]
    )
