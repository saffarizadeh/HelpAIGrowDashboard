from django.shortcuts import render

from django.http import JsonResponse
from .models import *
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from random import randint
from django.utils import timezone
import re
from django.conf import settings
from django.http import Http404
from oauth2client.service_account import ServiceAccountCredentials
import ast
import random
import logging

logger = logging.getLogger(__name__)

WEBSITE_ADDRESS = 'http://amandabot.xyz'

def is_conversation_finished(conversation, current_iteration):
    # This function should decide whether the conversation is over or not
    # For now since we only have no-iteration conversations, all conversations could be finished after the first hearing from the user
    is_finished = False
    if current_iteration >= conversation.experiment_group.number_of_iterations:
        is_finished = True
    return is_finished

def game_response(request):
    conversation_token = request.POST.get("conversation_token")
    message = request.POST.get("message")
    is_finished = False
    user_na_error = False

    try:
        conversation_token_obj = ConversationToken.objects.get(token=conversation_token, updated_at__gte= (timezone.now() - timezone.timedelta(minutes=15)) )
        # update expiration time of the token by resaving it
        conversation_token_obj.save()
        conversation = conversation_token_obj.conversation
    except ObjectDoesNotExist:
        return JsonResponse({"response": {"id": 123456789, "fulfillment": -1, "response_code": 0, "is_finished": is_finished, "message": "Session expired! Please login again!"}})

    if message:
        Utterance.objects.create(conversation=conversation, text=message)
    iteration = conversation.iteration + 1
    conversation.iteration = iteration
    is_finished = is_conversation_finished(conversation, conversation.iteration)
    conversation.is_finished = is_finished
    conversation.save()

    response = ""
    if not is_finished:
        if iteration == 1:
            response = "The first question!"
        elif iteration == 2:
            response = "Which city are you from?"
        elif iteration == 3:
            response = "How many times do you do it every week?"
        else:
            response = "What's up?"
    else:
        response = "Thanks! We can continue our conversation later. But for now, if you don't mind, please answer a few questions about me!"
    response_dict = {"response": {"id": 123456789, "fulfillment": -1, "response_code": 0, "is_finished": is_finished, "message": response}}
    return JsonResponse(response_dict)

def simple_response(request):
    conversation_token = request.POST.get("conversation_token")
    message = request.POST.get("message")
    is_finished = False
    user_na_error = False
    response = False


    conversation_token_obj = ConversationToken.objects.filter(token=conversation_token, updated_at__gte= (timezone.now() - timezone.timedelta(minutes=15)) ).latest('updated_at')
    # update expiration time of the token by resaving it
    conversation_token_obj.save()
    conversation = conversation_token_obj.conversation

    if not response:
        if message:
            Utterance.objects.create(conversation=conversation, text=message)
            if BotUtteranceCompletion.objects.filter(conversation=conversation, is_done=False).exists():
                undone_bot_utterance_completion = BotUtteranceCompletion.objects.filter(conversation=conversation, is_done=False)[0]
                undone_bot_utterance_completion.is_done = True
                undone_bot_utterance_completion.save()
            conversation.iteration += 1
            # is_finished = is_conversation_finished(conversation, conversation.iteration)
            # conversation.is_finished = is_finished
            conversation.save()
            is_finished = conversation.is_finished
            response = ""
            current_utterance = False
            if not is_finished:
                bot_utterances = BotUtterance.objects.filter(experiment_group=conversation.experiment_group, deactivated=False).order_by('priority')
                for bot_utterance in bot_utterances:
                    if not BotUtteranceCompletion.objects.filter(conversation=conversation, bot_utterance=bot_utterance, is_done=True).exists():
                        BotUtteranceCompletion.objects.create(conversation=conversation, bot_utterance=bot_utterance, is_done=False)
                        current_utterance = bot_utterance
                        break
                if not current_utterance:
                    is_finished = True
                    conversation.is_finished = True
                    conversation.save()
                    response = "<speak>Thanks! That was interesting! We can continue our conversation later. But for now, if you don't mind, please answer a few questions about me!</speak>"
                # is_last_bot_utterance = (current_utterance.pk == bot_utterances.order_by('-priority')[0].pk)
                # if is_last_bot_utterance:
                else:
                    response = current_utterance.message
            else:
                response = ""
        else:
            if BotUtteranceCompletion.objects.filter(conversation=conversation, is_done=False).exists():
                undone_bot_utterance_completion = BotUtteranceCompletion.objects.filter(conversation=conversation, is_done=False)[0]
                undone_bot_utterance = undone_bot_utterance_completion.bot_utterance
            else:
                undone_bot_utterance = BotUtterance.objects.filter(experiment_group=conversation.experiment_group, deactivated=False).order_by('priority')[0]
                b, c = BotUtteranceCompletion.objects.get_or_create(conversation=conversation, bot_utterance=undone_bot_utterance, is_done=False)
            response = undone_bot_utterance.message
        response_dict = {"response": {"id": 123456789, "fulfillment": -1, "response_code": 0, "is_finished": is_finished, "message": response}}
        response = JsonResponse(response_dict)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Max-Age"] = "1000"
    response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
    return response

