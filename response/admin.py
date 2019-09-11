from django.contrib import admin
from .models import *

admin.site.register(UserInfo)
admin.site.register(ExperimentType)
admin.site.register(ExperimentStage)
admin.site.register(Conversation)
admin.site.register(Utterance)
admin.site.register(CAUtterance)
admin.site.register(ConversationToken)
admin.site.register(ExperimentGroup)
admin.site.register(Command)
admin.site.register(ConversationCommand)
admin.site.register(CommadCompletion)
admin.site.register(BotUtterance)
admin.site.register(BotUtteranceCompletion)
