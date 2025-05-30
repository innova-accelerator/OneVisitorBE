from django.db import models
from django.conf import settings
import uuid

def upload_visitor_file(instance, filename):
	return "%s%s" %("Visitor/file/",filename)

class Site(models.Model):
	name 			=models.CharField(max_length=500, default="")
	tenantId		=models.CharField(max_length=500, default="")
	url  			=models.CharField(max_length=500, default="")
	urlType 		=models.CharField(max_length=500, default="")
	published 		=models.BooleanField(default=False)

	logo  			=models.CharField(max_length=500, default="")
	favicon   		=models.CharField(max_length=500, default="")
	primaryColor  	=models.CharField(max_length=50, default="")
	secondaryColor 	=models.CharField(max_length=50, default="")


	welcomeMessage  =models.TextField(default="")
	language   		=models.CharField(max_length=50, default="")
	lastPublished   =models.DateField(auto_now_add=False)
	visitorTypes   	=models.JSONField(default=list)
	formFields   	=models.JSONField(default=list)

	def __str__(self):
		return self.name

class Visitor(models.Model):
	company   			=models.CharField(max_length=500, default="")
	email   			=models.CharField(max_length=500, default="")
	expectedDuration  	=models.CharField(max_length=50, default="")
	host   				=models.CharField(max_length=500, default="")
	name  				=models.CharField(max_length=500, default="")
	phone  				=models.CharField(max_length=500, default="")
	purpose   			=models.CharField(max_length=500, default="")
	signature   		=models.CharField(max_length=500, default="")
	visitorType   		=models.CharField(max_length=500, default="")
	site   				=models.ForeignKey(Site, on_delete=models.CASCADE, related_name="visitor")

	def __str__(self):
		return self.name

class visitorPhoto(models.Model):
	file 				=models.FileField(upload_to=upload_visitor_file)
	visitor 			=models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name="visitorPhoto")

