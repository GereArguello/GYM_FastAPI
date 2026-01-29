from fastapi_pagination import Params

class DefaultPagination(Params):
    page: int = 1
    size: int = 20
    max_size: int = 100

class ProductPagination(Params):
    page: int = 1
    size: int = 10
    max_size: int = 20
