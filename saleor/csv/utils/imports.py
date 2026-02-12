import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import pandas as pd
from django.core.exceptions import ValidationError

from ...account.events import change_balance_event
from ...account.models import User
from ...csv.models import ImportFile
from .. import ImportStatus, ImportType

VALID_KEYS = ["code", "username", "jaccount", "email", "bonus", "poor_sign"].sort()


def validate_account_dataframe(df: pd.DataFrame, import_status: str):
    if df.keys().tolist().sort() != VALID_KEYS:
        raise ValidationError(
            {"file": ValidationError("Invalid csv keys.", code="invalid")}
        )


def update_users_with_complete_df(df, existing_users):
    for _, row in df.iterrows():
        user = existing_users.get(jaccount=row["jaccount"])
        if row["bonus"]:
            user.balance += Decimal(row["bonus"])
            change_balance_event(user=user, balance=user.balance)
        if row["poor_sign"] is not None:
            user.private_metadata = user.private_metadata or {}
            user.private_metadata["is_poor"] = str(bool(row["poor_sign"])).lower()
    User.objects.bulk_update(existing_users, ["balance", "poor_mark"])


def create_users_with_complete_df(df):
    user_objects = []
    for _, row in df.iterrows():
        user = User(
            code=row["code"],
            username=row["username"],
            jaccount=row["jaccount"],
            email=row["email"],
            balance=Decimal(row["bonus"]),
            private_metadata={"is_poor": str(bool(row["poor_sign"])).lower()},
        )
        user_objects.append(user)
    User.objects.bulk_create(user_objects)


@dataclass
class ImportResult:
    success: bool
    nrecords: int = 0
    nimports: int = 0
    nupdates: int = 0
    errors: Optional[pd.DataFrame] = None


def import_account_csv_pending(df: pd.DataFrame) -> ImportResult:
    codes = df["code"].tolist()
    existing_users = User.objects.filter(code__in=codes)
    existing_codes = set(existing_users.values_list("code", flat=True))
    rows_not_found = df[~df["code"].isin(existing_codes)]
    rows_to_updates = df[df["code"].isin(existing_codes)]

    if not rows_not_found.empty:
        if (
            rows_not_found["username"].isnull().any()
            or rows_not_found["jaccount"].isnull().any()
        ):
            rows_not_found[rows_not_found["username"].isnull()]["username"] = "N/A"
            rows_not_found[rows_not_found["jaccount"].isnull()]["jaccount"] = "N/A"
            return ImportResult(success=False, errors=df)

    rows_to_creates = rows_not_found
    create_users_with_complete_df(rows_to_creates)
    update_users_with_complete_df(rows_to_updates, existing_users)

    return ImportResult(
        success=True,
        nrecords=len(df),
        nimports=len(rows_to_creates),
        nupdates=len(rows_to_updates),
    )


def import_account_csv_incomplete(df: pd.DataFrame) -> ImportResult:
    jaccounts = df["jaccount"].tolist()
    existing_users = User.objects.filter(jaccount__in=jaccounts)
    existing_jaccounts = set(existing_users.values_list("jaccount", flat=True))

    rows_to_updates = df[df["jaccount"].isin(existing_jaccounts)]
    rows_not_found = df[~df["jaccount"].isin(existing_jaccounts)]

    if not rows_not_found.empty:
        if (
            rows_not_found["username"].isnull().any()
            or rows_not_found["email"].isnull().any()
        ):
            rows_not_found[rows_not_found["username"].isnull()]["username"] = "N/A"
            rows_not_found[rows_not_found["email"].isnull()]["email"] = "N/A"
            return ImportResult(success=False, errors=df)

    rows_to_creates = rows_not_found
    create_users_with_complete_df(rows_to_creates)
    update_users_with_complete_df(rows_to_updates, existing_users)

    return ImportResult(
        success=True,
        nrecords=len(df),
        nimports=len(rows_to_creates),
        nupdates=len(rows_to_updates),
    )


def import_file_csv(import_file: ImportFile) -> Optional[pd.DataFrame]:
    df: pd.DataFrame

    with import_file.data_file.open() as f:
        if ext := os.path.splitext(import_file.data_file.name)[1].lower() != ".csv":
            raise ValueError(f"Invalid file extension: {ext}. CSV file required.")
        df = pd.read_csv(f)

    if import_file.type == ImportType.ACCOUNT:
        validate_account_dataframe(df, import_file.status)
        if import_file.status == ImportStatus.PENDING:
            result = import_account_csv_pending(df)
        elif import_file.status == ImportStatus.INCOMPLETE:
            result = import_account_csv_incomplete(df)

        if not result.success:
            result.errors.to_csv(import_file.data_file.path, index=False)
            import_file.metadata = {"download_link": import_file.data_file.url}
            import_file.status = ImportStatus.INCOMPLETE
            import_file.save(update_fields=["metadata", "status", "updated_at"])
        else:
            import_file.metadata = {
                "record_num": result.nrecords,
                "import_num": result.nimports,
                "update_num": result.nupdates,
            }
            import_file.status = ImportStatus.SUCCESS
            import_file.save(update_fields=["metadata", "updated_at"])