def conversation_finished(request):
    conversation_token = request.POST.get("conversation_token")
    try:
        conversation_token_obj = ConversationToken.objects.get(token=conversation_token, updated_at__gte= (timezone.now() - timezone.timedelta(minutes=15)) )
        conversation = conversation_token_obj.conversation
        conversation.is_finished = True
        conversation.save()
        success = True
    except ObjectDoesNotExist:
        success = False
    return JsonResponse({"response": {"id": 123456789, "success": success}})

class SentenceRandomizer():
    def set_response_string(self, response_string):
        self.response_string = response_string
    def choose_random(self, choice_list):
        return random.choice(choice_list)
    def string_to_list(self, string):
        return ast.literal_eval(string)
    def choice_list_maker(self, string_list):
        return self.string_to_list(string_list)
    def response_template_detector(self, response_string):
        return re.findall("\[[^\[|\]]+\]", response_string)
    def produce_response(self):
        response = ""
        response_template = self.response_template_detector(self.response_string)
        if response_template:
            for string_list in response_template:
                choice_list = self.choice_list_maker(string_list)
                choice = self.choose_random(choice_list)
                response = response + choice + " "
        else:
            response = self.response_string
        return response

def random_wording(text):
    # Add multilayed random later <rand2>
    sentence = ""
    rand1s = text.split("<rand1>")
    if "<rand1>" in text:
        sentence += random.choice(rand1s[1:])
    else:
        sentence += random.choice(rand1s) # In case the input does not contain any <rand1>
    return sentence

def random_choice(text):
    choices = text.split("<choice>")
    return random.choice(choices[1:])

def get_similar_phrases(text):
    similarity_dict = {"I turned on the light.":
                                                [
                                                "The light is on.",
                                                "It's on.",

                                                "I turned on the light.",
                                                "Turned on the light.",
                                                "I turned it on.",
                                                "Turned it on.",

                                                "I switched on the light.",
                                                "Switched on the light.",
                                                "I switched it on.",
                                                "Switched it on."
                                                ]
                        }
    paraphrases = similarity_dict.get(text, [])
    return similarity_dict.get(text)

def add_verbal_indeterminacy(text):
    paraphrases = get_similar_phrases(text)
    if paraphrases:
        paraphrase = random.choice(paraphrases)
    else:
        paraphrase = text
    return paraphrase

def negate_sentence(text):
    pattern = re.compile("turned", re.IGNORECASE)
    text = pattern.sub("didn't turn", text)
    pattern = re.compile("switched", re.IGNORECASE)
    text = pattern.sub("didn't switch", text)
    pattern = re.compile("It's", re.IGNORECASE)
    text = pattern.sub("It's not", text)
    text = text.replace(" is ", " is not ")
    text = text.capitalize()
    return text

def add_taskfulfillment_indeterminacy(text):
    fulfillment = 1
    if random.random()>0.5:
        text = negate_sentence(text)
        fulfillment = 0
    return (text, fulfillment)

def add_halting_indeterminacy(text):
    text_list = text.split(" ")
    if random.random() > 0.5:
        chosen_index = random.randint(1,len(text_list)-1)
        text_list.insert(chosen_index, '<amazon:breath duration="short"/>')
    return ' '.join(text_list)

