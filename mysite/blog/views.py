from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Post, Comment
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm
from django.core.mail import send_mail
from taggit.models import Tag
from django.db.models import Count

# view for sharing posts via email

def post_share(request, post_id):
    # retrieve post by id
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False

    # check if request is POST and if yes, send email
    if request.method == "POST":
        # form was submitted
        form = EmailPostForm(request.POST)

        # check if form is valid
        if form.is_valid():

            # form fields passed validation
            cd = form.cleaned_data

            # build post url
            post_url = request.build_absolute_uri(
                post.get_absolute_url()
            )
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url}\n\n {cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'admin@myblog.com', [{cd['to']}])
            sent = True

    # In case of GET request
    else:
        # just show the empty form to the user
        form = EmailPostForm()

    context_obj = {'post': post,
                   'form': form,
                   'sent': sent}
    return render(request, 'blog/post/share.html', context_obj)


# view to show up list view of posts

def post_list(request, tag_slug=None):
    # get all Post objects
    object_list = Post.objects.all()

    tag = None

    # check if a tag_slug is sent as an argument and filter the posts by tag
    if tag_slug:
        # get the tag from Tag model based on slug
        tag = get_object_or_404(Tag, slug=tag_slug)
        # filter the Post objects with the tag argument sent
        object_list = object_list.filter(tags__in=[tag])

    # Paginate the objects into chunks of 3
    paginator = Paginator(object_list, 3)
    # get 'page' argument from GET request
    page = request.GET.get('page')
    # if page arg is not in GET req, set it to 1
    if not page:
        page = 1
    try:
        # get specific page
        posts = paginator.page(page)
    except PageNotAnInteger:
        # how first page if page is not a number
        posts = Paginator.page(1)
    except EmptyPage:
        # show last page if page number is more than max pages available
        posts = Paginator.page(paginator.num_pages)

    return render(request, 'blog/post/list.html', {'page': page,
                                                   'posts': posts,
                                                   'tag': tag })


# view to show up all details about a Post

def post_detail(request, year, month, day, post):
    # get Post object based on argument passed
    post = get_object_or_404(Post, slug=post, status='published', publish__year=year,\
                             publish__month=month, publish__day=day)

    # List of active comments for this post (related_name field in Comment model)
    comments = post.comments.filter(active=True)

    new_comment = None

    # check if request is POST and if yes, save the comment based on form data
    if request.method == 'POST':
        # A comment was posted
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Create Comment object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # Assign the current post to the comment
            new_comment.post = post
            # Save the comment to the database
            new_comment.save()

    # if request was GET, show up the comment form
    else:
        comment_form = CommentForm()

    # list of similar posts

    # get the ids of tags for current posts. retrive values instead of single value tuples
    post_tags_ids = post.tags.values_list('id', flat=True)
    # get the posts containing any of post_tags_ids, excluding the current post
    similar_posts = Post.published.filter(tags__in=post_tags_ids)\
                                    .exclude(id=post.id)
    # use Count() to compute number of tags shared with all other tags and order the results by same_tags and publish desc
    similar_posts = similar_posts.annotate(same_tags=Count('tags'))\
                                    .order_by('-same_tags', '-publish')[:4]

    context_object = {'post': post,
                      'comments': comments,
                      'new_comment': new_comment,
                      'comment_form': comment_form,
                      'similar_posts': similar_posts}

    return render(request, 'blog/post/detail.html', context_object)


# Class Based View (alternative for post_list view)

class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'