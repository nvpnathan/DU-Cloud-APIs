import csv
import os


class CSVWriter:
    @staticmethod
    def write_extraction_results_to_csv(
        extraction_results, document_path, output_directory
    ):
        fields_to_extract = [
            "FieldName",
            "Value",
            "OcrConfidence",
            "Confidence",
            "IsMissing",
        ]

        # Extract file name without extension
        file_name = os.path.splitext(os.path.basename(document_path))[0]

        # Construct output directory path
        output_dir_path = os.path.join(os.getcwd(), output_directory)

        # Check if the output directory exists, if not, create it
        if not os.path.exists(output_dir_path):
            os.makedirs(output_dir_path)

        # Construct output file path with .csv extension
        output_file = os.path.join(output_dir_path, file_name + ".csv")

        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            # Initialize an empty list for fieldnames
            fieldnames = fields_to_extract.copy()

            # Check if a table exists
            table_exists = any(
                field.get("FieldName") == "items"
                for field in extraction_results["extractionResult"]["ResultsDocument"][
                    "Fields"
                ]
            )

            # If a table exists, extract table headers and append them to fieldnames
            if table_exists:
                table_data = next(
                    (
                        field
                        for field in extraction_results["extractionResult"][
                            "ResultsDocument"
                        ]["Fields"]
                        if field.get("FieldName") == "items"
                    ),
                    None,
                )
                if table_data:
                    headers_dict = extract_table_data(table_data)
                    index = len(fieldnames)
                    for key in headers_dict:
                        fieldnames.insert(index, key)
                        fieldnames.insert(index + 1, f"{key}_IsMissing")
                        index += 2

            # Initialize csv.DictWriter with dynamic fieldnames
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            # Write regular fields to the CSV
            for field in extraction_results["extractionResult"]["ResultsDocument"][
                "Fields"
            ]:
                if "Values" in field and field["Values"]:
                    field_data = {
                        "FieldName": field["FieldName"],
                        "Value": field["Values"][0]["Value"],
                        "Confidence": field["Values"][0].get("Confidence", ""),
                        "OcrConfidence": field["Values"][0].get("OcrConfidence", ""),
                        "IsMissing": field["IsMissing"],
                    }
                    writer.writerow(field_data)

            if table_exists:
                num_rows = max(
                    len(value["Values"]) for value in headers_dict.values()
                )  # Get the maximum number of rows

                for i in range(num_rows):
                    # Create a dictionary for each row with values from headers_dict
                    row_data = {}

                    for key, value in headers_dict.items():
                        # Check if the current row index is within the range of values list for this key
                        if i < len(value["Values"]):
                            row_data[key] = value["Values"][i]
                            # Add IsMissing column
                            row_data[f"{key}_IsMissing"] = value["IsMissing"][i]
                        else:
                            # If the value list is exhausted, fill with empty string and set IsMissing as True
                            row_data[key] = ""
                            row_data[f"{key}_IsMissing"] = True

                    # Write row_data to CSV
                    writer.writerow(row_data)

    @staticmethod
    def write_validated_results_to_csv(
        validated_results, extraction_results, document_path, output_directory
    ):
        # Extract file name without extension
        file_name = os.path.splitext(os.path.basename(document_path))[0]

        # Construct output directory path
        output_dir_path = os.path.join(os.getcwd(), output_directory)

        # Check if the output directory exists, if not, create it
        if not os.path.exists(output_dir_path):
            os.makedirs(output_dir_path)

        # Construct output file path with .csv extension
        output_file = os.path.join(output_dir_path, file_name + ".csv")

        # Update the fieldnames to include new columns for validated results
        fields_to_extract = [
            "FieldName",
            "Value",
            "OcrConfidence",
            "Confidence",
            "IsMissing",
            "ActualValue",
            "OperatorConfirmed",
            "IsCorrect",
        ]

        # Write validated results to the same CSV file
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields_to_extract)
            writer.writeheader()

            # Compare validated data with extracted data and write to CSV
            for validated_field in validated_results["result"][
                "validatedExtractionResults"
            ]["ResultsDocument"]["Fields"]:
                validated_value = None
                operator_confirmed = None

                if "Values" in validated_field and validated_field["Values"]:
                    validated_value = validated_field["Values"][0]["Value"]
                    operator_confirmed = validated_field["OperatorConfirmed"]

                # Find corresponding field in extraction results
                extraction_field = next(
                    (
                        field
                        for field in extraction_results["extractionResult"][
                            "ResultsDocument"
                        ]["Fields"]
                        if field["FieldName"] == validated_field["FieldName"]
                    ),
                    None,
                )

                if extraction_field:
                    extracted_value = None
                    confidence = None
                    ocr_confidence = None
                    is_missing = None

                    if "Values" in extraction_field and extraction_field["Values"]:
                        extracted_value = extraction_field["Values"][0].get("Value")
                        confidence = extraction_field["Values"][0].get("Confidence")
                        ocr_confidence = extraction_field["Values"][0].get(
                            "OcrConfidence"
                        )
                        is_missing = extraction_field.get("IsMissing")

                    # Compare ValidatedValue with ExtractedValue to determine correctness
                    is_correct = (
                        validated_value is None and extracted_value is None
                    ) or validated_value == extracted_value
                    field_data = {
                        "FieldName": validated_field["FieldName"],
                        "Value": extracted_value,
                        "Confidence": confidence,
                        "OcrConfidence": ocr_confidence,
                        "IsMissing": is_missing,
                        "ActualValue": validated_value,
                        "OperatorConfirmed": operator_confirmed,
                        "IsCorrect": is_correct,
                    }
                else:
                    # If no corresponding field found in extraction results
                    field_data = {
                        "FieldName": validated_field["FieldName"],
                        "Value": None,
                        "Confidence": None,
                        "OcrConfidence": None,
                        "IsMissing": None,
                        "ActualValue": validated_value,
                        "OperatorConfirmed": operator_confirmed,
                        "IsCorrect": True,
                    }
                writer.writerow(field_data)

    @staticmethod
    def pprint_csv_results(document_path, output_directory):
        # Extract file name without extension
        file_name = os.path.splitext(os.path.basename(document_path))[0]

        # Construct output directory path
        output_dir_path = os.path.join(os.getcwd(), output_directory)

        # Construct output file path with .csv extension
        output_file = os.path.join(output_dir_path, file_name + ".csv")

        with open(output_file, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            headers = reader.fieldnames
            max_widths = {header: len(header) for header in headers}

            rows = []
            for row in reader:
                rows.append(row)
                for header in headers:
                    max_widths[header] = max(max_widths[header], len(row[header]))

            # Print headers
            header_format = "|".join(
                ["{:<{}}".format(header, max_widths[header]) for header in headers]
            )
            print(header_format)
            print("-" * len(header_format))

            # Print rows
            for row in rows:
                row_format = "|".join(
                    [
                        "{:<{}}".format(row[header], max_widths[header])
                        for header in headers
                    ]
                )
                print(row_format)


def extract_table_data(table_data):
    # Extract headers
    headers_dict = {
        component["FieldName"]: {"IsMissing": [], "Values": []}
        for field in table_data["Values"][0]["Components"]
        if field.get("FieldId") == "items.Header"
        for component in field["Values"][0]["Components"]
    }

    # Extract data rows
    for field in table_data["Values"][0]["Components"]:
        if field.get("FieldId") == "items.Body":
            for line in field["Values"]:
                for component in line["Components"]:
                    header_name = component["FieldName"]
                    value = (
                        component["Values"][0]["Value"] if component["Values"] else ""
                    )
                    is_missing = bool(component["IsMissing"])
                    headers_dict[header_name]["Values"].append(value)
                    headers_dict[header_name]["IsMissing"].append(is_missing)

    return headers_dict
