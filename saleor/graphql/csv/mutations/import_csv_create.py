from django.core.exceptions import ValidationError

from ....csv import models
from ....csv.tasks import import_csv_task
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_CSV
from ...core.types import BaseInputObjectType, ImportError, Upload
from ...core.validators.file import clean_csv_file
from ..enums import ImportTypeEnum
from .base_import import BaseImportMutation


class ImportCsvInput(BaseInputObjectType):
    file = Upload(
        description="Uploaded CSV file content or file path.",
        required=True,
    )
    type = ImportTypeEnum(
        description="Type of import (e.g., 'accounts').",
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_CSV


class ImportCSVCreate(BaseImportMutation):
    class Arguments:
        input = ImportCsvInput(
            required=True, description="Fields required to import CSV data."
        )

    class Meta:
        description = "Import data from a CSV file."
        error_type_class = ImportError
        error_type_field = "import_errors"
        doc_category = DOC_CATEGORY_CSV

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, *, input):
        csv_file = input.get("file")
        import_type = input.get("type")
        if not csv_file:
            raise ValidationError({"file": "You must provide a CSV file."})
        if not import_type:
            raise ValidationError({"type": "You must provide an import type."})

        file = info.context.FILES.get(csv_file)
        if not file:
            raise ValidationError(
                {
                    "file": ValidationError(
                        "File not found in the request. Ensure the file is uploaded correctly.",
                    )
                }
            )
        input["file"] = file
        file = clean_csv_file(input, "file", ImportError)
        import_file = models.ImportFile.objects.create(
            user=info.context.user,
            data_file=file,
            type=import_type,
        )
        import_csv_task.delay(import_file.id, import_type)
        return cls(import_file=import_file)
