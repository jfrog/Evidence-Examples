# Create Evidence inside ServiceNow and upload it into Artifactory
ServiceNow offers multiple processes in which a user would benefit from creating a JFrog evidence. 
For example, following a release approval step, i.e., approval to promote a release bundle or a package, approval to deploy a new version or to distribute a release version.

These approval flows, being completed on ServiceNow, trigger operations inside JFrog, but without generating the evidence on ServiceNow, the release operations may not be backtracked for compliance or verified by automated controls.

This example demonstrates how to create evidence in ServiceNow and upload them into Artifactory.

For integrating ServiceNow with JFrog, we will add a few ServiceNow components that can then be used as building blocks in any ServiceNow process that requires JFrog evidence. 

Notice, throughout the example scripts referencing the added components will use the x_1560608_jfrog_1 app id which should be replaced with your own app id. 

## Example of a ServiceNow business rule 
The business rule in this example is planned to be triggered following a ServiceNow change request approval for a promotion request.
The script promotes a release bundle and creates evidence of the promotion approval.

business rule script example is on [jfrog_promotion](jfrog_promotion) 
Notice this script requires the below mandatory and optional ServiceNow entities to be created.
Notice that a few elements were not added here, for example, the notification and the event registry (eventQueue) that handle the business rules failures (as these are async and so cannot be handled through the UI).
While for other scenarios you might only need to create the mandatory components that perform evidence creation, signing and uploading, this business rule script performs a full process of promotion and evidence creation and so requires also few optional elements.

## Mandatory ServiceNow components required for the integration:
### 1. Script includes:
- **CryptoJS**: see [CryptoJS](CryptoJS) adds Cryptographic functions to servicenow, based on https://github.com/kjur/jsrsasign (MIT License).
- **JFrogEvidenceOperations**: see [JFrogEvidenceOperations](JFrogEvidenceOperations) which uses the CryptoJS for signing operations and adds few other evidence related utilities such as base64 handling and evidence creation. the main function is Create_evidence function.
  - Create_evidence function input parameters: 
    - jfrog_platform_url: the JFrog platform url (for example mycompany.jfrog.io)
    - jfrog_evidence_pkey: private key content that is used for the signing 
    - jfrog_keyid: optional, the JFrog name of the public key that was uploaded to jfrog, if missing JFRog signature verification will not be performed  
    - jfrog_bearer: JFrog bearer token
    - evidence_subject: the digest of the evidence subject, this may be the digest of a release bundle, a package, a buildinfo or any other JFrog artifact that the evidence is related to. 
    - evidence_payload: predicate of the evidence, it is advised to create a system property with evidence templates that can be used for generating this content.
  - result json:
    ```json
    {
            success: status,
            http_status: create_evidence_http_status,
            response_obj: create_evidence_response_obj
    }
    ```
-  

### 2. Outbound Integrations > Rest Messages
- **JFrog_evidence**: an outbound rest api for posting evidence to JFrog.
  - **Rest message Endpoint**: `https://$jfrog_platform_url.jfrog.io`
  - **HTTP Method**: create_evidence
  - ***Endpoint***: POST `https://${jfrog_platform_url}/evidence/api/v1/subject/${project}-release-bundles-v2/${release_name}/${release_number}/release-bundle.json.evd`
  - **Request Body**: 
    ```json
    {
    "payload": "${payload}",
    "payloadType": "application/vnd.in-toto+json",
    "signatures": [
        {
            "keyid": "${keyid}",
            "sig": "${signature}"
        }
    ]
    } 
    ```
    

## Optional ServiceNow components required for the integration:
### 1. Script includes:
- **JFrogReleaseOperations** see [JFrogReleaseOperations](JFrogReleaseOperations) provides functions for getting a release bundle digest and for promoting a release bundle.
### 2. Outbound Integrations > Rest Msssages
- **JFrog_rb**: an outbound rest api for working with JFrog Release bundle .
  - **Rest message Endpoint**: `https://${jfrog_platform_url}.jfrog.io/lifecycle/`
  - **HTTP Method**: promote
  - ***Endpoint***: POST `${jfrog_platform_url}/lifecycle/api/v2/promotion/records/my-rb/1.0.1`
  - **Query Parameters**: 
    - ***name***: project ***Value*** : ${project} 
    - ***name***: async ***Value*** : false
  - **Request Body**: 
    ```json
    {
    "environment": "${env}",
    "included_repository_keys": [],
    "excluded_repository_keys": []
    }
    ```
    
- **JFrog_rb**: an outbound rest api for working with JFrog storage, in our example, it is used for getting a release bundle digest.
  - **Rest message Endpoint**: `https://${jfrog_platform_url}//artifactory/api/storage`
  - **HTTP Method**: get_release_info
  - ***Endpoint***: GET `https://${jfrog_platform_url}/artifactory/api/storage/${project}-release-bundles-v2/${release_name}/${release_number}/release-bundle.json.evd`
  - **Query Parameters**: 
    - ***name***: project ***Value*** : ${project} 
    - ***name***: async ***Value*** : false
  - **Request Body**: 
    ```json
    {
    "environment": "${env}",
    "included_repository_keys": [],
    "excluded_repository_keys": []
    }
    ```
### 3. system properties:
- ***jfrog_bearer***: JFrog bearer token, property of type password2
- ***jfrog_evidence_pkey***: private key used for signing service now evidence, property of type password2
- ***jfrog_platform_url***: JFrog platform url, property of type string
- ***JFrog_evidence_keyid***: JFrog public key id, property of type string
- ***\<evidence type->evidence-template***: a system property that holds template for evidence predicate content, this can be used for managing and generating the evidence payload.
