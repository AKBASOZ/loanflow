*** Settings ***
Library    RequestsLibrary
Library    Collections
Library    ../libraries/loanflow_keywords.py


*** Variables ***
${APPLICATION_API_BASE_URL}    http://127.0.0.1:8000


*** Keywords ***
Create Application Api Session
    Create Session    application_api    ${APPLICATION_API_BASE_URL}

Create Loan Application
    [Arguments]    ${payload}
    ${response}=    POST On Session
    ...    application_api
    ...    /applications
    ...    json=${payload}
    RETURN    ${response}

Get Application By Id
    [Arguments]    ${application_id}
    ${response}=    GET On Session
    ...    application_api
    ...    /applications/${application_id}
    RETURN    ${response}

List Applications
    ${response}=    GET On Session
    ...    application_api
    ...    /applications
    RETURN    ${response}

List Applications By Status
    [Arguments]    ${status}
    ${params}=    Create Dictionary    status=${status}
    ${response}=    GET On Session
    ...    application_api
    ...    /applications
    ...    params=${params}
    RETURN    ${response}

Response Status Should Be
    [Arguments]    ${response}    ${expected_status_code}
    Should Be Equal As Integers    ${response.status_code}    ${expected_status_code}

Response Json Should Contain
    [Arguments]    ${response}    ${key}    ${expected_value}
    ${body}=    Evaluate    $response.json()
    Dictionary Should Contain Key    ${body}    ${key}
    Should Be Equal    ${body}[${key}]    ${expected_value}

Get Response Json
    [Arguments]    ${response}
    ${body}=    Evaluate    $response.json()
    RETURN    ${body}

Extract Application Id
    [Arguments]    ${response}
    ${body}=    Evaluate    $response.json()
    RETURN    ${body}[id]