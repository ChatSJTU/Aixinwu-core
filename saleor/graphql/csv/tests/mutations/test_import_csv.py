from ....tests.utils import (
    get_graphql_content,
    get_multipart_request_body,
)
from .utils import create_csv_file

IMPORT_FILE_MUTATION = """
    mutation MyMutation($file: Upload!) {
        importCsv(input: {file: $file, type: ACCOUNT}) {
            importFile {
            id
            message
            number
            status
            type
            }
        }
    }
"""


def test_mutation_import_csv(staff_api_client):
    query = IMPORT_FILE_MUTATION

    file = create_csv_file()
    variables = {"file": file.name}
    response = staff_api_client.post_multipart(
        get_multipart_request_body(query, variables, file, file.name)
    )
    print(response.content)
