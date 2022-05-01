#!/usr/bin/env python
# pylint: disable=C0116,W0613

import logging, configparser

from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

import ngrok
from config_options import *


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)




CNVSTATE_BLACKLISTED, CNVSTATE_WAITING_FOR_COMMAND = range(2)

configMain = {
    'TOKEN': ConfigOption('BotToken', '', ConfigOptionType.str, True),
    'WHITELIST': ConfigOption('WhiteList', '', ConfigOptionType.list)
}
configHA = {
    'COMMAND': ConfigOption('CommandNgrok', '', ConfigOptionType.command),
    'NGROKAPI': ConfigOption('NgrokAPIKey', '', ConfigOptionType.str),
    'TIMEOUT': ConfigOption('DefaultTimeout', '10', ConfigOptionType.int),
    'CMDADDITIONAL': ConfigOption('CommandAdditional', '', ConfigOptionType.str),
}




def isInWhiteList(id : int) -> bool:
    return str(id) in configMain['WHITELIST'].value

def notInWhiteList(id : int) -> int:
    logger.info('Non-white listed try: id={}'.format(id))
    return ConversationHandler.END



def exposeHomeAssistant(upd: Update, ctx: CallbackContext) -> int:
    if not isInWhiteList(upd.effective_user.id):
        return notInWhiteList(upd.effective_user.id)

    success = ngrok.RunNgrok(configHA['COMMAND'].value, configHA['TIMEOUT'].value)
    if not success:
        upd.message.reply_text('Problems with exposing HA')
        return CNVSTATE_WAITING_FOR_COMMAND

    link = ngrok.GetNgrokLink(configHA['NGROKAPI'].value)
    if not len(link):
        successTerminate = ngrok.StopNgrok(configHA['NGROKAPI'].value)
        if successTerminate:
            upd.message.reply_text('Couldn\'t get ngrok link. HA is back hidden')
        else:
            upd.message.reply_text('Executed ngrok, although couldn\'t get ngrok link and couldn\'t terminate ngrok back. HA is likely exposed!')
        return CNVSTATE_WAITING_FOR_COMMAND

    successAddCmd = False
    if 'CMDADDITIONAL' in configHA:
        successAddCmd = ngrok.RunAdditionalCommand(configHA['CMDADDITIONAL'], link)

    upd.message.reply_text('Successfully exposed HA for {} minutes. HA will be hidden at {}.{}'.format(configHA['TIMEOUT'].value, '(calculate yourself)',
                           '\nInfiny successfully updated!' if successAddCmd else ''))
    upd.message.reply_text(link)

    return CNVSTATE_WAITING_FOR_COMMAND

def hideHomeAssistant(upd: Update, ctx: CallbackContext) -> int:
    if not isInWhiteList(upd.effective_user.id):
        return notInWhiteList(upd.effective_user.id)

    success = ngrok.StopNgrok(configHA['NGROKAPI'].value)
    upd.message.reply_text('Successfully hidden HA' if success else 'Problems with hiding HA')

    return CNVSTATE_WAITING_FOR_COMMAND

def notImplementedCmd(upd: Update, ctx: CallbackContext) -> int:
    if not isInWhiteList(upd.effective_user.id):
        return notInWhiteList(upd.effective_user.id)

    upd.message.reply_text('Unfortunately this command is not implemented yet!')

    return CNVSTATE_WAITING_FOR_COMMAND

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

    retMain = processSection(cnf, 'Main', configMain)
    retHA = processSection(cnf, 'HA', configHA)

    return retMain and retHA

def main() -> None:
    # Configuration file
    if not processConfig():
        logger.error('Processing config file failed. Execution stopped')
        return

    # TG Bot related stuff
    updater = Updater(configMain['TOKEN'].value)
    updater.dispatcher.add_handler(ConversationHandler(
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
    ))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()