"""RFC 7636: Proof Key for Code Exchange by OAuth Public Clients

OAuth 2.0 public clients utilizing the Authorization Code Grant are
susceptible to the authorization code interception attack.  This
specification describes the attack as well as a technique to mitigate
against the threat through the use of Proof Key for Code Exchange
(PKCE, pronounced "pixy").

https://www.rfc-editor.org/info/rfc7636/
"""

import base64
import enum
import hashlib
import secrets


class CodeChallengeMethod(enum.StrEnum):
    """PKCE Code Challenge Method

    https://www.rfc-editor.org/info/rfc7636/#section-6.2
    https://www.iana.org/assignments/oauth-parameters/oauth-parameters.xhtml#pkce-code-challenge-method
    """

    PLAIN = "plain"
    S256 = "S256"


def create_code_challenge(
    code_verifier: str, code_challenge_method=CodeChallengeMethod.S256
):
    """Create a code challenge for the associated code verifier and code challenge method.

    https://www.rfc-editor.org/info/rfc7636/#section-4.2
    """
    match code_challenge_method:
        case CodeChallengeMethod.PLAIN:
            return code_verifier
        case CodeChallengeMethod.S256:
            return (
                base64.urlsafe_b64encode(
                    hashlib.sha256(code_verifier.encode()).digest()
                )
                .decode()
                .rstrip("=")
            )
        case _:
            raise RuntimeError(
                f"{code_challenge_method=} must be one of: {','.join(CodeChallengeMethod)}"
            )


def verify_code_verifier(
    code_verifier: str,
    code_challenge: str,
    code_challenge_method=CodeChallengeMethod.S256,
):
    """Verify a PKCE code verifier and code challenge using a "constant-time compare".

    https://www.rfc-editor.org/info/rfc7636/#section-4.6
    """
    return secrets.compare_digest(
        create_code_challenge(code_verifier, code_challenge_method),
        code_challenge,
    )
