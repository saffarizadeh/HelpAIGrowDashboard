from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.db import models
from django.utils import timezone
import uuid

@python_2_unicode_compatible
class UserInfo (models.Model):
    device_unique_id = models.CharField(max_length=100, default="0")
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField()
    def save(self, *args, **kwargs):
        if not self.id or not self.created_at:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(UserInfo, self).save(*args, **kwargs)
    def __str__(self):
        return str(self.device_unique_id)

@python_2_unicode_compatible
class ExperimentType(models.Model):
    name = models.CharField(max_length=30)
    identifier = models.IntegerField(default=0)
    description = models.CharField(max_length=500)
    consent_form_url = models.URLField(default="", blank=True, null=True)
    def __str__(self):
        return str(self.name) + ' - ' + str(self.identifier)

@python_2_unicode_compatible
class ExperimentStage(models.Model):
    experiment_type = models.ForeignKey(ExperimentType, on_delete=models.CASCADE)
    stage_number = models.IntegerField(default=1)
    next_stage = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True)
    min_gap_to_next_stage = models.IntegerField(default=0)
    number_of_users_attempted = models.IntegerField(default=0)
    def __str__(self):
        return "Stage " + str(self.stage_number) + " - " + str(self.experiment_type.name)

VOICE_PERSONA_CHOICES = [
    ('Joanna', 'English, US - Female - Joanna'), ('Kendra', 'English, US - Female - Kendra'), ('Ivy', 'English, US - Female - Ivy'),
    ('Kimberly', 'English, US - Female - Kimberly'), ('Salli', 'English, US - Female - Salli'),
    ('Joey', 'English, US - Male - Joey'), ('Justin', 'English, US - Male - Justin'), ('Matthew', 'English, US - Male - Matthew'),
    ('Amy', 'English, British - Female - Amy'), ('Emma', 'English, British - Female - Emma'), ('Brian', 'English, British - Male - Brian'),
    ('Nicole', 'English, Australian - Female - Nicole'), ('Russell', 'English, Australian - Male - Russell'),
    ('Geraint', 'English, Welsh - Male - Geraint'),
    ('Aditi', 'English, Indian - Female - Aditi'), ('Raveena', 'English, Indian - Female - Raveena'),
    ('Gwyneth', 'Welsh - Female - Gwyneth'),
    ('Carla', 'Italian - Female - Carla'), ('Giorgio', 'Italian - Male - Giorgio'),
    ('Conchita', 'Spanish, Castilian - Female - Conchita'), ('Enrique', 'Spanish, Castilian - Male - Enrique'),
    ('Penelope', 'Spanish, US - Female - Penelope'), ('Miguel', 'Spanish, US - Male - Miguel'),
    ('Ines', 'Portuguese - Female - Ines'), ('Cristiano', 'Portuguese - Male - Cristiano'),
    ('Vitoria', 'Portuguese, Brazilian - Female - Vitoria'), ('Ricardo', 'Portuguese, Brazilian - Male - Ricardo'),
    ('Celine', 'French - Female - Celine'), ('Mathieu', 'French - Male - Mathieu'),
    ('Chantal', 'French, Canadian - Female - Chantal'),
    ('Vicki', 'German - Female - Vicki'), ('Marlene', 'German - Female - Marlene'), ('Hans', 'German - Male - Hans'),
    ('Lotte', 'Dutch - Female - Lotte'), ('Ruben','Dutch - Male - Ruben'),
    ('Naja', 'Danish - Female - Naja'), ('Mads', 'Danish - Male - Mads'),
    ('Astrid', 'Swedish - Female - Astrid'),
    ('Liv', 'Norwegian - Female - Liv'),
    ('Dora', 'Icelandic - Female - Dora'), ('Karl', 'Icelandic - Male - Karl'),
    ('Tatyana', 'Russian - Female - Tatyana'), ('Maxim', 'Russian - Male - Maxim'),
    ('Ewa', 'Polish - Female - Ewa'), ('Maja', 'Polish - Female - Maja'), ('Jan', 'Polish - Male - Jan'), ('Jacek', 'Polish - Male - Jacek'),
    ('Carmen', 'Romanian - Female - Carmen'),
    ('Mizuki', 'Japanese - Female - Mizuki'), ('Takumi', 'Japanese - Male - Takumi'),
    ('Seoyeon', 'Korean, Female - Seoyeon'),
    ('Filiz', 'Turkish - Female - Filiz')
]

@python_2_unicode_compatible
class ExperimentGroup(models.Model):
    experiment_stage = models.ForeignKey(ExperimentStage, on_delete=models.CASCADE, default=None)
    group_number = models.IntegerField(default=1)
    next_stage_group = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(default="", blank=True)
    initial_utterance = models.TextField(default="", blank=True)
    voice_persona = models.CharField(max_length=20, default="", choices=VOICE_PERSONA_CHOICES)
    number_of_iterations = models.IntegerField(default=1)
    pre_test_url = models.URLField(default="")
    post_test_url = models.URLField(default="")
    app_experiment_code = models.IntegerField(default=0)
    deactivated = models.BooleanField(default=False)
    def __str__(self):
        return str(self.experiment_stage.experiment_type.name) + " - Stage " + str(self.experiment_stage.stage_number) + " - Group " + str(self.group_number)

