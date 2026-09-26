# Technical Risks

| Risk | Why It May Matter | Mitigation |
|------|--------------------|------------|
| Static CSV input | The prototype may not represent a continuously operating banking data source. | Ingestion sits behind a clear interface so the CSV source can later be replaced by a database, batch source or streaming source. |
| Invalid input data | Incorrect types, malformed dates or missing required fields could cause unreliable predictions or pipeline failures. | Validate inputs before preprocessing; return explicit validation errors. |
| Model version mismatch | Pipeline code could send inputs using a feature structure that belongs to a different model version. | Track model versions separately from code; record the model version used per prediction. |
| Unmatched Customer_ID | The pipeline may be unable to correctly combine customer and transaction information. | Validate the customer lookup; reject or explicitly flag unmatched records rather than silently proceeding. |
| Data leakage | Information intended only for training (e.g. Risk_Review_Flag) could accidentally enter prediction-time inputs. | Separate target fields from inference features; validate the feature contract before each prediction. |
| Dependency on Data Science track | ML Engineering cannot fully integrate the real model until Data Science provides a usable artifact/interface. | Define the expected model contract early; use a mock model/interface (`src/model/model_interface.py`) while the real model is unavailable. |
