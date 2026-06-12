"""DRF serializer fields backed by UniRate.

* :class:`CurrencyCodeField` — a ``CharField`` that normalises ISO-4217
  codes to upper-case and (optionally) validates them against the live list
  of supported currencies.
* :class:`ConvertedAmountField` — a read-only field that converts a model's
  monetary amount into a target currency on the fly, using the latest rate.
"""

from __future__ import annotations

from typing import Any, ClassVar

from rest_framework import serializers

from rest_framework_unirate.client import get_accessor

_CODE_LENGTH = 3


def _resolve(instance: Any, name: str) -> Any:
    """Read ``name`` from a model instance or a mapping."""
    if isinstance(instance, dict):
        return instance[name]
    return getattr(instance, name)


class CurrencyCodeField(serializers.CharField):
    """A currency-code field that upper-cases input and validates length.

    Set ``validate_supported=True`` to additionally check the code against
    the live ``/api/currencies`` list (one cached network call). It is off
    by default so deserialization stays offline unless you opt in.
    """

    default_error_messages: ClassVar[dict[str, str]] = {
        "invalid_length": "Currency codes must be {length} letters (e.g. 'USD').",
        "not_supported": "'{code}' is not a supported currency.",
    }

    def __init__(self, *, validate_supported: bool = False, **kwargs: Any) -> None:
        self.validate_supported = validate_supported
        kwargs.setdefault("max_length", _CODE_LENGTH)
        kwargs.setdefault("min_length", _CODE_LENGTH)
        kwargs.setdefault("trim_whitespace", True)
        super().__init__(**kwargs)

    def to_internal_value(self, data: Any) -> str:
        value = super().to_internal_value(data).upper()
        if len(value) != _CODE_LENGTH or not value.isalpha():
            self.fail("invalid_length", length=_CODE_LENGTH)
        if self.validate_supported:
            if value not in get_accessor().get_supported_currencies():
                self.fail("not_supported", code=value)
        return value


class ConvertedAmountField(serializers.Field):
    """Read-only field that converts an amount into a target currency.

    The field reads the *whole* parent instance, so it can combine a source
    amount with a sibling currency field and serialize the converted value::

        class ProductSerializer(serializers.ModelSerializer):
            price_eur = ConvertedAmountField(
                amount_field="price",
                from_currency_field="currency",
                to_currency="EUR",
            )

    ``to_currency`` may be omitted to take the target from the serializer
    context key ``target_currency`` instead (useful for per-request targets).
    """

    def __init__(
        self,
        *,
        amount_field: str,
        to_currency: str | None = None,
        from_currency: str | None = None,
        from_currency_field: str | None = None,
        rounding: int | None = 2,
        **kwargs: Any,
    ) -> None:
        if from_currency is None and from_currency_field is None:
            msg = "Provide either 'from_currency' or 'from_currency_field'."
            raise ValueError(msg)
        self.amount_field = amount_field
        self.to_currency = to_currency.upper() if to_currency else None
        self.from_currency = from_currency.upper() if from_currency else None
        self.from_currency_field = from_currency_field
        self.rounding = rounding
        kwargs["read_only"] = True
        kwargs.setdefault("source", "*")
        super().__init__(**kwargs)

    def to_representation(self, value: Any) -> float:
        amount = float(_resolve(value, self.amount_field))
        if self.from_currency is not None:
            source = self.from_currency
        else:
            assert self.from_currency_field is not None
            source = str(_resolve(value, self.from_currency_field)).upper()
        target = self._target_currency()
        converted = get_accessor().convert(source, target, amount)
        if self.rounding is not None:
            return round(converted, self.rounding)
        return converted

    def to_internal_value(self, data: Any) -> Any:  # pragma: no cover - read only
        msg = "ConvertedAmountField is read-only."
        raise NotImplementedError(msg)

    def _target_currency(self) -> str:
        if self.to_currency is not None:
            return self.to_currency
        target = (self.context or {}).get("target_currency")
        if not target:
            msg = (
                "ConvertedAmountField needs a 'to_currency' argument or a "
                "'target_currency' key in the serializer context."
            )
            raise serializers.ValidationError(msg)
        return str(target).upper()


__all__ = [
    "ConvertedAmountField",
    "CurrencyCodeField",
]
