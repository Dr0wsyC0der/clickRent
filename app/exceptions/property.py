class PropertyError(Exception):
    pass

class PropertyAlreadyExistsException(PropertyError):
    pass

class PropertyNotFoundException(PropertyError):
    pass

class PropertyAccessDeniedException(PropertyError):
    pass