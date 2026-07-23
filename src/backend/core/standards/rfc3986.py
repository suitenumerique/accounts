"""RFC 3986: Uniform Resource Identifier (URI): Generic Syntax

A Uniform Resource Identifier (URI) is a compact sequence of
characters that identifies an abstract or physical resource.  This
specification defines the generic URI syntax and a process for
resolving URI references that might be in relative form, along with
guidelines and security considerations for the use of URIs on the
Internet.  The URI syntax defines a grammar that is a superset of all
valid URIs, allowing an implementation to parse the common components
of a URI reference without knowing the scheme-specific requirements
of every possible identifier.  This specification does not define a
generative grammar for URIs; that task is performed by the individual
specifications of each URI scheme.

https://www.rfc-editor.org/info/rfc3986/
"""

import string

# https://www.rfc-editor.org/info/rfc3986/#section-2.2
GENERIC_DELIMITERS = ":/?#[]@"
SUBCOMPONENT_DELIMITERS = "!$&'()*+,;="
RESERVED_CHARACTERS = GENERIC_DELIMITERS + SUBCOMPONENT_DELIMITERS

# https://www.rfc-editor.org/info/rfc3986/#section-2.3
UNRESERVED_CHARACTERS = string.ascii_letters + string.digits + "-._~"
