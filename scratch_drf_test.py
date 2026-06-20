import os
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=[
        'rest_framework',
    ]
)
django.setup()

from rest_framework import serializers

class TestCaseSerializer(serializers.Serializer):
    input = serializers.CharField(allow_blank=True, default="")

s = TestCaseSerializer(data={"input": ["10", "20"]})
print("is_valid:", s.is_valid())
if s.is_valid():
    print("validated_data:", s.validated_data)
else:
    print("errors:", s.errors)
