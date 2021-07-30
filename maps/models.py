from django.db import models
import geocoder
from django.conf import settings
# Create your models here.
class Hotel(models.Model):
	location = models.CharField(max_length =500,primary_key=True)
	longitude = models.FloatField(null =True,blank = True)
	latitude = models.FloatField(null =True,blank = True)
	

	def __str__(self):
		return self.location