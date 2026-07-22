from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    # Empty for now, but doing this on day one anyway — swapping
    # AUTH_USER_MODEL after the first migration is apparently a nightmare,
    # so better to eat the cost now while there's nothing to migrate.
    pass
