import graphene
from django.core.exceptions import ValidationError

from ....csv import models
from ....csv.tasks import import_csv_task
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_CSV
from ...core.mutations import ModelMutation
from ...core.types import ImportError
from ...core.types.base import BaseInputObjectType
from ...core.types.upload import Upload
from ..types import ImportFile


class ImportCSVUpdateInput(BaseInputObjectType):
    file = Upload(
        description="Uploaded CSV file content or file path.",
        required=True,
    )


class ImportCSVUpdate(ModelMutation):
    import_file = graphene.Field(
        ImportFile,
        description="The import file updated by this mutation.",
    )

    class Arguments:
        id = graphene.ID(required=True, description="The ID of the import file.")
        input = ImportCSVUpdateInput(
            required=True, description="Fields required to update an import file."
        )

    class Meta:
        description = "Update an import file."
        doc_category = DOC_CATEGORY_CSV
        model = models.ImportFile
        object_type = ImportFile
        return_field_name = "import_file"
        error_type_class = ImportError
        error_type_fields = "import_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        import_file = cls.get_instance(info, data["id"], ImportFile)
        input = data["input"]
        csv_file = input["file"]

        if not csv_file:
            raise ValidationError({"file": "No file was provided."})
        file = info.context.FILES.get(csv_file)
        if not file:
            raise ValidationError({"file": "The file was not found in the request."})
        import_file.data_file.save(file.name, file)
        import_file.save(update_fields=["data_file", "updated_at"])
        import_csv_task.delay(import_file.id, import_file.type)
        return cls.success_response(instance=import_file)
