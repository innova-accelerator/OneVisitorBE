from django.db import models
from django.conf import settings
import uuid
from datetime import date
from datetime import datetime

def upload_visitor_file(instance, filename):
	return "%s%s" %("Visitor/file/",filename)


class Site(models.Model):
    name            = models.CharField(max_length=500, default="")
    tenantId        = models.CharField(max_length=500, default="")
    url             = models.CharField(max_length=500, default="", blank=True, null = True)
    urlType         = models.CharField(max_length=500, default="", blank=True, null = True)
    published       = models.BooleanField(default=False)


    logo            = models.CharField(max_length=500, default="", blank=True, null = True)
    favicon         = models.CharField(max_length=500, default="", blank=True, null = True)
    primaryColor    = models.CharField(max_length=50, default="", blank=True, null = True)
    secondaryColor  = models.CharField(max_length=50, default="", blank=True, null = True)


    welcomeMessage  = models.TextField(default="", blank=True, null = True)
    language        = models.CharField(max_length=50, default="", blank=True, null = True)
    lastPublished   = models.DateTimeField(null=True, blank=True)
    timezoneOffset  =models.CharField(max_length=50, default="", blank=True, null=True)
    visitorTypes    = models.JSONField(default=list)
    formFields      = models.JSONField(default=list)
    
    def save(self, *args, **kwargs):
        """Auto-update lastPublished when site is published"""
        if self.pk:  # This is an update
            try:
                old_instance = Site.objects.get(pk=self.pk)
                if not old_instance.published and self.published:
                    self.lastPublished = datetime.now(pytz.UTC)
            except Site.DoesNotExist:
                pass
        else:  # This is a create
            if self.published:
                self.lastPublished = datetime.now(pytz.UTC)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class Host(models.Model):
	name  			=models.CharField(max_length=500, default="")
	email  			=models.CharField(max_length=500, default="")
	phone  			=models.CharField(max_length=500, default="")
	department  	=models.CharField(max_length=500, default="")
	site 			=models.ForeignKey(Site, on_delete=models.CASCADE, related_name="host")

	def __str__(self):
		return self.name


class Visitor(models.Model):
	company   			=models.CharField(max_length=500, default="")
	email   			=models.CharField(max_length=500, default="")
	expectedDuration  	=models.CharField(max_length=50, default="")
	host   				=models.ForeignKey(Host, on_delete=models.CASCADE, related_name="visitor")
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

