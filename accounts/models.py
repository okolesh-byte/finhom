from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.functions import Lower


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Укажите электронную почту')
        email = self.normalize_email(email).strip().lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

    def get_by_natural_key(self, username):
        return self.get(email__iexact=username.strip())


class User(AbstractUser):
    username = None
    email = models.EmailField('Электронная почта', unique=True)
    first_name = models.CharField('Имя', max_length=100)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    objects = UserManager()

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        constraints = [models.UniqueConstraint(Lower('email'), name='unique_email_case_insensitive')]

    def __str__(self):
        return self.email


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    birth_date = models.DateField('Дата рождения', null=True, blank=True)
    avatar = models.ImageField('Фотография', upload_to='avatars/', blank=True)
    expected_income = models.DecimalField('Ожидаемый доход', max_digits=12, decimal_places=2, default=0)
    payday = models.PositiveSmallIntegerField('День получения дохода', default=1)
    reserve_target = models.DecimalField('Желаемый резерв', max_digits=12, decimal_places=2, default=0)
    onboarding_completed = models.BooleanField('Настройка завершена', default=False)

    def __str__(self):
        return f'Профиль {self.user.first_name}'
