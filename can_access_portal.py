"""Simple portal access check per user specification.

Checks in order:
 - user is authenticated
 - user's role is in portal's allowed_roles
 - portal is not locked

Returns True only if all checks pass.

Note: This implementation assumes the caller provides the expected dict shapes
and will raise KeyError if keys are missing. This matches the minimal
implementation requested.
"""

def can_access_portal(user, portal):
    if not user["authenticated"]:
        return False
    if user["role"] not in portal["allowed_roles"]:
        return False
    if portal["locked"]:
        return False
    return True
