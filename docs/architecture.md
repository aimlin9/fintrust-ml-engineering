# ML Workflow — Architecture

Data → Validation → Preprocessing → Feature Preparation → Model → Prediction → Output → Testing

## Data
The pipeline receives the raw transaction and customer records from the
FinTrust CSV sources. Transaction records contain the information to be
assessed, while customer records provide additional information linked
through `Customer_ID`.

## Validation
The pipeline checks that incoming records match the expected schema
before processing them: required fields, data types, valid values and
ranges, and the `Customer_ID` relationship between transaction and
customer data.

## Preprocessing
Valid records are cleaned and standardised: missing `Device_Type` and
`Location` values are handled, `Transaction_DateTime` is parsed
consistently, and categorical fields are encoded.

## Feature Preparation
The pipeline joins customer and transaction data on `Customer_ID`, then
selects the fields marked `Modelling_Use: Yes` in the data dictionary.
A transaction whose `Customer_ID` has no matching customer record is a
data-quality case (see `risks.md`), not something that passes through
silently.

## Model
The trained predictive model receives the prepared feature set and
produces the risk-related prediction. The model itself is owned by the
Data Science track; ML Engineering integrates it and provides the
correct inputs. Until a trained model is delivered, this stage uses a
mock interface with the same contract (see `src/model/model_interface.py`).

## Prediction
The integrated model generates a prediction for the individual
transaction, including a probability where supported.

## Output
The raw model response is converted into a consistent downstream
format: `Transaction_ID`, `Customer_ID`, `risk_review_prediction`,
`risk_review_probability`.

## Testing
The complete workflow is tested from input to output, including valid
records, missing `Device_Type`/`Location` values, invalid data types,
missing required fields, unmatched `Customer_ID` values, and
model/service failures.
