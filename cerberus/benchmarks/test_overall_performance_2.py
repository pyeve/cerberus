import json
from collections import Counter
from pathlib import Path
from typing import Callable, Dict, List
from typing import Counter as CounterType

from cerberus import TypeDefinition, Validator

from cerberus.benchmarks.schemas.overalll_schema_2 import group_schema, product_schema
from cerberus.benchmarks import DOCUMENTS_PATH

def init_validator_1():
    class TestValidator(Validator):
        types_mapping = {
            **Validator.types_mapping,
            "path": TypeDefinition("path", (Path,), ()),
        }

    return TestValidator(product_schema, purge_unknown=True)


def load_documents_1():
  f = open(DOCUMENTS_PATH + 'data.json',   'r')
  documents = json.load(f)
  return documents


def validate_documents(init_validator: Callable, documents: List[dict]) -> None:
    doc_count = failed_count = 0
    error_paths: CounterType[tuple] = Counter()
    validator = init_validator()

    def count_errors(errors):
        if errors is None:
            return
        for error in errors:
            if error.is_group_error:
                count_errors(error.child_errors)
            else:
                error_paths[error.schema_path] += 1

    for document in documents:
        if validator.validated(document) is None:
            failed_count += 1
            count_errors(validator._errors)
        doc_count += 1

    print(
        f"{failed_count} out of {doc_count} documents failed with "
        f"{len(error_paths)} different error leafs."
    )
    print("Top 3 errors, excluding container errors:")
    for path, count in error_paths.most_common(3):
        print(f"{count}: {path}")


def test_overall_performance(benchmark):
    benchmark.pedantic(
        validate_documents, (init_validator_1, load_documents_1()), rounds=1
    )

