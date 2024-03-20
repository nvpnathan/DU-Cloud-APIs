import csv
import os
import json


@staticmethod
def write_extraction_results_to_csv():

    with open("extractionResults.json", "r") as results:
        extraction_results = json.load(results)

    fields_to_extract = [
        "FieldName",
        "Value",
        "OcrConfidence",
        "Confidence",
        "IsMissing",
    ]

    # Extract file name without extension
    file_name = os.path.splitext(os.path.basename("invoice.pdf"))[0]

    # Construct output directory path
    output_dir_path = os.path.join(os.getcwd(), "./")

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
                index = len(fieldnames)  # Insert at the end of the original fieldnames
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
        print(headers_dict)
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


def extract_table_data(table_data):
    # Extract headers
    headers = [
        component["FieldName"]
        for field in table_data["Values"][0]["Components"]
        if field.get("FieldId") == "items.Header"
        for component in field["Values"][0]["Components"]
    ]
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
    # print(headers_dict)
    return headers_dict


@staticmethod
def pprint_csv_results(document_path="invoice.pdf", output_directory="./"):
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
                ["{:<{}}".format(row[header], max_widths[header]) for header in headers]
            )
            print(row_format)


write_extraction_results_to_csv()

pprint_csv_results()
