from collections.abc import Mapping
from typing import Union

import graphene
from django.core.exceptions import ValidationError

from ...core.enums import ExportErrorCode
from ...core.mutations import BaseMutation
from ..enums import ExportScope
from ..types import ImportFile


class BaseImportMutation(BaseMutation):
    import_file = graphene.Field(
        ImportFile,
        description=(
            "The newly created import file job which is responsible for importing data."
        ),
    )

    class Meta:
        abstract = True

    @classmethod
    def get_scope(cls, input) -> Mapping[str, Union[dict, str]]:
        scope = input.get("scope", "all")
        if scope == ExportScope.FILTER.value:  # type: ignore[attr-defined]
            return cls.clean_filter(input)
        return {"all": ""}

    @staticmethod
    def clean_file(input) -> dict[str, str]:
        file_data = input.get("file")
        if not file_data:
            raise ValidationError(
                {
                    "file": ValidationError(
                        "You must provide a file.",
                        code=ExportErrorCode.REQUIRED.value,
                    )
                }
            )
        return {"file": file_data}
