from django.contrib import admin
from .models import Skill, Job, UserSkill

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title',)

@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'level', 'xp')
    list_filter = ('user', 'level')