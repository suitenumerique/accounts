"""RFC 7636: Proof Key for Code Exchange by OAuth Public Clients

OAuth 2.0 public clients utilizing the Authorization Code Grant are
susceptible to the authorization code interception attack.  This
specification describes the attack as well as a technique to mitigate
against the threat through the use of Proof Key for Code Exchange
(PKCE, pronounced "pixy").

https://www.rfc-editor.org/info/rfc7636/
"""

import base64
import collections
import enum
import hashlib
import secrets

from core.standards import rfc3986


class CodeChallengeMethod(enum.StrEnum):
    """PKCE Code Challenge Method

    https://www.rfc-editor.org/info/rfc7636/#section-6.2
    https://www.iana.org/assignments/oauth-parameters/oauth-parameters.xhtml#pkce-code-challenge-method
    """

    PLAIN = "plain"
    S256 = "S256"


CodePair = collections.namedtuple("CodePair", ["verifier", "challenge"])


def create_code_pair(code_challenge_method=CodeChallengeMethod.S256, *, length=None):
    """Create a code verifier and its associated code challenge using a code challenge method"""
    code_verifier = create_code_verifier(length=length)
    return CodePair(
        verifier=code_verifier,
        challenge=create_code_challenge(code_verifier, code_challenge_method),
    )


def create_code_verifier(*, length=None):
    """Create a suitable code verifier

    https://www.rfc-editor.org/info/rfc7636/#section-4.1
    """
    length = (
        length or 43
    )  # Follow the RFC recommandation for suitable random number generator
    if not 43 <= length <= 128:
        raise ValueError("A code_verifier length must be between 43 and 128")
    return "".join(secrets.choice(rfc3986.UNRESERVED_CHARACTERS) for _ in range(length))


def create_code_challenge(
    code_verifier: str, code_challenge_method=CodeChallengeMethod.S256
):
    """Create the code challenge for a given code verifier using the chosen code challenge method.

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
                .rstrip(b"=")
                .decode()
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
