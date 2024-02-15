import csv
import os


class ResultPrinter:
    @staticmethod
    def print_extraction_results(extraction_results):
        field_data = {}

        for field in extraction_results['extractionResult']['ResultsDocument']['Fields']:
            if isinstance(field, dict):  # Ensure 'field' is a dictionary
                field_name = field.get('FieldName')
                values = [value.get('Value') for value in field.get('Values', [])]

                confidence = None
                if 'Values' in field and field['Values'] and 'Confidence' in field['Values'][0]:
                    confidence = field['Values'][0]['Confidence']
                if field_name:
                    field_data[field_name] = {'values': values, 'Confidence': confidence}

        # Print parsed data
        print("Extraction Results: \n")
        for field_name, data in field_data.items():
            values = data['values']
            confidence = data.get('Confidence')
            print(f"{field_name}: {values}, Confidence: {confidence}")


class CSVWriter:
    @staticmethod
    def write_extraction_results_to_csv(extraction_results, document_path):
        fields_to_extract = ['FieldName', 'Value', 'Confidence', 'OcrConfidence', 'IsMissing']

        # Extract file name without extension
        file_name = os.path.splitext(os.path.basename(document_path))[0]

        # Construct output file name with .csv extension
        output_file = file_name + '.csv'

        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields_to_extract)
            writer.writeheader()

            for field in extraction_results['extractionResult']['ResultsDocument']['Fields']:
                if 'Values' in field and field['Values']:
                    field_data = {
                        'FieldName': field['FieldName'],
                        'Value': field['Values'][0]['Value'],
                        'Confidence': field['Values'][0].get('Confidence', ''),
                        'OcrConfidence': field['Values'][0].get('OcrConfidence', ''),
                        'IsMissing': field['IsMissing']
                    }
                    writer.writerow(field_data)
                else:
                    # Handle case where Values is empty or None
                    field_data = {
                        'FieldName': field['FieldName'],
                        'Value': '',
                        'Confidence': '',
                        'OcrConfidence': '',
                        'IsMissing': field['IsMissing']
                    }
                    writer.writerow(field_data)
