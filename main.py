#!/usr/bin/env python
# pylint: disable=C0116,W0613

import logging, configparser
from enum import Enum
from typing import Dict

from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

CNVSTATE_BLACKLISTED, CNVSTATE_WAITING_FOR_COMMAND = range(2)

reply_keyboard = [
    ['Age', 'Favourite colour'],
    ['Number of siblings', 'Something else...'],
    ['Done'],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)




class ConfigOptionType(Enum):
    str, int, float, list = range(4)

class ConfigOption:
    def __init__(self, _key : str, _val : any, _type : ConfigOptionType = ConfigOptionType.str, _mandatory : bool = False):
        self.configKey : str = _key
        self.mandatory : bool = _mandatory
        self.type : ConfigOptionType = _type
        self.value = self.setValue(_val)

    def setValue(self, _val : str):
        if self.type == ConfigOptionType.str:
            self.value = str(_val)
        elif self.type == ConfigOptionType.int:
            self.value = int(_val)
        elif self.type == ConfigOptionType.float:
            self.value = float(_val)
        elif self.type == ConfigOptionType.list:
            self.value = [token.strip() for token in _val.split(',')]
        else:
            raise Exception('Unknown type')

    def __str__(self):
        return '{}{} => {}'.format(self.configKey, '*' if self.mandatory else '', self.value)


configMain = {
    'TOKEN': ConfigOption('BotToken', '', ConfigOptionType.str, True),
    'WHITELIST': ConfigOption('WhiteList', '', ConfigOptionType.list)
}

configHA = {
    'EXPOSETIME': ConfigOption('DefaultExposeTime', '10', ConfigOptionType.int)
}

def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f'{key} - {value}' for key, value in user_data.items()]
    return "\n".join(facts).join(['\n', '\n'])

def isInWhiteList(id : int) -> bool:
    return str(id) in configMain['WHITELIST'].value

def notInWhiteList(id : int) -> int:
    logger.info('Non-white listed try: id={}'.format(id))
    return ConversationHandler.END


def startCmd(upd: Update, ctx: CallbackContext) -> int:
    if not isInWhiteList(upd.effective_user.id):
        return notInWhiteList(upd.effective_user.id)

    upd.message.reply_text('Hi! You can lucky to be in a white list. You /help to check all available commands')

    return CNVSTATE_WAITING_FOR_COMMAND

def fallbackMsg(upd: Update, ctx: CallbackContext) -> int:
    if not isInWhiteList(upd.effective_user.id):
        return notInWhiteList(upd.effective_user.id)

    upd.message.reply_text('I don\'t understand what you need. Use /help to check all available commands')

def helpCmd(upd: Update, ctx: CallbackContext) -> int:
    if not isInWhiteList(upd.effective_user.id):
        return notInWhiteList(upd.effective_user.id)

    reply: str = 'You can use the following commands:'
    for cmd, (_, description) in commands.items():
        reply += '\n/{} - {}'.format(cmd, description)
    upd.message.reply_text(reply)

    return CNVSTATE_WAITING_FOR_COMMAND

def exposeHomeAssistant(upd: Update, ctx: CallbackContext) -> int:
    if not isInWhiteList(upd.effective_user.id):
        return notInWhiteList(upd.effective_user.id)

    upd.message.reply_text('This command exposes HA')

    return CNVSTATE_WAITING_FOR_COMMAND

def hideHomeAssistant(upd: Update, ctx: CallbackContext) -> int:
    if not isInWhiteList(upd.effective_user.id):
        return notInWhiteList(upd.effective_user.id)

    upd.message.reply_text('This command hides HA')

    return CNVSTATE_WAITING_FOR_COMMAND

def notImplementedCmd(upd: Update, ctx: CallbackContext) -> int:
    if not isInWhiteList(upd.effective_user.id):
        return notInWhiteList(upd.effective_user.id)

    upd.message.reply_text('Unfortunately this command is not implemented yet!')

    return CNVSTATE_WAITING_FOR_COMMAND

commands = {
    'help': (helpCmd, 'Shows this help message'),
    'exposeha': (exposeHomeAssistant, 'Exposes the Home Assistant web page to the internet and sends back the access link.'
                                      ' You can pass the number of minutes to keep HA exposed (default'),
    'hideha': (hideHomeAssistant, 'Hides the Home Assistant web page from the internet.'),
    'reloadconfig': (notImplementedCmd, 'Reloads the configuration file'),
}

def processConfig() -> bool:
    try:
        cnf = configparser.ConfigParser()
        cnf.read('secrets.ini')
    except:
        logger.error('Could not read secrets.ini')
        return False

    def processSection(configuration: configparser.ConfigParser, section: str, configDict: dict) -> bool:
        if not (section in configuration.sections()):
            logger.error('Processing config file error: No [{}] section found'.format(section))
            return False
        cnfSection = configuration[section]

        for k, v in configDict.items():
            if v.configKey in cnfSection:
                configDict[k].setValue(cnfSection[v.configKey])
            elif v.mandatory:
                logger.error('Processing config file error: The {} mandatory key in section [{}] was not found'.format(v.configKey, section))
                return False

        return True

    processSection(cnf, 'Main', configMain)
    processSection(cnf, 'HA', configHA)
    return True

def main() -> None:
    if not processConfig():
        logger.error('Processing config file failed. Execution stopped')
        return

    updater = Updater(configMain['TOKEN'].value)
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', startCmd)
        ],
        states={
            CNVSTATE_WAITING_FOR_COMMAND:
                [CommandHandler(cmd, fn) for cmd, (fn, _) in commands.items()] + [
                    MessageHandler(Filters.all, fallbackMsg)
                ],
        },
        fallbacks=[
            MessageHandler(Filters.all, fallbackMsg)
        ],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()