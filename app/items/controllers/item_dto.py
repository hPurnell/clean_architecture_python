from litestar.dto import DataclassDTO, DTOConfig

from app.items.domain import Item


class ItemDTO(DataclassDTO[Item]):
    config = DTOConfig(rename_strategy="pascal")


class NewItemDTO(DataclassDTO[Item]):
    config = DTOConfig(
        exclude={"id", "created_date", "modified_date"}, rename_strategy="pascal"
    )


class UpdateItemDTO(DataclassDTO[Item]):
    config = DTOConfig(
        rename_strategy="pascal",
    )