def add_tonal_indeterminacy(text):
    text = text.replace('breath duration', 'breath_duration')
    text_list = text.split(" ")
    if random.random() > 0.5:
        chosen_index = random.randint(1,len(text_list)-1)
        chosen_token = text_list.pop(chosen_index)
        chosen_token = '<amazon:effect phonation="soft">'+chosen_token+'</amazon:effect>'
        text_list.insert(chosen_index, chosen_token)
    if random.random() > 0.5:
        chosen_index = random.randint(1,len(text_list)-1)
        chosen_token = text_list.pop(chosen_index)
        chosen_token = '<emphasis level="strong">'+chosen_token+'</emphasis>'
        text_list.insert(chosen_index, chosen_token)
    if random.random() > 0.5:
        chosen_index = random.randint(1,len(text_list)-1)
        chosen_token = text_list.pop(chosen_index)
        chosen_token = '<prosody volume="x-loud">'+chosen_token+'</prosody>'
        text_list.insert(chosen_index, chosen_token)
    if random.random() > 0.5:
        chosen_index = random.randint(1,len(text_list)-1)
        chosen_token = text_list.pop(chosen_index)
        chosen_token = '<amazon:effect vocal-tract-length="+5%"> '+chosen_token+'</amazon:effect>'
        text_list.insert(chosen_index, chosen_token)
    text = ' '.join(text_list)
    text = text.replace('breath_duration', 'breath duration')
    return text

# To randomly choose an option and keep it throughout the conversation
# if command.verbal_indeterminacy:
#     response_message = command.success_message
# else:
#     try:
#         command_conversation = ConversationCommand.objects.get(conversation=conversation,command=command)
#         predefined_response = command_conversation.predefined_response
#     except:
#         predefined_response = random_choice(command.success_message)
#         ConversationCommand.objects.create(conversation=conversation,command=command,
#                                            predefined_response=predefined_response)
#     response_message = predefined_response                    response_message = command.success_message

def assistant_response(request):
    conversation_token = request.POST.get("conversation_token")
    # logger.info("The value of conversation_token is %s", conversation_token)
    message = request.POST.get("message")
    #predefined_response = request.POST.get("predefined_response") # Receive a static message from Qualtrics
    predefined_response = ""
    next_command_hint_text = ""
    is_finished = False
    user_na_error = False
    response_code = 1
    response_parameter = ""
    tutorial = False
    response_message = ""
    has_tried_all_commands = False
    response_time_min = 0
    response_time_max = 0
    command_completed = False
    fulfillment = -1

    try:
        conversation_token_obj = ConversationToken.objects.get(token=conversation_token, updated_at__gte= (timezone.now() - timezone.timedelta(minutes=15)) )
        # update expiration time of the token by resaving it
        conversation_token_obj.save()
        conversation = conversation_token_obj.conversation
    except ObjectDoesNotExist:
        return JsonResponse({"response": {"id": 123456789, "fulfillment": -1, "response_code": 0, "is_finished": is_finished, "message": "Session expired! Please login again!"}})

    available_commands = Command.objects.filter(experiment_group=conversation.experiment_group)

    if message:
        utterance = Utterance.objects.create(conversation=conversation, text=message)
        conversation.iteration += 1
        conversation.save()
        response = ""
        for command in available_commands:
            if re.search(command.detection_regex, message, flags=re.IGNORECASE):
                try:
                    response_message = command.success_message

                    if command.verbal_indeterminacy:
                        response_message = add_verbal_indeterminacy(response_message)
                    if command.taskfulfillment_indeterminacy:
                        response_message, fulfillment = add_taskfulfillment_indeterminacy(response_message)
                    else:
                        fulfillment = 1
                    if command.halting_indeterminacy:
                        response_message = add_halting_indeterminacy(response_message)
                    if command.tonal_indeterminacy:
                        response_message = add_tonal_indeterminacy(response_message)
                    if command.response_parameter_regex:
                        response_parameter = re.search(command.response_parameter_regex, message, flags=re.IGNORECASE).group(1)
                        response_message = response_message.replace("{{response_parameter}}", str(response_parameter))
                    response_code = command.response_code
                    response_time_min = command.response_time_min
                    response_time_max = command.response_time_max
                    command_completion, c = CommadCompletion.objects.get_or_create(conversation=conversation, command=command)
                    command_completion.use_count += 1
                    command_completion.tutorial_is_done = True
                    command_completion.save()
                    command_completed = command_completion.use_count >= command.completion_criteria
                except:
                    response_message = command.failure_message
                    response_code = 1
                    fulfillment = -1
                break
        if not response_message:
            response_message = "I’m sorry! I didn’t understand."
            fulfillment = -1
    completed_tutorials = CommadCompletion.objects.filter(conversation=conversation, tutorial_is_done=True).values_list('command__id', flat=True)
    tutorials = Command.objects.filter(experiment_group=conversation.experiment_group).exclude(pk__in=completed_tutorials).order_by('priority')
    try:
        tutorial = tutorials[0]
        next_command_hint_text = tutorial.tutorial_message
    except:
        next_command_hint_text = "You have tried all the commands!"
        has_tried_all_commands = True
    response_message = '<speak>' + response_message + '</speak>'
    CAUtterance.objects.create(conversation=conversation, text=response_message)
    response = JsonResponse({"response": {"id": 123456789, "response_code": response_code, "response_parameter": response_parameter,
                        "next_command_hint_text": next_command_hint_text, "is_finished": False,
                        "response_time_min": response_time_min, "response_time_max":response_time_max, "command_completed": command_completed,
                        "has_tried_all_commands": has_tried_all_commands, "fulfillment":fulfillment, "message": response_message}})
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Max-Age"] = "1000"
    response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
    return response

