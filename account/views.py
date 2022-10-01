from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Profile, Contact
from .forms import LoginForm, UserRegistrationForm, UserEditForm, ProfileEditForm
from actions.utils import create_action
from actions.models import Action
# Create your views here.

"""
When the user submits the form via POST, the following actions are performed:
• The form is instantiated with the submitted data with form = LoginForm(request.POST). • The form is validated with form.is_valid(). If it is not valid, the form errors will be displayed 
later in the template (for example, if the user didn’t fill in one of the fields).
• If the submitted data is valid, the user gets authenticated against the database using the 
authenticate() method. This method takes the request object, the username, and the password
parameters and returns the User object if the user has been successfully authenticated, or 
None otherwise. If the user has not been successfully authenticated, a raw HttpResponse is 
returned with an Invalid login message.
• If the user is successfully authenticated, the user status is checked by accessing the is_active
attribute. This is an attribute of Django’s User model. If the user is not active, an HttpResponse
is returned with a Disabled account message.
• If the user is active, the user is logged into the site. The user is set in the session by calling the 
login() method. An Authenticated successfully message is returned.
"""

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request, username=cd['username'], password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponse('Authenticated successfully')
                else:
                    return HttpResponse('Account disabled')
            else:
                return HttpResponse('Invalid Login')
    else:
        form = LoginForm()
        
    return render(request, 'account/login.html', {'form': form})

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            # Create a new user object but avoid saving yet
            new_user = user_form.save(commit=False)
            # Set the choosen password
            new_user.set_password(user_form.cleaned_data['password'])
            # Save the User object
            new_user.save()
            
            # Create the user profile

            Profile.objects.create(user=new_user)
            # Use actions. Chapter 7, p306
            create_action(new_user, "created account")
            return render(request, 'account/register_done.html', { 'new_user': new_user})
    else:
        user_form = UserRegistrationForm()
    return render(request, 'account/register.html', {'user_form': user_form})


@login_required
def dashboard(request):
    #Chapter 7, p307 displaying the activity stream
    actions = Action.objects.exclude(user=request.user)
    following_ids = request.user.following.values_list('id', flat=True)
    if following_ids:
        # if user is following others, retrieve only their actions
        actions = actions.filter(user_id__in=following_ids)
    # Using select_related()
    '''
    The select_related method is for ForeignKey
    and OneToOne fields. It works by performing a SQL JOIN and including the fields of the related object 
    in the SELECT statement.
    '''
    '''
    You use user__profile to join the Profile table in a single SQL query. If you call select_related()
    without passing any arguments to it, it will retrieve objects from all ForeignKey relationships. Always 
    limit select_related() to the relationships that will be accessed afterward.
    '''

    '''
    Django offers a different QuerySet method called 
    prefetch_related that works for many-to-many and many-to-one relationships in addition to the 
    relationships supported by select_related(). The prefetch_related() method performs a separate lookup for each relationship and joins the results using Python. This method also supports the 
    prefetching of GenericRelation and GenericForeignKey.
    '''
    actions = actions.select_related('user', 'user__profile')[:10].prefetch_related('target')[:10]

    return render(request, 'account/dashboard.html', {'section': 'dashboard', 'actions': actions})

@login_required
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance= request.user, data=request.POST)
        profile_form = ProfileEditForm(instance=request.user.profile, data=request.POST, files=request.FILES)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
        else:
            messages.error(request, 'Update profile failed!')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
    
    return render(request, 'account/edit.html', {'user_form': user_form, 'profile_form': profile_form})

# Chapter 7

@login_required
def user_list(request):
    users = User.objects.filter(is_active=True)
    return render(request, 'account/user/list.html', {'section': 'people', 'users': users})

@login_required
def user_detail(request, username):
    user = get_object_or_404(User, username=username, is_active=True )
    print(user)

    return render(request, 'account/user/detail.html', {'section': 'people', 'user': user})

@login_required
@require_POST
# Same logic as image_like
def user_follow(request):
    user_id = request.POST.get('id')
    action = request.POST.get('action')

    if user_id and action:
        try:
            user = User.objects.get(id=user_id)
            if action == 'follow':
                Contact.objects.get_or_create(user_from=request.user, user_to=user)
                create_action(request.user, "is_following", user)
            else:
                Contact.objects.filter(user_from=request.user, user_to=user).delete()
            return JsonResponse({'status': 'ok'})
        except User.DoesNotExist:
            return JsonResponse({'status': 'error'})
    return JsonResponse({'status': 'error'})