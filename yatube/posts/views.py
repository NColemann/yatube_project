from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm

NUM_OBJECTS_PER_PAGE = 10


@cache_page(20, key_prefix='index_page')
def index(request):
    """Главная страница."""
    template = 'posts/index.html'
    post_list = Post.objects.all()
    paginator = Paginator(post_list, NUM_OBJECTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'index': True,
    }
    return render(request, template, context)


def group_posts(request, slug):
    """Страница с записями группы."""
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, NUM_OBJECTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    """Страница пользователя."""
    template = 'posts/profile.html'
    author = User.objects.get(username=username)
    post_list = Post.objects.filter(author=author)
    paginator = Paginator(post_list, NUM_OBJECTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    count_obj = paginator.count
    following = (
        request.user.is_authenticated
        and author.following.filter(user=request.user).exists()
    )

    context = {
        'author': author,
        'page_obj': page_obj,
        'count_obj': count_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    """Страница отдельного поста."""
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    count_obj = Post.objects.filter(author=post.author).count()
    form = CommentForm(request.POST or None)
    comments_post = Comment.objects.filter(post=post_id)
    context = {
        'post': post,
        'count_obj': count_obj,
        'form': form,
        'comments': comments_post,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    """Страница создания поста."""
    template = 'posts/create_post.html'

    form = PostForm(request.POST or None, files=request.FILES or None)

    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', username=request.user)

    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    """Страница редактирования поста."""
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:post_detail', post_id=post_id)

    context = {
        'form': form,
        'is_edit': True,
        'post_id': post_id,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    """Добавить комментарий к посту."""
    post = Post.objects.get(id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Страница с постами авторов, на которые подписан пользователь."""
    template = 'posts/follow.html'
    user = request.user
    post_list = Post.objects.filter(author__following__user=user)
    paginator = Paginator(post_list, NUM_OBJECTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'follow': True,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора."""
    follow = get_object_or_404(User, username=username)
    is_exist = Follow.objects.filter(
        user=request.user,
        author=follow,
    ).exists()
    if follow != request.user and not is_exist:
        Follow.objects.get_or_create(
            user=request.user,
            author=follow
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Отписаться на автора."""
    unfollow = get_object_or_404(User, username=username)
    is_exist = Follow.objects.filter(
        user=request.user,
        author=unfollow,
    ).exists()
    if unfollow != request.user and is_exist:
        Follow.objects.filter(
            user=request.user,
            author=unfollow
        ).delete()
    return redirect('posts:profile', username=username)
