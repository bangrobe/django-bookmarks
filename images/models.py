from dataclasses import field
from email.policy import default
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils.text import slugify


# Create your models here.
class Image(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='images_created', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    url = models.URLField(max_length=250)
    image = models.ImageField(upload_to='images/%Y/%m/%d/')
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    users_like = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='images_liked', blank=True)
    # Chapter 7 - denormalizing counts
    total_likes = models.PositiveIntegerField(default=0)

    class Meta:
        #https://docs.djangoproject.com/en/4.1/ref/models/options/#django.db.models.Options.indexes
        indexes = [
            models.Index(fields=['-created']),
            models.Index(fields=['-total_likes'])
        ]
        ordering = ['-created']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    # common pattern for providing canonical URLs for objects is to define a get_
    #absolute_url() method in the model.
    def get_absolute_url(self):
        return reverse("images:detail", args=[self.id, self.slug])
    
    
    def __str__(self) -> str:
        return self.title