@python_2_unicode_compatible
class Conversation (models.Model):
    experiment_group = models.ForeignKey(ExperimentGroup, on_delete=models.CASCADE, default=None)
    pre_post_group = models.IntegerField(default=1)
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    tracking_id = models.CharField(max_length=100, default="0")
    iteration = models.IntegerField(default=0)
    is_finished = models.BooleanField(default=False)
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField()
    def save(self, *args, **kwargs):
        if not self.id or not self.created_at:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(Conversation, self).save(*args, **kwargs)
    def __str__(self):
        return str(self.id) + " - " + str(self.experiment_group.experiment_stage.experiment_type.name) + " - Stage " + str(self.experiment_group.experiment_stage.stage_number) + " - Group " + str(self.experiment_group.group_number)

@python_2_unicode_compatible
class Command(models.Model):
    title = models.CharField(max_length=100, default="")
    experiment_group = models.ForeignKey(ExperimentGroup, on_delete=models.CASCADE, default=None)
    detection_regex = models.TextField(default="", blank=True)
    response_parameter_regex = models.TextField(default="", blank=True)
    success_message = models.TextField(default="", blank=True)
    taskfulfillment_indeterminacy = models.BooleanField(default=False)
    verbal_indeterminacy = models.BooleanField(default=False)
    tonal_indeterminacy = models.BooleanField(default=False)
    halting_indeterminacy = models.BooleanField(default=False)
    failure_message = models.TextField(default="", blank=True)
    response_code = models.IntegerField(default=0)
    tutorial_message = models.TextField(default="", blank=True)
    response_time_min = models.IntegerField(default=0)
    response_time_max = models.IntegerField(default=0)
    completion_criteria = models.IntegerField(default=0)
    priority = models.IntegerField(default=1)
    def __str__(self):
        return str(self.title) + " - " + str(self.experiment_group.experiment_stage.experiment_type.name) + " - Stage " + str(self.experiment_group.experiment_stage.stage_number) + " - Group " + str(self.experiment_group.group_number)

@python_2_unicode_compatible
class ConversationCommand(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, default=None)
    command = models.ForeignKey(Command, on_delete=models.CASCADE, default=None)
    predefined_response = models.TextField(default="", blank=True)
    def __str__(self):
        return str(self.command.title) + " - " + str(self.conversation.experiment_group.experiment_stage.experiment_type.name) + " - Stage " + str(self.conversation.experiment_group.experiment_stage.stage_number) + " - Group " + str(self.conversation.experiment_group.group_number)

@python_2_unicode_compatible
class BotUtterance(models.Model):
    title = models.CharField(max_length=100, default="")
    experiment_group = models.ForeignKey(ExperimentGroup, on_delete=models.CASCADE, default=None)
    message = models.TextField(default="", blank=True)
    priority = models.IntegerField(default=1)
    deactivated = models.BooleanField(default=False)
    def __str__(self):
        return str(self.title) + " - " + str(self.experiment_group.experiment_stage.experiment_type.name) + " - Stage " + str(self.experiment_group.experiment_stage.stage_number) + " - Group " + str(self.experiment_group.group_number)

class BotUtteranceCompletion(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, default=None)
    bot_utterance = models.ForeignKey(BotUtterance, on_delete=models.CASCADE, default=None)
    is_done = models.BooleanField(default=True)
    def __str__(self):
        return str(self.id)

class CommadCompletion(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, default=None)
    command = models.ForeignKey(Command, on_delete=models.CASCADE, default=None)
    tutorial_is_done = models.BooleanField(default=False)
    use_count = models.IntegerField(default=0)
    def __str__(self):
        return str(self.id)

@python_2_unicode_compatible
class Utterance(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    text = models.TextField()
    dangling = models.BooleanField(default=False)
    created_at = models.DateTimeField(editable=False)
    def save(self, *args, **kwargs):
        if not self.id or not self.created_at:
            self.created_at = timezone.now()
        return super(Utterance, self).save(*args, **kwargs)
    def __str__(self):
        return str(self.text)

@python_2_unicode_compatible
class CAUtterance(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(editable=False)
    def save(self, *args, **kwargs):
        if not self.id or not self.created_at:
            self.created_at = timezone.now()
        return super(CAUtterance, self).save(*args, **kwargs)
    def __str__(self):
        return str(self.conversation.experiment_group.experiment_stage.experiment_type.name) + ' - ' + str(self.conversation.experiment_group.group_number) + ' - ' +str(self.text)

class ConversationToken(models.Model):
    token = models.CharField(max_length=100, default="0")
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField(blank=True, null=True)
    def save(self, *args, **kwargs):
        if not self.id  or not self.created_at:
            self.token = str(uuid.uuid1())
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(ConversationToken, self).save(*args, **kwargs)
    def __str__(self):
        return str(self.token)
