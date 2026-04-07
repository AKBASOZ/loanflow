*** Settings ***
Resource  api.resource
Library  Collections
Library  ../libraries/loanflow_keywords.py

*** Keywords ***
Prepare Test Environment
  Create Application Api Session

Reset Test State
  Reset Application Api State
  Reset Risk Engine Mock
  Reset Notification Mock

Configure Risk Engine For Approval
  Configure Risk Engine Mock  85  approve  0

Configure Risk Engine For Rejection
  Configure Risk Engine Mock  20  reject  0

Configure Risk Engine For Manual Review
  Configure Risk Engine Mock  50  manual_review  0

Configure Risk Engine For Timeout
  Configure Risk Engine Mock  50  manual_review  6

Application Should Be Approved
  [Arguments]  ${response}
  Response Status Should Be  ${response}  201
  ${body}=  Get Response Json  ${response}
  Should Be Equal  ${body}[status]  approved
  Should Be Equal As Integers  ${body}[risk_score]  85
  Should Be Equal  ${body}[decision_reason]  Meets auto-approval threshold

Application Should Be Rejected
  [Arguments]  ${response}
  Response Status Should Be  ${response}  201
  ${body}=  Get Response Json  ${response}
  Should Be Equal  ${body}[status]  rejected

Application Should Be Pending
  [Arguments]  ${response}
  Response Status Should Be  ${response}  201
  ${body}=  Get Response Json  ${response}
  Should Be Equal  ${body}[status]  pending
  Should Be Equal As Integers  ${body}[risk_score]  50

Application Should Be Error
  [Arguments]  ${response}
  Response Status Should Be  ${response}  201
  ${body}=  Get Response Json  ${response}
  Should Be Equal  ${body}[status]  error
  Should Be True  $body["risk_score"] is None

Validation Error Should Be Returned
  [Arguments]  ${response}
  Should Be True  ${response.status_code} >= 400

Latest Notification Should Have Status
  [Arguments]  ${expected_status}
  ${notifications_response}=  Get Notifications
  Should Have Notification For Status  ${notifications_response}  ${expected_status}

Create Standard Application Payload
  ${payload}=  Generate Application Payload
  RETURN  ${payload}

Create Boundary Approval Payload
  ${payload}=  Generate Application Payload  annual_income=40000  requested_amount=20000  employment_status=employed
  RETURN  ${payload}

Create Invalid Amount Payload
  ${payload}=  Generate Application Payload  requested_amount=500
  RETURN  ${payload}

Create Unemployed High Amount Payload
  ${payload}=  Generate Application Payload  annual_income=30000  requested_amount=15000  employment_status=unemployed
  RETURN  ${payload}

Create Idempotent Payload
  [Arguments]  ${applicant_name}
  ${payload}=  Generate Application Payload  applicant_name=${applicant_name}  annual_income=65000  requested_amount=25000  employment_status=employed
  RETURN  ${payload}