#!/usr/bin/env python
# pylint: disable=C0116,W0613

import logging, configparser, datetime as dt

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
    'COMMANDINIT': ConfigOption('CommandInit', '', ConfigOptionType.str),
    'COMMAND': ConfigOption('CommandNgrok', '', ConfigOptionType.command),
    'NGROKAPI': ConfigOption('NgrokAPIKey', '', ConfigOptionType.str),
    'TIMEOUT': ConfigOption('DefaultTimeout', '10', ConfigOptionType.float),
    'CMDADDITIONAL': ConfigOption('CommandAdditional', '', ConfigOptionType.str),
}




def isInWhiteList(id : int) -> bool:
    return str(id) in configMain['WHITELIST'].value

def notInWhiteList(id : int) -> int:
    logger.info('Non-white listed try: id={}'.format(id))
    return ConversationHandler.END


def removeJobIfExists(name: str, ctx: CallbackContext) -> bool:
    curJobs = ctx.job_queue.get_jobs_by_name(name)
    if not curJobs:
        return False
    for job in curJobs:
        job.schedule_removal()
    return True

def exposeHomeAssistant(upd: Update, ctx: CallbackContext) -> int:
    if not isInWhiteList(upd.effective_user.id):
        return notInWhiteList(upd.effective_user.id)

    # Figure out proper timeout value
    timeout = float(configHA['TIMEOUT'].getValue())
    if len(ctx.args):
        timeoutFailed = False
        try:
            timeout = float(ctx.args[0])
        except:
            timeoutFailed = True
        if timeoutFailed or timeout < 0.5 or timeout > 1440:
            upd.message.reply_text('The timeout value should be an integer from 1 to 1440 (in minutes)')
            return CNVSTATE_WAITING_FOR_COMMAND

    # Expose HA
    success = ngrok.RunNgrok(configHA['COMMAND'].getValue(), configHA['NGROKAPI'].getValue())
    if not success:
        upd.message.reply_text('Problems with exposing HA')
        return CNVSTATE_WAITING_FOR_COMMAND

    # Safety check using ngrok API
    link = ngrok.GetNgrokLink(configHA['NGROKAPI'].getValue())
    if not len(link):
        successTerminate = ngrok.StopNgrok(configHA['NGROKAPI'].getValue())
        if successTerminate:
            upd.message.reply_text('Couldn\'t get ngrok link. HA is back hidden')
        else:
            upd.message.reply_text('Executed ngrok, although couldn\'t get ngrok link and couldn\'t terminate ngrok back. HA is likely left exposed!')
        return CNVSTATE_WAITING_FOR_COMMAND

    # Setup timer for hiding
    def stopNgrok(ctx: CallbackContext) -> None:
        if ngrok.StopNgrok(configHA['NGROKAPI'].getValue()):
            ctx.bot.send_message(ctx.job.context, text='HA has just been hidden by timeout.')
        else:
            ctx.bot.send_message(ctx.job.context, text='Problems hiding HA by timeout. HA is likely left exposed.')
    jobName = '{}:hideha'.format(upd.effective_user.id)
    ifJobRemoved = removeJobIfExists(jobName, ctx)
    ctx.job_queue.run_once(stopNgrok, int(timeout * 60), context=upd.effective_chat.id, name=jobName)

    # Run additional command
    successAddCmd = False
    if 'CMDADDITIONAL' in configHA:
        successAddCmd = ngrok.RunCommand(repr(configHA['CMDADDITIONAL']).format(link))

    upd.message.reply_text('Successfully exposed HA for {} minutes.{}{}'
                                .format(timeout,
                                        '\nInfiny successfully updated!' if successAddCmd else '',
                                        '\nPrevious timer has been removed' if ifJobRemoved else ''))
    upd.message.reply_text(link)

    return CNVSTATE_WAITING_FOR_COMMAND

def hideHomeAssistant(upd: Update, ctx: CallbackContext) -> int:
    if not isInWhiteList(upd.effective_user.id):
        return notInWhiteList(upd.effective_user.id)

    success = ngrok.StopNgrok(configHA['NGROKAPI'].getValue())
    ifJobRemoved = False
    if success:
        jobName = '{}:hideha'.format(upd.effective_user.id)
        ifJobRemoved = removeJobIfExists(jobName, ctx)
    upd.message.reply_text('{}{}'.format('Successfully hidden HA' if success else 'Problems with hiding HA',
                                         '\nPrevious timer has been removed' if ifJobRemoved else ''))

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


def init() -> bool:
    if configHA['COMMANDINIT']:
        retCmdInit = ngrok.RunCommand(configHA['COMMANDINIT'].getValue())
        logger.info('Running init command [HA]: ...{}'.format('done' if retCmdInit else 'failed'))
    return True

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

    if not init():
        logger.error('Initialization failed. Execution stopped')
        return

    # TG Bot related stuff
    updater = Updater(configMain['TOKEN'].getValue())
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