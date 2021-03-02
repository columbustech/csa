from django.db import models

class CSAJob(models.Model):
    uid = models.CharField(max_length=20, primary_key=True)
    job_name = models.CharField(max_length=50)
    stage = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    long_status = models.CharField(max_length=500)
