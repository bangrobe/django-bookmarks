import datetime
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .models import Action

'''
The create_action() function allows you to create actions that optionally include a target object. 
You can use this function anywhere in your code as a shortcut to add new actions to the activity stream
'''

'''
You have changed the create_action() function to avoid saving duplicate actions and return a Boolean 
to tell you whether the action was saved. This is how you avoid duplicates:
1. First, you get the current time using the timezone.now() method provided by Django. This 
method does the same as datetime.datetime.now() but returns a timezone-aware object. 
Django provides a setting called USE_TZ to enable or disable timezone support. The default 
settings.py file created using the startproject command includes USE_TZ=True.
2. You use the last_minute variable to store the datetime from one minute ago and retrieve any 
identical actions performed by the user since then.
3. You create an Action object if no identical action already exists in the last minute. You return 
True if an Action object was created, or False otherwise.
'''
def create_action(user, verb, target=None):
    now = timezone.now() # (1)
    last_minute = now - datetime.timedelta(seconds=60) # (2)
    similar_actions = Action.objects.filter(user_id=user.id, verb=verb, created__gte=last_minute) # (3)
    if target:
        target_ct = ContentType.objects.get_for_model(target)
        similar_actions = similar_actions.filter(target_ct=target_ct, target_id=target.id)
    
    if not similar_actions:
        action = Action(user=user, verb=verb, target=target)
        action.save()
        return True
    return False