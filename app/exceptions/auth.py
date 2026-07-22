class AuthError(Exception):
    pass

class EmailAlreadyExistsException(AuthError):
    pass

class UsernameAlreadyExistsException(AuthError):
    pass

class InvalidCredentialsException(AuthError):
    pass

class RefreshTokenRevokedException(AuthError):
    pass

class RefreshTokenExpiredException(AuthError):
    pass

class InvalidRefreshTokenException(AuthError):
    pass