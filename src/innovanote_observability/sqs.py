"""Submódulo público para uso explícito de SQS:

>>> from innovanote_observability import sqs
>>> sqs.publish(queue_url, {"foo": "bar"})

Re-exporta os helpers de :mod:`.sqs_helpers` num namespace dedicado, deixando
o uso mais explícito ("``sqs.publish``" vs "``publish``") sem precisar trocar
``boto3.client('sqs').send_message`` por algo opaco.
"""

from __future__ import annotations

from innovanote_observability.sqs_helpers import publish, sqs_message_context

__all__ = ["publish", "sqs_message_context"]
