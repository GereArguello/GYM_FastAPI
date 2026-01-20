from enum import Enum


class StatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class ProductType(str, Enum):
    MONEY = "money"
    POINTS = "points"