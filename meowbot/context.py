from meowbot.api import SlackApi
from meowbot.util import quote_user_id


class CommandContext:

    def __init__(self, data):
        self._data = data
        self._event = SlackEvent(self._data['event'])
        self._command, self._args = self._parse_command()

    def _parse_command(self):
        if not hasattr(self.event, 'text'):
            return None, None

        split_text = self.event.text.split(' ')
        quoted_bot_user = quote_user_id(self.bot_user)

        # If message starts with `@meowbot`
        if split_text[0] == quoted_bot_user:
            if len(split_text) > 1:
                _, command, *args = split_text
            else:
                return None, None
        # If message is direct IM, no `@meowbot` necessary
        elif self.event.channel_type == 'im':
            command, *args = split_text
        else:
            return None, None

        return (command.lower(), args)

    @property
    def event(self):
        return self._event

    @property
    def command(self):
        return self._command

    @property
    def args(self):
        return self._args

    @property
    def bot_user(self):
        return self._data['authed_users'][0]

    @property
    def api(self):
        if not hasattr(self, '_api'):
            self._api = SlackApi.from_command_context(self)
        return self._api

    def __getattr__(self, item):
        if item not in self._data:
            raise AttributeError(item)
        return self._data[item]


class SlackEvent:

    def __init__(self, event):
        self._event = event

    def __getattr__(self, item):
        if item not in self._event:
            raise AttributeError(item)
        return self._event[item]


class InteractivePayload:

    def __init__(self, data):
        self._data = data
        self._actions = [
            SlackAction(action)
            for action in self._data['actions']
        ]

    @property
    def api(self):
        if not hasattr(self, '_api'):
            self._api = SlackApi.from_interactive_payload(self)
        return self._api

    @property
    def actions(self):
        return self._actions

    def __getattr__(self, item):
        if item not in self._data:
            raise AttributeError(item)
        return self._data[item]


class SlackAction:

    def __init__(self, action):
        self._action = action
        self._command, self._action_name = self._parse_action_id()

    def _parse_action_id(self):
        return self.action_id.split(':')

    @property
    def command(self):
        return self._command

    @property
    def action_name(self):
        return self._action_name

    def __getattr__(self, item):
        if item not in self._action:
            raise AttributeError(item)
        return self._action[item]
