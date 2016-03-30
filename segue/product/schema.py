from segue.schema import BaseSchema, Field


class ProductSchema(BaseSchema):
    id = Field.int(dump_only=True)
    kind = Field.str()
    category = Field.str()
    public = Field.bool()
    price = Field.decimal()
    sold_until = Field.date()
    description = Field.str()