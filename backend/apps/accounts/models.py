from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model. Empty for now, but swapping AUTH_USER_MODEL later
    would require rebuilding every migration that touches the user table."""
