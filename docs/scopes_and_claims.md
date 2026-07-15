# Scopes and claims supported

## Table of contents

<!-- TOC -->
* [Scopes and claims supported](#scopes-and-claims-supported)
  * [Table of contents](#table-of-contents)
  * [OIDCValidator](#oidcvalidator)
  * [LaSuiteValidator](#lasuitevalidator)
<!-- TOC -->

## OIDCValidator

[Standard OpenID Connect claim](https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims):

| Scope   | Claim          | Implementation details                                           |
|---------|----------------|------------------------------------------------------------------|
| openid  | sub            | N/A                                                              |
| email   | email          | N/A                                                              |
| email   | email_verified | Always `false` as the project doesn't currently verify the email |
| profile | given_name     | N/A                                                              |
| profile | name           | N/A                                                              |


## LaSuiteValidator

Extend the `OIDCValidator` to add additional claims or modify standard ones.

| Scope        | Claim          | Type    | Description                                                                                 |
|--------------|----------------|---------|---------------------------------------------------------------------------------------------|
| email        | email_verified | boolean | True if _at least one_ of the End-User's identity provider `email_verified` claim is `true` |
| organization | siret          | string  | [SIRET](https://en.wikipedia.org/wiki/SIRET_code) of the End-User's organization            |

