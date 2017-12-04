import requests
import json
from tokenlib import TokenManager, make_token, parse_token

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, FormView, TemplateView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist

from .utils import *
from .models import Message, ReplyMessage, AdminUser, Team, Token
from .forms import UserCreationForm, LoginForm, SettingsForm
from core.settings import CLIENT_ID, CLIENT_SECRET, SECRET_SALT


#--------------------------- Auth Views ------------------------------------
class SignView(CreateView):
    form_class = UserCreationForm
    template_name = 'leave_bot/registration.html'
    success_url = '/'
    model = AdminUser


class LogView(FormView):
    form_class = LoginForm
    template_name = 'leave_bot/login.html'
    success_url = 'index'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect('index')
        return super(LogView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(email=email, password=password)
        if user is not None:
            login(self.request, user)
            return redirect(self.success_url)

def out(request):
    logout(request)
    return redirect('login')

#--------------------------- Primary Views ------------------------------------
@login_required(login_url='login')
def index(request):
    print(request.user.pk)
    teams = Team.objects.filter(admin_id=request.user.pk)
    context = {
        'teams':teams
    }
    return render(request, 'leave_bot/index.html', context)


class StatisticsView(TemplateView):
    template_name = 'leave_bot/statistics.html'

    def get_context_data(self, **kwargs):
        context = super(StatisticsView, self).get_context_data(**kwargs)
        team_id = self.kwargs['team_id']
        team = Team.objects.get(team_id=team_id)
        team_name = team.team_name
        messages = Message.objects.filter(team_id=team_id).prefetch_related('answers')
        context['messages'] = messages
        context['team_name'] = team_name
        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(StatisticsView, self).dispatch(*args, **kwargs)


@login_required(login_url='login')
def settings(request, team_id):
    if request.POST:
        req_channel = request.POST.get('channel')
        team = Team.objects.get(team_id=team_id)
        if team.admin_id != request.user.pk:
            return HttpResponse("Not authorized")
        channels = json.loads(
            requests.get(
                'https://slack.com/api/groups.list?token='+team.bot_token
            ).text
        )['groups']
        for chan in channels:
            if chan['name'] == req_channel:
                new_chan = chan['id']
                break
        team.channel = new_chan or team.channel
        team.moderator_expire = request.POST.get('expire') or team.moderator_expire
        team.save()
        return redirect('index')
    team = Team.objects.get(team_id=team_id)
    context = {
        'team_name':team.team_name,
        'team':team_id,
        'form':SettingsForm
    }
    return render(request, 'leave_bot/channel.html', context)

@login_required(login_url='login')
def invite(request, team_id):
    team = Team.objects.get(team_id=team_id)
    token = make_token(
        {"team_id":team_id,
         "team_name":team.team_name},
        timeout=team.moderator_expire, secret=SECRET_SALT
    )[:150]
    Token(token=token).save()
    context = {
        'token':token
    }
    return render(request, 'leave_bot/invite.html', context)

def invited(request, token):
    try:
        db_token = Token.objects.get(token=token)
    except ObjectDoesNotExist:
        return HttpResponse(
            "Token doesn't exists. Ask for token from administrator"
        )
    try:
        team = parse_token(token, secret=SECRET_SALT)
        team_id = team['team_id']
        team_name = team['team_name']
    except ValueError:
        db_token.delete()
        return HttpResponse(
            "Token expired. Ask for another token from administrator"
        )
    context = {
        'messages':Message.objects.filter(team_id=team_id).prefetch_related('answers'),
        'team_name':team_name
    }
    return render(request, 'leave_bot/statistics.html', context)

#--------------------------- Internal Views -----------------------------------
def oauth(request):
    """
    process response from Add to Slack button
    """
    code = request.GET['code']
    context = {
        'client_id':CLIENT_ID,
        'client_secret':CLIENT_SECRET,
        'code':code,
    }
    resp = requests.get('https://slack.com/api/oauth.access', context)
    data = json.loads(resp.text)
    admin = AdminUser.objects.get(pk=request.user.pk)
    team, created = Team.objects.get_or_create(team_id=data['team_id'])
    team.team_name=data['team_name']
    team.admin=admin
    team.bot_token=data['bot']['bot_access_token']
    team.bot_id=data['bot']['bot_user_id']
    team.save()
    return redirect('settings', team.team_id)

@csrf_exempt
def ask_leave(request):
    """
    process bot slash command
    """
    payload=request.POST
    try:
        team = Team.objects.get(team_id=payload.get('team_id'))
        user_info = requests.get(
            'https://slack.com/api/users.info'
            +'?token='+team.bot_token
            +'&user='+payload.get('user_id')
        )
        user = json.loads(user_info.text)['user']
    except:
        return HttpResponse("There is no such user")
    try:
        channel = Team.objects.get(team_id=payload['team_id']).channel
    except:
        return HttpResponse("Channel doesn't set up, or team does not exist")
    resp = send_ask_leave(team.bot_token, user['real_name'],
                          payload.get('text'), channel)
    mesg = Message(
        author_id=payload['user_id'],
        author_name=user['real_name'],
        text=payload['text'],
        ts=resp['ts'],
        team_id=payload['team_id'],
        is_answered=False
    )
    mesg.save()

    return HttpResponse(
        'The sign was given, brah. Now relax and wait for the answer'
    )

@csrf_exempt
def listen_events(request):
    """
    process events catched by bot
    """
    payload = json.loads(request.body.decode())
    # for slack callback verification
    if payload.get('challenge'):
        return HttpResponse(payload['challenge'])

    event = payload['event']
    # retrieving users real name for the message record
    bot_token = Team.objects.get(team_id=payload['team_id']).bot_token
    speaker = json.loads(
        requests.get(
            'https://api.slack.com/api/users.info?token={0}&user={1}'
            .format(bot_token, event['user'])
        ).text
    )
    speaker = speaker['user']['real_name']

    if event.get('thread_ts'):
        parent = Message.objects.get(ts=event['thread_ts'])
        if parent:
            reply = ReplyMessage(
                author_id=event['user'],
                author_name=speaker,
                text=event['text'],
                origin=parent,
                ts=event['ts'],
                team_id=payload['team_id'],
            )
            answer_dm(bot_token, event['text'], parent.author_id)
            reply.save()
            parent.is_answered = True
            parent.save()
    return HttpResponse(
        'Something strange happend. You better contact admin of this app.'
    )

