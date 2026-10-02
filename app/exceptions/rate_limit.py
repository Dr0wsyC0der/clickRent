class RateLimitExceededException(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Слишком много запросов. Повторите попытку через {retry_after} сек.")
