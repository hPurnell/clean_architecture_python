from litestar.dto import DataclassDTO, DTOConfig

from app.items.domain import Item


class ItemDTO(DataclassDTO[Item]):
    config = DTOConfig(rename_strategy="pascal")


class NewItemDTO(DataclassDTO[Item]):
    config = DTOConfig(
        exclude={"id", "created_date", "modified_date"}, rename_strategy="pascal"
    )


class UpdateItemDTO(DataclassDTO[Item]):
    # The timestamps are the store's own, not a caller's to send.
    config = DTOConfig(
        exclude={"created_date", "modified_date"},
        rename_strategy="pascal",
    )
