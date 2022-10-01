from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Image
'''
First, you register the users_like_changed function as a receiver function using the receiver() decorator. You attach it to the m2m_changed signal. Then, you connect the function to Image.users_like.
through so that the function is only called if the m2m_changed signal has been launched by this sender. 
There is an alternate method for registering a receiver function; it consists of using the connect()
method of the Signal object.
'''

@receiver(m2m_changed, sender=Image.users_like.through)

def users_like_changed(sender, instance, **kwargs):
    instance.total_likes = instance.users_like.count()
    instance.save()

