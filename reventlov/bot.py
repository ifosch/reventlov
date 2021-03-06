import os
import logging

from telegram import ParseMode
from telegram.ext import Updater, CommandHandler

from reventlov.bot_plugins import BotPlugins, get_list_from_environment

logger = logging.getLogger(__name__)


class Bot(object):
    def __init__(self):
        self.updater = Updater(token=os.getenv('TELEGRAM_BOT_TOKEN'))
        self.admins = get_list_from_environment('TELEGRAM_BOT_ADMINS')
        self.dispatcher.add_handler(CommandHandler('start', self.start))
        self.dispatcher.add_handler(CommandHandler('help', self.help))
        self.dispatcher.add_handler(CommandHandler('settings', self.settings))
        self.dispatcher.add_handler(CommandHandler(
            'enable_plugin',
            self.enable_plugin,
            pass_args=True,
        ))
        self.dispatcher.add_handler(CommandHandler(
            'disable_plugin',
            self.disable_plugin,
            pass_args=True,
        ))
        self.plugins = BotPlugins(self.dispatcher)

    @property
    def name(self):
        return self.bot.get_me()['first_name']

    @property
    def username(self):
        return self.bot.get_me()['username']

    @property
    def bot(self):
        return self.updater.bot

    @property
    def dispatcher(self):
        return self.updater.dispatcher

    @property
    def start_message(self):
        msg = f'I am {self.name} (@{self.username})'
        features_msg = ''
        for feature_desc in self.plugins.feature_descs:
            features_msg = f'{features_msg}\n- {feature_desc}'
        msg += features_msg
        return msg

    @property
    def help_message(self):
        msg = 'I am offering the following:' \
              f'\n-/start: Greeting and list of features provided.' \
              f'\n-/help: Help about my features.' \
              f'\n-/settings: View my settings.'
        return msg

    @property
    def admin_help_message(self):
        msg = f'\n-/enable\_plugin: `plugin_name` Enable `plugin_name`' \
              f'\n-/disable\_plugin: `plugin_name` Disable `plugin_name`'
        return msg

    @property
    def plugin_help_messages(self):
        msg = ''
        for command, message in self.plugins.command_descs.items():
            msg = f'{msg}\n-{command}: {message}'
        return msg

    @property
    def disabled_plugins(self):
        return ', '.join(sorted(self.plugins.disabled_plugins))

    @property
    def enabled_plugins(self):
        return ', '.join(sorted(self.plugins.enabled_plugins))

    def start(self, bot, update):
        '''
        Greeting and list of features I am providing.

        The list of features are including the feature descriptions of all
        the plugins loaded.
        '''
        bot.send_message(
            chat_id=update.message.chat_id,
            text=self.start_message,
            parse_mode=ParseMode.MARKDOWN,
        )

    def help(self, bot, update):
        '''
        Help about my features.

        The list might include many different kinds of help text from all the
        different plugins loaded.
        '''
        msg = self.help_message
        if update.message.from_user.username in self.admins:
            msg += self.admin_help_message
        msg += self.plugin_help_messages
        bot.send_message(
            chat_id=update.message.chat_id,
            text=msg,
            parse_mode=ParseMode.MARKDOWN,
        )

    def settings(self, bot, update):
        '''
        View my settings.

        These settings can include loaded plugins' settings.
        '''
        msg = 'Here is a list of my settings:' \
              f'\n- `enabled_plugins`: {self.enabled_plugins}' \
              f'\n- `disabled_plugins`: {self.disabled_plugins}'
        bot.send_message(
            chat_id=update.message.chat_id,
            text=msg,
            parse_mode=ParseMode.MARKDOWN,
        )

    def enable_plugin(self, bot, update, args):
        '''
        Enable a disabled plugin

        Enable one of the disabled plugins.
        '''
        msg = ''
        if update.message.from_user.username in self.admins:
            if len(args) == 1:
                if args[0] in self.disabled_plugins:
                    self.plugins.enable(args[0])
                    msg = f'Plugin {args[0]} enabled'
                else:
                    msg = f'Plugin {args[0]} is not disabled'
            else:
                msg = 'You must specify which plugin you want to enable'
        else:
            msg = 'You must be admin to enable plugins'
        bot.send_message(
            chat_id=update.message.chat_id,
            text=msg,
        )

    def disable_plugin(self, bot, update, args):
        '''
        Disable an enabled plugin

        Disable one of the enable plugins.
        '''
        msg = ''
        if update.message.from_user.username in self.admins:
            if len(args) == 1:
                if args[0] in self.enabled_plugins:
                    self.plugins.disable(args[0])
                    msg = f'Plugin {args[0]} disabled'
                else:
                    msg = f'Plugin {args[0]} is not enabled'
            else:
                msg = 'You must specify which plugin you want to disable'
        else:
            msg = 'You must be admin to enable plugins'
        bot.send_message(
            chat_id=update.message.chat_id,
            text=msg,
        )

    def run(self):
        logger.info(f'I am {self.name} (@{self.username})')
        self.updater.start_polling()
