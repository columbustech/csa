from rest_framework import serializers
from .models import CSAJob

class CSAJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSAJob
        fields = '__all__'
