from . import ProductEvents, ProductVariantEvents
from .models import ProductEvent, ProductVariantEvent


def product_create_event(user, product):
    ProductEvent.objects.create(
        user=user, product=product, type=ProductEvents.PRODUCT_CREATED
    )


def product_delete_event(user, product):
    ProductEvent.objects.create(
        user=user, product_name=product.name, type=ProductEvents.PRODUCT_DELETED
    )


def product_bulk_create_events(user, products):
    ProductEvent.objects.bulk_create(
        [
            ProductEvent(user=user, product=product, type=ProductEvents.PRODUCT_CREATED)
            for product in products
        ]
    )


def product_bulk_delete_events(user, product_names):
    ProductEvent.objects.bulk_create(
        [
            ProductEvent(
                user=user, product_name=product_name, type=ProductEvents.PRODUCT_DELETED
            )
            for product_name in product_names
        ]
    )


def product_variant_create_event(user, variant):
    ProductVariantEvent.objects.create(
        user=user,
        product_variant=variant,
        type=ProductVariantEvents.PRODUCT_VARIANT_CREATED,
    )


def product_variant_delete_event(user, variant):
    ProductVariantEvent.objects.create(
        user=user,
        product_variant_name=variant.name,
        type=ProductVariantEvents.PRODUCT_VARIANT_DELETED,
    )


def product_variant_update_event(user, variant, stock):
    ProductVariantEvent.objects.create(
        user=user,
        product_variant=variant,
        stock_changed=stock,
        type=ProductVariantEvents.PRODUCT_VARIANT_UPDATED,
    )


def product_variant_bulk_create_events(user, variants):
    ProductVariantEvent.objects.bulk_create(
        [
            ProductVariantEvent(
                user=user,
                product_variant=variant,
                type=ProductVariantEvents.PRODUCT_VARIANT_CREATED,
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
            )
            for variant in variants
        ]
    )


def product_variant_bulk_update_events(user, variants, stocks):
    ProductVariantEvent.objects.bulk_create(
        [
            ProductVariantEvent(
                user=user,
                product_variant=variant,
                stock_changed=stock,
                type=ProductVariantEvents.PRODUCT_VARIANT_UPDATED,
            )
            for variant, stock in zip(variants, stocks)
        ]
    )
