from cProfile import label
import redis
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from .forms import ImageCreateForm
from .models import Image
#Chapter 7
from actions.utils import create_action

# Create your views here.

# Connect with redis
r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)

'''
This is how 
this view works:
1. Initial data has to be provided through a GET HTTP request in order to create an instance of 
the form. This data will consist of the url and title attributes of an image from an external 
website. Both parameters will be set in the GET request by the JavaScript bookmarklet that we 
will create later. For now, we can assume that this data will be available in the request.
2. When the form is submitted with a POST HTTP request, it is validated with form.is_valid(). 
If the form data is valid, a new Image instance is created by saving the form with form.
save(commit=False). The new instance is not saved to the database because of commit=False.
3. A relationship to the current user performing the request is added to the new Image instance 
with new_image.user = request.user. This is how we will know who uploaded each image.
4. The Image object is saved to the database.
5. Finally, a success message is created using the Django messaging framework and the user 
is redirected to the canonical URL of the new image. We havent yet implemented the get_
absolute_url() method of the Image model;
'''

@login_required
def image_create(request):
    if request.method == 'POST':
        form = ImageCreateForm(data=request.POST) # (2)
        if form.is_valid():                       # (2)
            cd = form.cleaned_data
            new_image = form.save(commit=False)   #2

            # assign current user to the item
            new_image.user = request.user         # (3)
            # save new image
            new_image.save()                      # (4)

            # use action (chapter 7, p.305)
            create_action(request.user,"bookmarked image", new_image)
            #Success message
            messages.success(request,'Image added successfully')  #(5)

            # Redirect to new created item detail view
            return redirect(new_image.get_absolute_url())
    else:
        # build form with data provided by the bookmarklet via GET
        form = ImageCreateForm(data=request.GET)
    return render(request, 'images/image/create/html', {'section': 'images', 'form': form})


def image_detail(request, id, slug):
    image = get_object_or_404(Image, id=id, slug=slug )
    
    # Chapter 7 - Count images view with redis
    # incr là hàm của redis, mang nghĩa increment. 
    # You store the value in the total_views variable and pass it into the template context. 
    # You build the Redis key using a notation such as object-type:id:field (for example, image:33:id)
    total_views = r.incr(f'image:{image.id}:views')

    # Storing a ranking in Redis

    r.zincrby('image_ranking',1,image.id)
    return render(request, 'images/image/detail.html', {'section': 'images', 'image': image, 'total_views': total_views})

@login_required
def image_list(request):
    images = Image.objects.all()
    paginator = Paginator(images, 8)
    page = request.GET.get('page')

    images_only = request.GET.get('images_only') # GET parameter images_only to know if the whole page has to be rendered or only the new images when scrolling
    try:
        images = paginator.page(page)
    
    except PageNotAnInteger:
        # If page is not an integer deliver the first page
        images = paginator.page(1)
    except EmptyPage:
        if images_only:
            # If ajax request and page out of range
            return HttpResponse('')
        images = paginator.page(paginator.num_pages)
    
    if images_only:
        return render(request, 'images/image/list_images.html', {'section': 'images', 'images': images})
    
    return render(request, 'images/image/list.html', {'section': 'images', 'images': images})

'''
The require_POST decorator returns an HttpResponseNotAllowed
object (status code 405) if the HTTP request is not done via POST. This way, you only allow POST requests for this view.
'''

'''
If the add() method is called passing an object that is already present in the related object set, it will 
not be duplicated. If the remove() method is called with an object that is not in the related object set, 
nothing will happen. Another useful method of many-to-many managers is clear(), which removes 
all objects from the related object set.
'''

'''
To generate the view response, we have used the JsonResponse class provided by Django, which 
returns an HTTP response with an application/json content type, converting the given object into 
a JSON output.
'''

@login_required
@require_POST

def image_like(request):
    image_id = request.POST.get('id')
    action = request.POST.get('action')

    if image_id and action:
        try:
            image = Image.objects.get(id=image_id)
            if action == 'like':
                image.users_like.add(request.user)
                create_action(request.user, "likes",image)
            else:
                image.users_like.remove(request.user)
        except Image.DoesNotExist:
            pass
    return JsonResponse({'status': 'error'})

# CHapter 7 - Store ranking with Redis
'''
The image_ranking view works like this:
1. You use the zrange() command to obtain the elements in the sorted set. This command expects 
a custom range according to the lowest and highest scores. Using 0 as the lowest and -1 as the 
highest score, you are telling Redis to return all elements in the sorted set. You also specify 
desc=True to retrieve the elements ordered by descending score. Finally, you slice the results 
using [:10] to get the first 10 elements with the highest score.
2. You build a list of returned image IDs and store it in the image_ranking_ids variable as a list 
of integers. You retrieve the Image objects for those IDs and force the query to be executed 
using the list() function. It is important to force the QuerySet execution because you will 
use the sort() list method on it (at this point, you need a list of objects instead of a QuerySet).
3. You sort the Image objects by their index of appearance in the image ranking. Now you can use 
the most_viewed list in your template to display the 10 most viewed images.
'''
@login_required
def image_ranking(request):
    image_ranking = r.zrange('image_ranking',0,-1,desc=True)[:10]
    image_ranking_ids = [int(id) for id in image_ranking]

    #get most viewed images
    most_viewed = list(Image.objects.filter(id__in=image_ranking_ids))
    most_viewed.sort(key=lambda x:image_ranking_ids.index(x.id))
    return render(request, 'images/image/ranking.html', {'section': 'images', 'most_viewed': most_viewed})