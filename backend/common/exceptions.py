from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    if isinstance(exc, IntegrityError):
        return Response(
            {"detail": "The request conflicts with existing data."},
            status=status.HTTP_409_CONFLICT,
        )
    return drf_exception_handler(exc, context)
