import graphene

from saleor.graphql.core.types.common import NonNullList
from saleor.site.models import SiteCarousel, SiteCarouselLine

from ....permission.enums import SitePermissions
from ...core import ResolveInfo
from ...core.descriptions import DEPRECATED_IN_3X_MUTATION
from ...core.doc_category import DOC_CATEGORY_SHOP
from ...core.mutations import BaseMutation
from ...core.types import ShopError
from ...site.dataloaders import get_site_promise
from ..types import Carousel, Shop
from django.utils import timezone


class CarouselInput(graphene.InputObjectType):
    urls = NonNullList(
        graphene.String, required=True, description="Url list of new carousel."
    )

    class Meta:
        doc_category = DOC_CATEGORY_SHOP


class ShopCarouselUpdate(BaseMutation):
    carousel = graphene.Field(Carousel, description="Updated carousel.")

    class Arguments:
        input = CarouselInput(
            description="Fields required to update or create the current carousel.",
            required=True,
        )

    class Meta:
        description = (
            "Updates site domain of the shop."
            + DEPRECATED_IN_3X_MUTATION
            + " Use `PUBLIC_URL` environment variable instead."
        )
        doc_category = DOC_CATEGORY_SHOP
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input
    ):
        site_settings = get_site_promise(info.context).get().settings
        urls = input.get("urls")
        try:
            carousel = site_settings.carousel
            carousel.site = None
            carousel.deleted_at = timezone.now()
            carousel.save(update_fields=["site", "deleted_at"])
        except:
            raise  # no carousel present passing

        carousel = SiteCarousel.objects.create(site=site_settings)

        SiteCarouselLine.objects.bulk_create(
            [SiteCarouselLine(url=url, carousel=carousel) for url in urls]
        )
        return ShopCarouselUpdate(carousel=Carousel())
