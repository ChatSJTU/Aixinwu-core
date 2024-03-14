from ...donation.models import Donation
from ..core.dataloaders import DataLoader


class DonationByDonatorDataloader(DataLoader):
    context_key = "donation_by_user"

    def batch_load(self, keys):
        return (
            Donation.objects.using(self.database_connection_name)
            .filter(donator_id__in=keys)
            .all()
        )


class DonationByIdDataLoader(DataLoader):
    context_key = "donation_by_id"

    def batch_load(self, keys):
        return (
            Donation.objects.using(self.database_connection_name)
            .filter(id__in=keys)
            .all()
        )
