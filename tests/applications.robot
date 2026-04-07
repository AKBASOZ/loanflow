*** Settings ***
Resource  ../resources/api.resource
Resource  ../resources/common.resource
Suite Setup  Prepare Test Environment
Test Setup  Reset Test State

*** Test Cases ***
Auto Approve Application At Exact Boundary
  [Documentation]  Approves when risk_score >= 70 and income-to-loan ratio >= 2.0.
  Configure Risk Engine Mock  70  approve  0
  ${payload}=  Create Boundary Approval Payload
  ${response}=  Create Loan Application  ${payload}
  Response Status Should Be  ${response}  201
  ${body}=  Get Response Json  ${response}
  Should Be Equal  ${body}[status]  approved
  Should Be Equal As Integers  ${body}[risk_score]  70
  Should Be Equal  ${body}[decision_reason]  Meets auto-approval threshold
  Latest Notification Should Have Status  approved

Reject Invalid Requested Amount
  [Documentation]  Returns validation error when requested_amount is below minimum.
  Configure Risk Engine For Approval
  ${payload}=  Create Invalid Amount Payload
  ${response}=  Create Loan Application  ${payload}
  Should Be True  ${response.status_code} >= 400

Reject Unemployed Applicant Above 10000
  [Documentation]  Rejects when employment_status is unemployed and requested_amount > 10000.
  Configure Risk Engine Mock  85  approve  0
  ${payload}=  Create Unemployed High Amount Payload
  ${response}=  Create Loan Application  ${payload}
  Response Status Should Be  ${response}  201
  ${body}=  Get Response Json  ${response}
  Should Be Equal  ${body}[status]  rejected
  Should Be Equal As Integers  ${body}[risk_score]  85
  Should Be Equal  ${body}[decision_reason]  Unemployed applicant requesting more than 10000
  Latest Notification Should Have Status  rejected

Risk Engine Timeout Sets Error Status
  [Documentation]  Sets status error and risk_score null when Risk Engine exceeds 5 seconds.
  Configure Risk Engine For Timeout
  ${payload}=  Create Standard Application Payload
  ${response}=  Create Loan Application  ${payload}
  Response Status Should Be  ${response}  201
  ${body}=  Get Response Json  ${response}
  Should Be Equal  ${body}[status]  error
  Should Be True  $body["risk_score"] is None
  Should Be Equal  ${body}[decision_reason]  Risk Engine timeout or unavailable
  Latest Notification Should Have Status  error

Duplicate Submission Returns Existing Application
  [Documentation]  Returns the same application for same name and amount within idempotency window.
  Configure Risk Engine For Approval
  ${payload}=  Create Idempotent Payload  Maria Same
  ${first_response}=  Create Loan Application  ${payload}
  ${second_response}=  Create Loan Application  ${payload}
  Response Status Should Be  ${first_response}  201
  Response Status Should Be  ${second_response}  201
  ${first_id}=  Extract Application Id  ${first_response}
  ${second_id}=  Extract Application Id  ${second_response}
  Should Be Same Application Id  ${first_id}  ${second_id}
  ${list_response}=  List Applications
  ${applications}=  Get Response Json  ${list_response}
  Length Should Be  ${applications}  1