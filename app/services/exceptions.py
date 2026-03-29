class SiteLimitExceeded(Exception):
    pass


class SiteAlreadyExists(Exception):
    pass

class SiteNotFound(Exception):
    pass

class UserAlreadyExists(Exception):
    pass

class InvalidCredentials(Exception):
    pass

class EmailNotConfirmed(Exception):
    pass

class InvalidToken(Exception):
    pass

class TokenExpired(Exception):
    pass

class InvalidRefreshToken(Exception):
    pass

class UserInactive(Exception):
    pass

class InvalidLogoutToken(Exception):
    pass