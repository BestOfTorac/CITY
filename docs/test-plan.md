# CITY - Test Plan

## Functional tests

| ID | Test | Expected result |
|---|---|---|
| T1 | Manual report without image | Workflow reaches 100%, DynamoDB record created |
| T2 | Manual report with image | Image uploaded to S3, Rekognition executed, workflow reaches 100% |
| T3 | Camera test | Random dataset image selected, IoT rule triggers lambdaIngestion |
| T4 | Severe emergency | SNS notification sent |
| T5 | Non-severe emergency | SNS notification skipped |
| T6 | WebSocket disconnected | Workflow continues anyway |
| T7 | Invalid report | App receives invalid emergency status |
| T8 | Archive failure | App receives image archive failure status |

## Metrics to collect

- API response time
- time to 50%
- time to 100%
- Step Functions duration
- Rekognition duration
- success rate
- number of DynamoDB records
- number of archived images
- SNS notification status

## Test sequence

```text
1. Deploy all CloudFormation stacks.
2. Confirm SNS email subscription.
3. Upload dataset images to S3 dataset/.
4. Configure Android endpoints locally.
5. Run manual report without image.
6. Run manual report with image.
7. Run camera simulation test.
8. Check DynamoDB, S3, Step Functions and CloudWatch logs.
```
