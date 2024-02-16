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


    @staticmethod
    def write_validated_results_to_csv(validated_results, extraction_results, document_path):
        # Extract file name without extension
        file_name = os.path.splitext(os.path.basename(document_path))[0]

        # Construct output file name with .csv extension
        output_file = file_name + '.csv'

        # Update the fieldnames to include new columns for validated results
        fields_to_extract = ['FieldName', 'Value', 'Confidence', 'OcrConfidence', 'IsMissing',
                            'ActualValue', 'OperatorConfirmed', 'IsCorrect']

        # Write validated results to the same CSV file
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields_to_extract)
            writer.writeheader()

            # Compare validated data with extracted data and write to CSV
            for validated_field in validated_results['result']['validatedExtractionResults']['ResultsDocument']['Fields']:
                if 'Values' in validated_field and validated_field['Values']:
                    validated_value = validated_field['Values'][0]['Value']
                    operator_confirmed = validated_field['OperatorConfirmed']

                    # Find corresponding field in extraction results
                    extraction_field = next((field for field in extraction_results['extractionResult']['ResultsDocument']['Fields'] 
                                            if field['FieldName'] == validated_field['FieldName']), None)

                    if extraction_field:
                        extracted_value = extraction_field.get('Values', [{}])[0].get('Value')
                        confidence = extraction_field.get('Values', [{}])[0].get('Confidence')
                        ocr_confidence = extraction_field.get('Values', [{}])[0].get('OcrConfidence')
                        is_missing = extraction_field.get('IsMissing')
                    else:
                        extracted_value = None
                        confidence = None
                        ocr_confidence = None
                        is_missing = None

                    # Compare ValidatedValue with ExtractedValue to determine correctness
                    if validated_value is None and extracted_value is None:
                        is_correct = True
                    elif validated_value == extracted_value:
                        is_correct = True
                    else:
                        is_correct = False

                    field_data = {
                        'FieldName': validated_field['FieldName'],
                        'Value': extracted_value,
                        'Confidence': confidence,
                        'OcrConfidence': ocr_confidence,
                        'IsMissing': is_missing,
                        'ActualValue': validated_value,
                        'OperatorConfirmed': operator_confirmed,
                        'IsCorrect': is_correct
                    }
                    writer.writerow(field_data)
