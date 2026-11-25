def unique_emails(records: list[dict]) -> list[str]:
    """Return e-mails in first-seen order, without duplicates (records can be ~10^6)."""
    seen = []
    for record in records:
        email = record["email"].strip().lower()
        if email not in seen:
            seen.append(email)
    return seen
