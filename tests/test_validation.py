import pytest
from pydantic import ValidationError

from app.schemas.ingest import IngestRequest


def test_ingest_request_rejects_empty_records():
    with pytest.raises(ValidationError):
        IngestRequest.model_validate({"records": []})


def test_ingest_request_rejects_wrong_dtype_for_numeric_field():
    with pytest.raises(ValidationError):
        IngestRequest.model_validate(
            {
                "records": [
                    {
                        "customer_id": "cust-1",
                        "age": "34",
                        "annual_income": 72000.0,
                        "debt_to_income": 0.31,
                        "credit_utilization": 0.42,
                        "num_open_accounts": 5,
                        "delinquency_count": 1,
                        "loan_amount": 12000.0,
                        "employment_years": 6.0,
                    }
                ]
            }
        )
