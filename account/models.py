from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_of_birth = models.DateField(blank=True, null=True)
    photo = models.ImageField(upload_to='users/%Y/%md/%d/', blank=True)

    def __str__(self) -> str:
        return f'Profile of {self.user.username}'

# Chapter 7
# Contact duoc goi la intermediary model
class Contact(models.Model):
    user_from = models.ForeignKey('auth.User', related_name='rel_from_set', on_delete=models.CASCADE)
    user_to = models.ForeignKey('auth.User', related_name='rel_to_set', on_delete=models.CASCADE)

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [ models.Index(fields=['-created'])]
        ordering = ['-created']
    

    def __str__(self) -> str:
        return f'{self.user_from} follows {self.user_to}' 

#Add following field to User dynamically (page 289)
# add_to_class is a way to avoid creating custom user model
user_model = get_user_model()
user_model.add_to_class('following', models.ManyToManyField('self', through=Contact, related_name='followers', symmetrical=False))