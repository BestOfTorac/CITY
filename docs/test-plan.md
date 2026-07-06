# CITY â€” Test Plan

## Functional tests

| ID | Test | Expected result |
|---|---|---|
| T1 | Manual report without image | Workflow reaches 100%, DynamoDB record created |
| T2 | Manual report with image | Image uploaded to S3, Rekognition executed, workflow reaches 100% |
| T3 | Camera test | Random dataset image selected, IoT rule triggers lambdaIngestion |
| T4 | Severe emergency | SNS notification sent |
| T5 | Non-severe emergency | SNS notification skipped |
| T6 | WebSocket disconnected | Workflow continues anyway |
| T7 | Invalid report | App receives INVALID_EMERGENCY |
| T8 | Archive failure | App receives IMAGE_ARCHIVE_FAILED |

## Metrics to collect

- API response time
- Time to 50%
- Time to 100%
- Step Functions duration
- Rekognition duration
- Success rate
- Number of DynamoDB records
- Number of archived images
- SNS notification status
