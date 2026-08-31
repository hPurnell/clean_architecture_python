from litestar.dto import DataclassDTO, DTOConfig

from app.items.domain import Item


class ItemDTO(DataclassDTO[Item]):
    config = DTOConfig(rename_strategy="pascal")


class NewItemDTO(DataclassDTO[Item]):
    config = DTOConfig(
        exclude={"id", "created_date", "modified_date"}, rename_strategy="pascal"
    )


class UpdateItemDTO(DataclassDTO[Item]):
    # The timestamps are the store's own: created_date records when the item
    # was first written and modified_date is stamped on every change, so
    # neither is a caller's to send. What is left is the id, which says which
    # item to change, and the values that are being changed.
    config = DTOConfig(
        exclude={"created_date", "modified_date"},
        rename_strategy="pascal",
    )
