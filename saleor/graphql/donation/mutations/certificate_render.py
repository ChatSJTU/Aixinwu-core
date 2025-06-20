import hashlib
import os

import graphene
import pymupdf

from .... import settings
from ....account.models import User
from ....core.exceptions import PermissionDenied
from ....core.utils import build_absolute_uri
from ....donation.models import Donation
from ...core import ResolveInfo
from ...core.utils import from_global_id_or_error
from ...utils import get_user_or_app_from_context


class CertificateRender(graphene.Mutation):
    class Arguments:
        donation_id = graphene.ID(required=True, description="ID of the donation.")

    certificate_pdf = graphene.String(
        description="The rendered certificate in PDF format."
    )
    certificate_png = graphene.String(
        description="The rendered certificate in PNG format."
    )

    @staticmethod
    def _integer_to_chinese(integer: int):
        chinese_numerals = {
            "0": "〇",
            "1": "一",
            "2": "二",
            "3": "三",
            "4": "四",
            "5": "五",
            "6": "六",
            "7": "七",
            "8": "八",
            "9": "九",
        }
        return "".join(
            chinese_numerals[digit]
            for digit in str(integer)
            if digit in chinese_numerals
        )

    @classmethod
    def mutate(cls, root, info: ResolveInfo, donation_id):
        user = get_user_or_app_from_context(info.context)
        if not user:
            raise PermissionDenied("You do not have permission to render certificate.")
        _, db_id = from_global_id_or_error(donation_id, "Donation")
        try:
            donation = (
                Donation.objects.get(pk=db_id)
                if user.has_perm("donation.manage_donations")
                else Donation.objects.get(pk=db_id, donator=user.code)  # type: ignore
            )
        except Donation.DoesNotExist:
            raise PermissionDenied("Donation not found.")
        if not donation.certificate:
            return CertificateRender(certificate=None)
        certificate_template = os.path.join(
            settings.TEMPLATES_DIR,
            "certificates",
            donation.certificate.template_filename,
        )
        data = {
            "name": User.objects.get(code=donation.donator).first_name,
            "quantity": str(donation.quantity),
            "price": str(donation.price.amount).rstrip("0").rstrip("."),  # type: ignore
            "year": cls._integer_to_chinese(donation.created_at.year),
            "month": cls._integer_to_chinese(donation.created_at.month),
        }
        doc = pymupdf.open(certificate_template)
        for page in doc:
            for widget in page.widgets():
                if widget.field_name in data:
                    widget.field_value = data[widget.field_name]  # type: ignore
                    widget.update()
        doc.bake()
        save_path = os.path.join(settings.MEDIA_ROOT, "certificates")
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        filename = hashlib.sha256(
            settings.SECRET_KEY.encode() + donation_id.encode()
        ).hexdigest()
        doc.save(os.path.join(save_path, f"{filename}.pdf"))
        img = doc.load_page(0).get_pixmap(dpi=300)  # type: ignore
        img.save(os.path.join(save_path, f"{filename}.png"))
        return CertificateRender(
            certificate_pdf=build_absolute_uri(
                os.path.join(settings.MEDIA_URL, "certificates", f"{filename}.pdf")
            ),
            certificate_png=build_absolute_uri(
                os.path.join(settings.MEDIA_URL, "certificates", f"{filename}.png")
            ),
        )
