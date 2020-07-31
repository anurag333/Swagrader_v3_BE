from rest_framework import serializers
from .models import EmailNamespace

class EmailNamespaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailNamespace
        fields = ['namespace']
