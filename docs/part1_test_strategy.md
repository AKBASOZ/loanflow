# Part 1 — Test Analysis and Strategy

## 1. Context and Scope

LoanFlow is a microservices-based loan processing system with three components:
- Application API
- Risk Engine
- Notification Service

The primary system under test is the Application API.

This solution focuses on:
- clarifying vague acceptance criteria
- identifying testable areas
- proposing a deterministic mocking strategy
- defining a practical CI/CD pipeline approach
- automating the highest-risk API scenarios

## 2. Sharpened Acceptance Criteria

1. Given a valid application, when the Risk Engine returns a score greater than or equal to 70 and the income-to-loan ratio is greater than or equal to 2.0, then the application is created with status `approved`.

2. Given a valid application, when the Risk Engine returns a score below 30, then the application is created with status `rejected`.

3. Given a valid application, when `employment_status = unemployed` and `requested_amount > 10000`, then the application is created with status `rejected`.

4. Given a valid application, when the Risk Engine returns a score between 30 and 69 and no explicit rejection rule applies, then the application is created with status `pending`.

5. Given the Risk Engine does not respond within 5 seconds, then the application is handled as an error and `risk_score` is `null`.

6. Given the same applicant name and requested amount are submitted again within 60 seconds, then the existing application is returned instead of creating a duplicate.

7. Given invalid request data, then the API returns a validation error response.

## 3. Questions for the Product Owner

- What does 'accept' mean in the first criteria — does it mean the data arrived, or that it passed validation, or that it was scored and stored? These are three different things and all three could fail independently. If I send you a request with a negative income, did the system "accept" it?

- How do you define a valid vs invalid application? And what does processed mean exactly - scored, stored, both? In what order? 

- When you say rejected, do you mean HTTP 400 back to the caller with nothing saved, or do you mean the application is saved with status "rejected"? These are very different behaviours. A 400 means it never entered the system. A saved rejection means it is in the database with a decision attached.

- Should be used for scoring — what happens when it cannot be used? If the Risk Engine is down for some reason and someone submits an application, do we turn the applicant away with an error, or do we accept the application, save it, and score it later? Right now the architecture document says we save it with status "error" and a null score, but the API spec also lists 503 as a possible response. Which one is it?

- Notified when exactly the applicant — on every status change, or only when there is a final decision?

- What if the Notification Service itself is down when we try to send — does the application submission fail, do we retry in the background, or do we just log it and move on?

- What does gracefully mean in your mind for this system?
Because from a testing perspective, gracefully could mean: the API returns a structured error response instead of crashing. It could mean the application is never left in a broken half-saved state. It could mean the user always gets a human-readable message. It could mean the engineering team gets an alert. It probably means all of these — but I cannot write a test for "gracefully." I can write a test for "when the database is unavailable, the API returns 503 with error_code SERVICE_UNAVAILABLE and logs the exception."

## 4. Testable Areas and Decomposition

### Functional
- request validation
- decision logic
- idempotency
- retrieval by id
- list/filter by status

### Integration
- synchronous Risk Engine call
- asynchronous Notification Service callback

### Edge Cases
- threshold boundaries
- timeout handling
- duplicate submission
- invalid enums and numeric limits

### Non-Functional
- pipeline execution
- reliability/flakiness control
- audit-friendly evidence generation

## 5. Risk-Based Prioritization

Highest priority:
- AuthN/AuthZ (JSON WebToken validation, permissions)
- approval/rejection/pending decision logic
- validation
- timeout/error handling
- idempotency

Medium priority:
- get by id
- list applications
- notification verification

Lower priority for this challenge:
- broader non-functional depth
- performance/scalability
- persistence-level testing against a real database

## 6. Mocking / Service Virtualization Strategy

The Application API remains the primary system under test.

The Risk Engine will be replaced by a lightweight mock service that exposes the same interface and can be configured to return:
- high score for approval
- low score for rejection
- middle score for pending
- delayed response for timeout

The Notification Service will be replaced by a simple capture service that records incoming notifications for assertion.

This approach provides deterministic and repeatable automated tests without depending on unstable external environments.

## 7. CI/CD Pipeline Proposal

### Pull Request Pipeline
- install dependencies
- start local test services
- run critical automated API tests
- publish Robot test artifacts

### Main Branch Pipeline
- run full automated suite
- publish reports
- fail on critical regressions

### Nightly
- rerun full suite
- track flaky tests
- review trend metrics

### Flaky Test Handling
- do not silently ignore flaky tests
- tag and quarantine if needed
- create follow-up defect/task
- restore as pipeline gate only after root cause is fixed