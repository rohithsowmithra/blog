from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Post, Comment
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm
from django.core.mail import send_mail

# Create your views here.

def post_share(request, post_id):
    # retrieve post by id
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False

    if request.method == "POST":
        # form was submitted
        form = EmailPostForm(request.POST)

        if form.is_valid():
            # form fields passed validation
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(
                post.get_absolute_url()
            )
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url}\n\n {cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'admin@myblog.com', [{cd['to']}])
            sent = True
    else:
        form = EmailPostForm()

    context_obj = {'post': post,
                   'form': form,
                   'sent': sent}
    return render(request, 'blog/post/share.html', context_obj)


def post_list(request):
    object_list = Post.objects.all()
    paginator = Paginator(object_list, 3)
    page = request.GET.get('page')
    if not page:
        page = 1
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = Paginator.page(1)
    except EmptyPage:
        posts = Paginator.page(paginator.num_pages)

    return render(request, 'blog/post/list.html', {'page': page,
                                                   'posts': posts})

def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post, status='published', publish__year=year,\
                             publish__month=month, publish__day=day)

    # List of active comments for this post
    comments = post.comments.filter(active=True)

    new_comment = None

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
    else:
        comment_form = CommentForm()

    context_object = {'post': post,
                      'comments': comments,
                      'new_comment': new_comment,
                      'comment_form': comment_form}

    return render(request, 'blog/post/detail.html', context_object)


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'