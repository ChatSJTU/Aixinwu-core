class DonationStatus:
    UNREVIEWED = "unreviewed"
    COMPLETED = "completed"
    REJECTED = "rejected"

    CHOICES = [
        (UNREVIEWED, "The donation is not yet to be reviewed."),
        (COMPLETED, "The donation is completed."),
        (REJECTED, "The donation is rejected."),
    ]