def experiment_group(request, user=None):
    if user:
        return user

def auth(request):
    if 'time' in request.session:
        del request.session['time']
    try:
        unique_id = request.POST.get("unique_id")
    except:
        unique_id = request.GET.get("unique_id")
    try:
        experiment_id = request.POST.get("experiment_id")
    except:
        experiment_id = request.GET.get("experiment_id")
    try:
        experiment_group = request.POST.get("experiment_group")
    except:
        try:
            experiment_group = request.GET.get("experiment_group")
        except:
            experiment_group = None
    pre_test_url = ""
    post_test_url = ""
    experiment_id_error = False
    user_creation_error = False
    conversation_creation_error = False
    days_until_next_stage = 0
    conversation_token = ""
    success = False
    experiment_is_over = False
    group_number = 0
    pre_post_group = 0
    voice_persona = "Joanna"
    consent_form_url = ""
    app_experiment_code = 0
    user_pk = 0

    try:
        experiment_type = ExperimentType.objects.get(identifier = experiment_id)
    except ObjectDoesNotExist:
        experiment_id_error = True

    new_conversation = None
    if not experiment_id_error:
        if unique_id != "" or unique_id!=None:
            try:
                user, created = UserInfo.objects.get_or_create(device_unique_id=unique_id)
                user_pk = user.id
            except:
                user_creation_error = True
        else:
            user_creation_error = True
        if not user_creation_error:
            try:
                conversation = Conversation.objects.filter(experiment_group__experiment_stage__experiment_type=experiment_type, user=user).order_by('-updated_at')[0]
                if conversation.is_finished:
                    next_stage_group = conversation.experiment_group.next_stage_group
                    if next_stage_group:
                        min_gap_to_next_stage = conversation.experiment_group.experiment_stage.min_gap_to_next_stage
                        days_since_previous_stage = (timezone.now() - conversation.updated_at).days
                        if days_since_previous_stage >= min_gap_to_next_stage:
                            new_conversation = Conversation.objects.create(
                                                user=user,
                                                experiment_group = next_stage_group
                                                )
                            success = True
                        else:
                            # user need to wait until the next stage be available
                            days_until_next_stage = min_gap_to_next_stage - days_since_previous_stage
                            success = False
                    else:
                        # the entire experiment is finished!
                        experiment_is_over = True
                        success = False
                else:
                    success = True
                    if conversation.iteration > 0 and conversation.iteration < conversation.experiment_group.number_of_iterations:
                        Utterance.objects.filter(conversation=conversation).delete()
                        conversation.iteration = 0
                        conversation.save()
            except:
                # first time user using the app
                experiment_stage = ExperimentStage.objects.get(experiment_type=experiment_type, stage_number=1)
                experiment_groups = ExperimentGroup.objects.filter(experiment_stage=experiment_stage, deactivated=False).order_by('group_number')
                number_of_experiment_groups = experiment_groups.count()
                if str.isdigit(str(experiment_group)):
                    """ Qualtrics handles group randomization """
                    experiment_group = ExperimentGroup.objects.get(experiment_stage=experiment_stage, deactivated=False, group_number=experiment_group)
                    pre_post_group = 1
                else:
                    """ Randomizing: 1-Pure random; 2-Sequential """
                    """ pre_post_group referes to the possibility of receiving the questions before or after the test
                        The use of this feature is obsolete because we handle this feature via Qualtrics.
                        We keep it for future use cases.
                    """
                    #1-Pure random
                    # group_random_number = randint(1,number_of_experiment_groups) - 1
                    #2-Sequential
                    group_random_number = experiment_stage.number_of_users_attempted % number_of_experiment_groups
                    if number_of_experiment_groups % 2 == 0:
                        nth_cycle = experiment_stage.number_of_users_attempted / number_of_experiment_groups
                        pre_post_group = 1 + (experiment_stage.number_of_users_attempted + nth_cycle) % 2
                    else:
                        pre_post_group = 1 + experiment_stage.number_of_users_attempted % 2
                    experiment_group = experiment_groups[group_random_number]
                    """ ---------------------------------------- """
                experiment_stage.number_of_users_attempted += 1
                experiment_stage.save()
                new_conversation = Conversation.objects.create(
                                        user=user,
                                        experiment_group = experiment_group,
                                        pre_post_group=pre_post_group,
                                        )
                success = True
            if new_conversation:
                conversation = new_conversation
            if success:
                conversation_token_obj = ConversationToken.objects.create(conversation=conversation)
                conversation_token = conversation_token_obj.token
                pre_test_url = conversation.experiment_group.pre_test_url
                post_test_url = conversation.experiment_group.post_test_url
                group_number = conversation.experiment_group.group_number
                pre_post_group = conversation.pre_post_group
                voice_persona = conversation.experiment_group.voice_persona
                consent_form_url = conversation.experiment_group.experiment_stage.experiment_type.consent_form_url
                app_experiment_code = conversation.experiment_group.app_experiment_code
                if not consent_form_url:
                    consent_form_url = WEBSITE_ADDRESS + '/consent_form/%d/' %int(experiment_id)
    response = JsonResponse({"response": {"id": 123456789, "experiment_id_error": experiment_id_error,
                        "conversation_creation_error": conversation_creation_error,
                        "user_creation_error": user_creation_error, "days_until_next_stage":days_until_next_stage,
                        "conversation_token": conversation_token, "experiment_is_over": experiment_is_over,
                        "post_test_url": post_test_url, "pre_test_url": pre_test_url, "group_number": group_number,
                        "pre_post_group": pre_post_group,
                        "voice_persona": voice_persona, "consent_form_url": consent_form_url,
                        "app_experiment_code": app_experiment_code, "user_pk": user_pk, "success": success}})
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Max-Age"] = "1000"
    response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
    return response

