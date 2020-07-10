import unicodedata


def generate_username(email):
    # Using Python 3 and Django 1.11, usernames can contain alphanumeric
    # (ascii and unicode), _, @, +, . and - characters. So we normalize
    # it and slice at 150 characters.
    # Temporarily hardcode this, because the email isn't passed in the scope yet
    return unicodedata.normalize("NFKC", email)[:150]
