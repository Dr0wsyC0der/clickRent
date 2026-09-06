class PropertyImageError(Exception):
    pass

class PropertyImageNotFoundException(PropertyImageError):
    pass

class PropertyImageCreateException(PropertyImageError):
    pass