import sqlite3
import time
from datetime import datetime, timedelta
from typing import Any, Optional
from project_config import SQLITE_DB_PATH, CACHE_EXPIRY_DAYS


def execute_query(query: str, params: tuple = ()) -> list[Any]:
    """Execute an SQL query and return results."""
    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def update_document_stage(
    action: str,
    document_id: str,
    new_stage: str,
    operation_id: str,
    duration: Optional[float] = None,
    classifier_id: Optional[str] = None,
    extractor_id: Optional[str] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    """Update the stage of a document."""
    operation_id_column = f"{action}_operation_id"
    duration_column = f"{action}_duration"

    query = f"""
        UPDATE documents
        SET stage = ?, {operation_id_column} = ?, error_code = ?, error_message = ?
    """
    params = [new_stage, operation_id, error_code, error_message]

    if duration is not None:
        query += f", {duration_column} = ?"
        params.append(duration)

    if classifier_id is not None:
        query += ", classifier_id = ?"
        params.append(classifier_id)

    if extractor_id is not None:
        query += ", extractor_id = ?"
        params.append(extractor_id)

    query += " WHERE document_id = ?"
    params.append(document_id)

    execute_query(query, tuple(params))


def insert_classification_results(
    document_id: str,
    filename: str,
    document_type_id: str,
    classification_confidence: float,
    start_page: int,
    page_count: int,
    classifier_name: str,
    operation_id: str,
) -> None:
    """Insert classification results into the database."""
    query = """
        INSERT INTO classification (document_id, filename, document_type_id, classification_confidence,
                                     start_page, page_count, classifier_name, operation_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        document_id,
        filename,
        document_type_id,
        classification_confidence,
        start_page,
        page_count,
        classifier_name,
        operation_id,
    )
    execute_query(query, params)


def get_document_id_from_cache(filename: str) -> Optional[str]:
    """Retrieve the document_id based on the filename."""
    query = "SELECT document_id, timestamp FROM documents WHERE filename = ?"
    result = execute_query(query, (filename,))
    if result:
        document_id, timestamp = result[0]
        cache_time = datetime.fromtimestamp(timestamp)
        if datetime.now() - cache_time > timedelta(days=CACHE_EXPIRY_DAYS):
            return None
        return document_id
    return None


def update_cache(
    filename: str,
    document_id: Optional[str],
    stage: str,
    project_id: Optional[str] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    """Insert or update the document cache."""
    timestamp = time.time()
    query_update = """
        UPDATE documents
        SET document_id = ?, stage = ?, timestamp = ?, project_id = ?, error_code = ?, error_message = ?
        WHERE filename = ?
    """
    params_update = (
        document_id,
        stage,
        timestamp,
        project_id,
        error_code,
        error_message,
        filename,
    )

    query_insert = """
        INSERT INTO documents (document_id, filename, stage, timestamp, project_id, error_code, error_message)
        SELECT ?, ?, ?, ?, ?, ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM documents WHERE filename = ?
        )
    """
    params_insert = (
        document_id,
        filename,
        stage,
        timestamp,
        project_id,
        error_code,
        error_message,
        filename,
    )

    execute_query(query_update, params_update)
    execute_query(query_insert, params_insert)
