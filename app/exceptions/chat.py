class ChatError(Exception):
    pass

class ChatNotFoundException(ChatError):
    pass

class ChatAccessDeniedException(ChatError):
    pass

class ChatParticipantNotFoundException(ChatError):
    pass

class InvalidChatParticipantException(ChatError):
    pass
