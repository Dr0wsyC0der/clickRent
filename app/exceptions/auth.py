class AuthError(Exception):
    default_message = "Ошибка аутентификации."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.default_message)

class EmailAlreadyExistsException(AuthError):
    default_message = "Пользователь с таким email уже существует."

class UsernameAlreadyExistsException(AuthError):
    default_message = "Пользователь с таким именем уже существует."

class InvalidCredentialsException(AuthError):
    default_message = "Неверные учетные данные или недействительный токен."

class RefreshTokenRevokedException(AuthError):
    default_message = "Refresh-токен отозван."

class RefreshTokenExpiredException(AuthError):
    default_message = "Срок действия refresh-токена истек."

class InvalidRefreshTokenException(AuthError):
    default_message = "Недействительный refresh-токен."

class AdminAccessDeniedException(AuthError):
    default_message = "Действие доступно только администратору."

class AccessDeniedException(AuthError):
    default_message = "Действие доступно только владельцам недвижимости."

class InactiveUserException(AuthError):
    default_message = "Учетная запись деактивирована."
