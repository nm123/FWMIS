def is_valid_email(email):
    """
    Validate email address with comprehensive checks
    """
    if not email or not isinstance(email, str):
        return False

    email = email.strip()
    if not email:
        return False

    import re

    # More comprehensive email regex pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    # Basic format check
    if not re.match(pattern, email):
        return False

    # Additional checks
    if email.count("@") != 1:
        return False

    local_part, domain_part = email.split("@")

    # Local part checks
    if not local_part or len(local_part) > 64:
        return False

    # Domain part checks
    if not domain_part or len(domain_part) > 253:
        return False

    # Check for consecutive dots
    if ".." in email:
        return False

    # Check that domain has at least one dot
    if "." not in domain_part:
        return False

    return True
