import pandas
from django.core.files.uploadedfile import SimpleUploadedFile


def create_csv_file():
    df = pandas.DataFrame({"name": ["test"], "description": ["test description"]})
    csv_data = df.to_csv(index=False)
    csv_file = SimpleUploadedFile("test.csv", csv_data.encode("utf-8"), "text/csv")
    return csv_file