def consent_form(request, experiment_id):
    html = 'response/consent_form_%d.html' %experiment_id
    context = {}
    try:
        return render(request, html, context)
    except:
        raise Http404

def about(request, version):
    html = 'response/about_%s.html' %version
    context = {}
    return render(request, html, context)

def refresh_conversation_token(conversation_token):
    try:
        conversation_token_obj = ConversationToken.objects.get(token=conversation_token, updated_at__gte= (timezone.now() - timezone.timedelta(minutes=15)) )
        # update expiration time of the token by resaving it
        conversation_token_obj.save()
        conversation = conversation_token_obj.conversation
        return conversation
    except ObjectDoesNotExist:
        return False


def speech_access_token(request):
    conversation_token = request.GET.get("conversation_token")
    conversation = refresh_conversation_token(conversation_token)
    if not conversation:
        success = False
        return JsonResponse({"response": {"id": 987, "success": success}})

    try:
        json_file = settings.BASE_DIR + '/response/credential.json'
        scopes = ['https://www.googleapis.com/auth/cloud-platform']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file, scopes=scopes)
        token = credentials.get_access_token()
        access_token = token.access_token
        expires_in = token.expires_in
        success = True
        return JsonResponse({"response": {"id": 156, "access_token": access_token, "expires_in": expires_in, "success": success}})
    except:
        success = False
        return JsonResponse({"response": {"id": 564, "success": success}})
