import random

import requests
import validators

import meowbot
from meowbot.commands import SimpleResponseCommand
from meowbot.context import CommandContext
from meowbot.models import Cat
from meowbot.util import get_cat_api_key


class CatCommand(SimpleResponseCommand):

    name = 'cat'
    help = '`cat [name] [number]`: gives one cat'
    aliases = ['getcat']

    def get_message_args(self, context: CommandContext):
        if len(context.args) in (1, 2):
            name = context.args[0]
            num_photos = Cat.query.filter_by(
                name=name.lower()
            ).count()
            if num_photos == 0:
                return {'text': f'No cats named {name} registered'}
            if len(context.args) == 2:
                number = context.args[1]
                if not number.isnumeric():
                    return {
                        'text': 'Second argument must be a number. '
                                f'Got `{number}`'
                    }
                number = int(number)
                if 1 <= number <= num_photos:
                    offset = number - 1
                else:
                    offset = random.randint(0, num_photos - 1)
            else:
                offset = random.randint(0, num_photos - 1)
            row = Cat.query.filter_by(
                name=name.lower()
            ).order_by(Cat.id).limit(1).offset(offset).one()
            return {
                'blocks': [
                    {
                        'type': 'image',
                        'image_url': row.url,
                        'alt_text': name,
                    }
                ]
            }
        return {
            'blocks': [
                {
                    'type': 'image',
                    'image_url': requests.head(
                        'https://api.thecatapi.com/v1/images/search?'
                        'format=src&mime_types=image/gif',
                        headers={'x-api-key': get_cat_api_key()}
                    ).headers['Location'],
                    'alt_text': 'cat gif'
                }
            ]
        }


class AddCat(SimpleResponseCommand):

    name = 'addcat'
    help = '`addcat [name] [photo_url]`: add a cat to the database'
    aliases = ['addacat', 'registercat']

    def get_message_args(self, context: CommandContext):
        if len(context.args) != 2:
            return {
                'text': 'Expected 2 args (name, url). '
                        f'Got {len(context.args)}',
                'thread_ts': context['event']['ts']
            }
        name, url = context.args
        # TODO: figure out why URLs are wrapped in <>.
        url = url[1:-1]
        if not validators.url(url):
            return {
                'text': f'`{url}` is not a valid URL',
                'thread_ts': context['event']['ts']
            }
        row = Cat(name=name.lower(), url=url)
        meowbot.db.session.add(row)
        meowbot.db.session.commit()
        return {
            'attachments': [
                {
                    'text': f'Registered {name}!',
                    'image_url': url,
                }
            ],
            'thread_ts': context['event']['ts']
        }


class ListCats(SimpleResponseCommand):

    name = 'listcats'
    help = '`listcats`: see all cats available for the `cat` command'

    def get_message_args(self, context: CommandContext):
        rows = meowbot.db.session.query(Cat.name).distinct()
        names = ', '.join((row.name for row in rows))
        return {'text': f'Cats in database: {names}'}


class RemoveCat(SimpleResponseCommand):

    name = 'removecat'
    help = '`removecat [name] [number]`: delete a photo from the database'

    def get_message_args(self, context: CommandContext):
        if len(context.args) != 2:
            return context.api.chat_post_message({
                'text': 'Expected 2 args (name, number). '
                        f'Got {len(context.args)}'
            })
        name, number = context.args
        if not number.isnumeric():
            return {
                'text': f'Second argument must be a number. Got `{number}`'
            }
        offset = int(number)
        if offset <= 0:
            return {
                'text': f'Number must be > 0. Got `{offset}`'
            }
        row = Cat.query.filter_by(
            name=name.lower()
        ).order_by(
            Cat.id
        ).limit(1).offset(
            offset - 1
        ).one_or_none()
        if row is None:
            return {
                'text': 'No matching rows'
            }
        meowbot.db.session.delete(row)
        meowbot.db.session.commit()
        return {'text': 'Successfully removed!'}
