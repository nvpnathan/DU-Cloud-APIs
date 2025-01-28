import os
import concurrent.futures
from config import (
    load_prompts,
    ProcessingConfig,
    DocumentProcessingContext,
)
from write_results import WriteResults


class DocumentProcessor:
    def __init__(
        self, digitize_client, classify_client, extract_client, validate_client
    ):
        self.digitize_client = digitize_client
        self.classify_client = classify_client
        self.extract_client = extract_client
        self.validate_client = validate_client

    def process_document(
        self,
        document_path: str,
        config: ProcessingConfig,
        context: DocumentProcessingContext,
    ) -> None:
        """Process a document using the provided configuration and context."""
        try:
            document_id = self.start_digitization(document_path)

            # Perform classification if required
            document_type_id = (
                self.classify_document(document_id, document_path, config, context)
                if config.perform_classification
                else None
            )

            # Perform extraction if required
            if config.perform_extraction:
                extractor_id, extractor_name = self.get_extractor(
                    context, document_type_id
                )
                if extractor_id and extractor_name:
                    self.perform_extraction(
                        document_id,
                        document_path,
                        extractor_id,
                        extractor_name,
                        config,
                        context,
                    )

        except Exception as e:
            print(f"Error processing {document_path}: {e}")

    def start_digitization(self, document_path: str) -> str:
        return self.digitize_client.digitize(document_path)

    def classify_document(
        self,
        document_id: str,
        document_path: str,
        config: ProcessingConfig,
        context: DocumentProcessingContext,
    ) -> str | None:
        classification_prompts = (
            load_prompts("classification")
            if context.classifier == "generative_classifier"
            else None
        )
        document_type_id = self.classify_client.classify_document(
            document_path,
            document_id,
            context.classifier,
            classification_prompts,
            config.validate_classification,
        )
        if config.validate_classification:
            document_type_id = self.validate_client.validate_classification_results(
                document_id,
                context.classifier,
                document_type_id,
                classification_prompts,
            )
        return document_type_id

    def get_extractor(
        self, context: DocumentProcessingContext, document_type_id: str | None
    ) -> tuple[str | None, str | None]:
        if document_type_id:
            extractor_id = context.extractor_dict.get(document_type_id, {}).get("id")
            extractor_name = context.extractor_dict.get(document_type_id, {}).get(
                "name"
            )
        else:
            extractor_info = next(iter(context.extractor_dict.values()))
            extractor_id = extractor_info.get("id")
            extractor_name = extractor_info.get("name")

        print(
            f"Using extractor: {extractor_id}, {extractor_name} for document type {document_type_id}"
        )
        return extractor_id, extractor_name

    def perform_extraction(
        self,
        document_id: str,
        document_path: str,
        extractor_id: str,
        extractor_name: str,
        config: ProcessingConfig,
        context: DocumentProcessingContext,
    ) -> None:
        extraction_prompts = (
            load_prompts(extractor_name)
            if context.project_id == "00000000-0000-0000-0000-000000000001"
            else None
        )
        extraction_results = self.extract_client.extract_document(
            extractor_id, document_id, extraction_prompts
        )
        self.write_extraction_results(extraction_results, document_path)

        if config.validate_extraction:
            validated_results = self.validate_client.validate_extraction_results(
                extractor_id, document_id, extraction_results, extraction_prompts
            )
            if validated_results:
                self.write_validated_results(
                    validated_results, extraction_results, document_path
                )

    def write_extraction_results(self, extraction_results, document_path):
        write_results = WriteResults(
            document_path=document_path, extraction_results=extraction_results
        )
        write_results.write_results()

    def write_validated_results(
        self, validated_results, extraction_results, document_path
    ):
        write_results = WriteResults(
            document_path=document_path,
            extraction_results=extraction_results,
            validation_extraction_results=validated_results,
        )
        write_results.write_results()

    def process_documents_in_folder(
        self,
        folder_path: str,
        config: ProcessingConfig,
        context: DocumentProcessingContext,
    ) -> None:
        """Process all documents in the specified folder."""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []

            for filename in os.listdir(folder_path):
                if filename.lower().endswith((".png", ".jpg", ".jpeg", ".pdf", ".tif")):
                    document_path = os.path.join(folder_path, filename)
                    print(f"Submitting document for processing: {document_path}")
                    futures.append(
                        executor.submit(
                            self.process_document,
                            document_path,
                            config,
                            context,
                        )
                    )

            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error in thread execution: {e}")
