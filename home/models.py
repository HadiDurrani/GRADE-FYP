# from django.db import models

# # Create your models here.
# from djongo import models

# class User(models.Model):
#     USER_TYPES = [
#         ('teacher', 'Teacher'),
#         ('student', 'Student'),
#     ]

#     username = models.CharField(max_length=255, unique=True)
#     email = models.EmailField(unique=True)
#     password = models.CharField(max_length=255)
#     user_type = models.CharField(max_length=10, choices=USER_TYPES)

#     def __str__(self):
#         return self.username

from djongo import models
from bson import ObjectId
import random
import string

def generate_class_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def generate_class_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class User(models.Model):
    USER_TYPES = [
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]

    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    user_type = models.CharField(max_length=10, choices=USER_TYPES)

    def __str__(self):
        return self.username

class Classroom(models.Model):
    id = models.ObjectIdField(primary_key=True, default=ObjectId)  # ✅ Fix: Use ObjectIdField
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=6, unique=True, default=generate_class_code)
    teacher = models.ForeignKey("User", on_delete=models.CASCADE, related_name='classes')

    def __str__(self):
        return f"{self.name} ({self.code})"

class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrolled_classes')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='students')

    class Meta:
        unique_together = ('student', 'classroom')

    def __str__(self):
        return f"{self.student.username} -> {self.classroom.name}"