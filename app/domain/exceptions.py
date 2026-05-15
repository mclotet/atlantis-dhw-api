class DhwDomainError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class InfluxUnavailable(DhwDomainError): ...
class InfluxQueryError(DhwDomainError): ...
