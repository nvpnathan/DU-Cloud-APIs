import os
import csv
import sqlite3
from config import SQLITE_DB_PATH


class WriteResults:
    def __init__(
        self, document_path, extraction_results=None, validation_extraction_results=None
    ):
        self.extraction_results = extraction_results
        self.validation_results = validation_extraction_results
        self.conn = sqlite3.connect(SQLITE_DB_PATH)
        self.cursor = self.conn.cursor()
        self.filename = os.path.basename(document_path)

    def create_headers_lookup_dict(self, table_data):
        header_dict = {}
        for field in table_data:
            field_id = field["FieldId"]
            field_headers = {}
            for value in field["Values"]:
                for cell in value["Cells"]:
                    if cell["RowIndex"] == 0 and cell["IsHeader"]:
                        column_index = cell["ColumnIndex"]
                        header_value = cell["Values"][0]["Value"]
                        field_headers[column_index] = header_value
            header_dict[field_id] = field_headers
        return header_dict

    def insert_field_data(self):
        document_id = self.extraction_results["extractionResult"]["DocumentId"]
        document_type_id = self.extraction_results["extractionResult"][
            "ResultsDocument"
        ]["DocumentTypeId"]

        for field in self.extraction_results["extractionResult"]["ResultsDocument"][
            "Fields"
        ]:
            field_data = {
                "filename": self.filename,
                "document_id": document_id,
                "document_type_id": document_type_id,
                "field_id": field.get("FieldId"),
                "field": field.get("FieldName"),
                "is_missing": field.get("IsMissing"),
                "field_value": None,
                "field_unformatted_value": None,
                "confidence": None,
                "ocr_confidence": None,
                "operator_confirmed": None,
                "is_correct": True,
            }
            if "Values" in field and field["Values"]:
                field_data.update(
                    {
                        "field_value": field["Values"][0].get("Value"),
                        "field_unformatted_value": field["Values"][0].get(
                            "UnformattedValue"
                        ),
                        "confidence": field["Values"][0].get("Confidence"),
                        "ocr_confidence": field["Values"][0].get("OcrConfidence"),
                        "operator_confirmed": field["Values"][0].get(
                            "OperatorConfirmed"
                        ),
                    }
                )
            columns = ", ".join(field_data.keys())
            placeholders = ", ".join(["?"] * len(field_data))
            sql = f"INSERT INTO extraction ({columns}) VALUES ({placeholders})"
            self.cursor.execute(sql, list(field_data.values()))

    def insert_table_data(self):
        document_id = self.extraction_results["extractionResult"]["DocumentId"]
        document_type_id = self.extraction_results["extractionResult"][
            "ResultsDocument"
        ]["DocumentTypeId"]

        tables = (
            self.extraction_results.get("extractionResult", {})
            .get("ResultsDocument", {})
            .get("Tables", [])
        )
        if tables:
            for table in tables:
                headers_lookup = self.create_headers_lookup_dict([table])
                field_id = table["FieldId"]
                headers = headers_lookup.get(field_id, {})

                for value in table["Values"]:
                    for cell in value["Cells"]:
                        # Skip header row
                        if cell["RowIndex"] != 0 and not cell["IsHeader"]:
                            cell_values = cell.get("Values", [{}])
                            first_value = cell_values[0] if cell_values else {}

                            row_data = {
                                "filename": self.filename,
                                "document_id": document_id,
                                "document_type_id": document_type_id,
                                "field_id": field_id,
                                "field": headers.get(cell["ColumnIndex"]),
                                "is_missing": cell.get("IsMissing", False),
                                "field_value": first_value.get("Value"),
                                "field_unformatted_value": first_value.get(
                                    "UnformattedValue"
                                ),
                                "confidence": first_value.get("Confidence"),
                                "ocr_confidence": first_value.get("OcrConfidence"),
                                "operator_confirmed": first_value.get(
                                    "OperatorConfirmed"
                                ),
                                "is_correct": (
                                    first_value.get("DataSource") != "ManuallyChanged"
                                ),
                                "row_index": cell["RowIndex"],  # Adding RowIndex
                                "column_index": cell[
                                    "ColumnIndex"
                                ],  # Adding ColumnIndex
                            }

                            # Insert each cell's data into the database
                            columns = ", ".join(row_data.keys())
                            placeholders = ", ".join(["?"] * len(row_data))
                            sql = f"INSERT INTO 'extraction' ({columns}) VALUES ({placeholders})"
                            self.cursor.execute(sql, list(row_data.values()))

    def update_validated_field_data(self):
        document_id = self.validation_results["result"]["validatedExtractionResults"][
            "DocumentId"
        ]

        # Iterate through each field in the validatedExtractionResults
        for field in self.validation_results["result"]["validatedExtractionResults"][
            "ResultsDocument"
        ]["Fields"]:
            field_id = field.get("FieldId")
            operator_confirmed = field.get("OperatorConfirmed")
            validated_value = (
                field.get("Values", [{}])[0].get("Value", None)
                if field.get("Values")
                else None
            )

            # Determine is_correct based on the DataSource
            if field.get("DataSource") in {"ManuallyChanged", "Manual"}:
                is_correct = False
            else:
                is_correct = True

            # Update the validated_field_value in the database for the corresponding DocumentId and FieldId
            sql = """
                UPDATE extraction
                SET validated_field_value = ?, operator_confirmed = ?, is_correct = ?
                WHERE document_id = ? AND field_id = ?
            """
            self.cursor.execute(
                sql,
                (
                    validated_value,
                    operator_confirmed,
                    is_correct,
                    document_id,
                    field_id,
                ),
            )

    def update_validated_table_data(self):
        document_id = self.validation_results["result"]["validatedExtractionResults"][
            "DocumentId"
        ]

        # Retrieve tables from validatedExtractionResults
        tables = (
            self.validation_results["result"]
            .get("validatedExtractionResults", {})
            .get("ResultsDocument", {})
            .get("Tables", [])
        )
        if tables:
            for table in tables:
                headers_lookup = self.create_headers_lookup_dict([table])
                field_id = table["FieldId"]
                headers = headers_lookup.get(field_id, {})

                # Iterate over each row in the table
                for value in table["Values"]:
                    for cell in value["Cells"]:
                        # Only process non-header rows
                        if cell["RowIndex"] != 0 and not cell["IsHeader"]:
                            cell_values = cell.get("Values", [{}])
                            first_value = cell_values[0] if cell_values else {}

                            # Get validated_field_value and other relevant data
                            validated_field_value = first_value.get("Value", None)
                            operator_confirmed = cell.get("OperatorConfirmed")
                            is_correct = cell.get("DataSource") not in {"ManuallyChanged", "Manual"}

                            # Map to the appropriate database field name for the cell's column
                            field_name = headers.get(cell["ColumnIndex"])
                            if field_name is None:
                                print(
                                    f"Warning: Column index {cell['ColumnIndex']} not found in headers."
                                )
                                continue  # Skip if field name is not found

                            # Execute a separate update for each cell to ensure accurate row-by-row updates
                            sql = """
                                UPDATE extraction
                                SET validated_field_value = ?, operator_confirmed = ?, is_correct = ?
                                WHERE document_id = ? AND field_id = ? AND field = ? AND row_index = ? AND column_index = ?
                            """
                            # Execute the update with the prepared data
                            self.cursor.execute(
                                sql,
                                (
                                    validated_field_value,
                                    operator_confirmed,
                                    is_correct,
                                    document_id,
                                    field_id,
                                    field_name,
                                    cell["RowIndex"],  # Unique row index
                                    cell["ColumnIndex"],  # Unique column index
                                ),
                            )

    def write_extraction_results(self):
        self.insert_field_data()
        self.insert_table_data()

    def write_validated_results(self):
        self.update_validated_field_data()
        self.update_validated_table_data()

    def export_query_to_csv(self):
        """
        Exports the result of an SQLite query to a CSV file.
        The CSV file is named after the 'filename' column in the query.

        Raises:
            ValueError: If the query doesn't return rows for the specified filename.
        """
        try:
            query = """
                SELECT filename, field_id, field, is_missing, field_value,
                    field_unformatted_value, confidence, ocr_confidence
                FROM extraction
                WHERE filename = ?;
            """

            # Execute the query with self.filename as a parameter
            self.cursor.execute(query, (self.filename,))
            rows = self.cursor.fetchall()
            column_names = [description[0] for description in self.cursor.description]

            # Check if rows are returned
            if not rows:
                raise ValueError(f"No rows returned for filename '{self.filename}'.")

            # Generate a CSV file name based on self.filename
            csv_filename = os.path.basename(self.filename)  # Strip any path components
            csv_filename = (
                os.path.splitext(csv_filename)[0] + ".csv"
            )  # Ensure a .csv extension

            # Define the output path
            output_dir = "output_results"
            os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists
            csv_filepath = os.path.join(output_dir, csv_filename)

            # Write the query results to the CSV file
            with open(csv_filepath, mode="w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(column_names)  # Write the header
                writer.writerows(rows)  # Write the data

            print(f"Data exported to {csv_filepath}")
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
        except ValueError as e:
            print(f"ValueError: {e}")

    def write_results(self):
        try:
            # Write regular and validated results
            if self.extraction_results:
                self.write_extraction_results()
            if self.validation_results:
                self.write_validated_results()

            self.export_query_to_csv()
            # Commit once after all data is written
            self.conn.commit()

        except Exception as e:
            print(f"An error occurred: {e}")
            self.conn.rollback()  # Rollback in case of error
        finally:
            # Close the connection after all operations
            self.conn.close()
