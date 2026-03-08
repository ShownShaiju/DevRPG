from django.contrib import admin
from .models import Guild, Quest, QuestRequirement

class QuestRequirementInline(admin.TabularInline):
    model = QuestRequirement
    extra = 1

@admin.register(Guild)
class GuildAdmin(admin.ModelAdmin):
    list_display = ('name', 'founder', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('members',)

@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ('title', 'guild', 'is_active', 'xp_reward', 'created_at')
    list_filter = ('is_active', 'guild')
    inlines = [QuestRequirementInline]