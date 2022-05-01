from enum import Enum

class ConfigOptionType(Enum):
    @staticmethod
    def _convert2str(v: any) -> str:
        try: return str(v)
        except: return ''
    @staticmethod
    def _convert2int(v: any) -> int:
        try: return int(v)
        except: return 0
    @staticmethod
    def _convert2float(v: any) -> float:
        try: return float(v)
        except: return 0.0
    @staticmethod
    def _convert2list(v: any) -> list:
        try: return [token.strip() for token in str(v).split(',')]
        except: return []
    @staticmethod
    def _parseCmdString(v: any) -> list[str]:
        import shlex
        try: return shlex.split(str(v))
        except: return []

    str = _convert2str
    int = _convert2int
    float = _convert2float
    list = _convert2list
    command = _parseCmdString

class ConfigOption:
    def __init__(self, _key : str, _val : any, _type : ConfigOptionType = ConfigOptionType.str, _mandatory : bool = False):
        self.configKey : str = _key
        self.mandatory : bool = _mandatory
        self.type : ConfigOptionType = _type
        self.value = self.setValue(_val)

    def setValue(self, _val : str):
        self.value = self.type(_val)

    def getValue(self):
        return self.value

    def __str__(self):
        return '{}{} => {}'.format(self.configKey, '*' if self.mandatory else '', self.value)
    def __repr__(self):
        return self.getValue()