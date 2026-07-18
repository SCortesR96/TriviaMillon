from django.contrib import admin

from .models import GameSession, LadderTemplate, Player, PlayerAnswer, PrizeLevel


class PrizeLevelInline(admin.TabularInline):
    model = PrizeLevel
    extra = 0


@admin.register(LadderTemplate)
class LadderTemplateAdmin(admin.ModelAdmin):
    search_fields = ['name']
    inlines = [PrizeLevelInline]


class PlayerInline(admin.TabularInline):
    model = Player
    extra = 0
    readonly_fields = ['nickname', 'score', 'joined_at']
    can_delete = False


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['code', 'question_set', 'ladder_template', 'status', 'current_level_index', 'is_paused', 'created_at']
    list_filter = ['status', 'question_set', 'ladder_template']
    search_fields = ['code']
    inlines = [PlayerInline]


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['nickname', 'session', 'score', 'joined_at']
    list_filter = ['session']
    search_fields = ['nickname']


@admin.register(PlayerAnswer)
class PlayerAnswerAdmin(admin.ModelAdmin):
    list_display = ['player', 'question', 'points_awarded', 'answered_at']
    list_filter = ['player__session']
