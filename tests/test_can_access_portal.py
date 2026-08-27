from can_access_portal import can_access_portal


def test_allowed_role_and_unlocked():
    user = {"authenticated": True, "role": "admin"}
    portal = {"locked": False, "allowed_roles": ["admin", "staff"]}
    assert can_access_portal(user, portal) is True


def test_not_authenticated():
    user = {"authenticated": False, "role": "admin"}
    portal = {"locked": False, "allowed_roles": ["admin"]}
    assert can_access_portal(user, portal) is False


def test_wrong_role():
    user = {"authenticated": True, "role": "guest"}
    portal = {"locked": False, "allowed_roles": ["admin", "staff"]}
    assert can_access_portal(user, portal) is False


def test_locked_portal():
    user = {"authenticated": True, "role": "admin"}
    portal = {"locked": True, "allowed_roles": ["admin"]}
    assert can_access_portal(user, portal) is False
