# Technical Requirements

## Input Requirements
Transaction fields marked `Modelling_Use: Yes` in the data dictionary
(`Location`, `Device_Type`, `Channel`, `Amount_NGN`, `Transaction_Type`,
`Transaction_DateTime`, `Customer_ID`, `Transaction_ID`,
`Transaction_Status`, `International_Transaction`), plus `Customer_ID`
for the join to customer records.

## Output Requirements
A structured prediction per transaction: `Transaction_ID`,
`Customer_ID`, `risk_review_prediction`, `risk_review_probability`,
returned as a single structured record (JSON) per request.

## Preprocessing Requirements
- Missing `Device_Type` / `Location` → replace with `"Unknown"`, do not drop the transaction.
- `Transaction_DateTime` → parse into a consistent datetime; reject/flag unparseable records.
- Numerical fields → validate type and expected ranges before model processing.
- Categorical fields → encode using the same method/config used at training time.
- `Customer_ID` → validate before joining; never silently create a feature from an unmatched customer.
- Apply the same preprocessing sequence at inference as at training.

## Dependencies
- Trained model artifact + input interface from Data Science (mocked for now).
- Python: pandas, scikit-learn.
- FinTrust customer/transaction schemas.
- A defined service layer (model exposed via API).

## Testing Requirements
Valid records, missing Device_Type/Location, invalid data types,
missing required fields, unmatched Customer_ID, model/service failures.

## Version-Control Requirements
- Git holds source code, config templates, schemas, preprocessing code, tests, docs, API/service code.
- Raw data and trained model binaries are excluded (see `.gitignore`).
- `main` branch stable, feature branches for development.
- Model versions tracked separately from code versions; predictions record which model version produced them.
- Configuration kept separate from code (`configs/`).

## API/Service Requirements
Request/response API service. A client sends a transaction (+ Customer_ID)
to the service; the service validates, preprocesses, calls the model, and
returns the structured prediction.
