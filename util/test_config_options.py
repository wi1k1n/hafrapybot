import configparser
from warnings import warn
from config_options import *

configMain = {
    'TOKEN': ConfigOption('BotToken', '', ConfigOptionType.str, True),
    'WHITELIST': ConfigOption('WhiteList', '', ConfigOptionType.list)
}
configHA = {
    'COMMAND': ConfigOption('CommandNgrok', '', ConfigOptionType.list),
    'NGROKAPI': ConfigOption('NgrokAPIKey', '', ConfigOptionType.str),
    'TIMEOUT': ConfigOption('DefaultTimeout', '10', ConfigOptionType.int),
    'CMDADDITIONAL': ConfigOption('CommandAdditional', '', ConfigOptionType.str),
}

def main() -> bool:
    try:
        cnf = configparser.ConfigParser()
        cnf.read('test_config_options.ini')
    except:
        warn('Could not read secrets.ini')
        return False

    def processSection(configuration: configparser.ConfigParser, section: str, configDict: dict) -> bool:
        if not (section in configuration.sections()):
            warn('Processing config file error: No [{}] section found'.format(section))
            return False
        cnfSection = configuration[section]

        for k, v in configDict.items():
            if v.configKey in cnfSection:
                configDict[k].setValue(cnfSection[v.configKey])
            elif v.mandatory:
                warn('Processing config file error: The {} mandatory key in section [{}] was not found'.format(v.configKey, section))
                return False

        return True

    retMain = processSection(cnf, 'Main', configMain)
    retHA = processSection(cnf, 'HA', configHA)

    return retMain and retHA

if __name__ == '__main__':
    main()