from tortoise import fields
from tortoise.models import Model


class Users(Model):
    id = fields.BigIntField(pk=True)
    is_subscribed = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    subscribes: fields.ReverseRelation["Subscribes"]


class Subscribes(Model):
    id = fields.BigIntField(pk=True)
    user = fields.ForeignKeyField("models.Users", related_name="subscribes")
    crypto = fields.CharField(max_length=255)
    is_subscribed = fields.BooleanField(default=True)

    class Meta:
        unique_together = (("user", "crypto"),)