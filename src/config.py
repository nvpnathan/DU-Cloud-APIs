class ProcessingConfig:
    def __init__(
        self,
        validate_classification=False,
        validate_extraction=False,
        perform_classification=True,
        perform_extraction=True,
    ):
        self.validate_classification = validate_classification
        self.validate_extraction = validate_extraction
        self.perform_classification = perform_classification
        self.perform_extraction = perform_extraction


class DocumentProcessingContext:
    def __init__(self, project_id, classifier=None, extractor_dict=None):
        self.project_id = project_id
        self.classifier = classifier
        self.extractor_dict = extractor_dict
