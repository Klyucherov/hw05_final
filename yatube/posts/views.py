from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import get_page_context


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    context = {
        'page_obj': get_page_context(request, post_list),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    context = {
        'group': group,
        'page_obj': get_page_context(request, post_list),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=author)
    if not request.user.is_authenticated:
        return render(request, 'users/login.html')
    following = Follow.objects.filter(
        user=request.user.id,
        author=author.id
    ).exists()
    context = {'page_obj': get_page_context(request, post_list),
               'author': author,
               'following': following,
               }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    comments = post.comments.filter(post=post_id)
    context = {
        'post': post,
        'post_id': post_id,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
@csrf_exempt
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post.pk, )
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post.pk, )
    is_edit = True
    context = {
        'form': form,
        'is_edit': is_edit
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = get_page_context(request, post_list)
    template = 'posts/follow.html'
    content = {
        'page_obj': page_obj,
    }
    return render(request, template, content)


@login_required
def profile_follow(request, username):
    author_obj = get_object_or_404(User, username=username)
    user_obj = request.user
    follow_obj = Follow.objects.filter(
        user=user_obj,
        author=author_obj
    )
    if not follow_obj.exists() and author_obj != user_obj:
        Follow.objects.create(user=user_obj, author=author_obj)
    return redirect('posts:profile', username=author_obj.username)


@login_required
def profile_unfollow(request, username):
    author_obj = get_object_or_404(User, username=username)
    user_obj = request.user
    follow_obj = Follow.objects.filter(
        user=user_obj,
        author=author_obj
    )
    if follow_obj.exists():
        follow_obj.delete()
    return redirect('posts:profile', username=author_obj.username)
