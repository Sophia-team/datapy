from enum import Enum

class VariableTypeEnum(Enum):
    Binary=1
    Nominal=2
    Scale=3
    Ordinal=4
    DateID=5
    Unknown=100
    
class VariableRoleEnum(Enum):
    REJECTED = 1
    FIXED_RULE = 2 
    HISTORICAL_RULE = 3
    POTENCIAL_RULE = 4
    NTU = 5
    ID = 6
    DATE = 7
    CREDITED = 8
    APPROVED = 9
    NEW_CREDIT = 10
    VALUE_COLUMN=51
    TARGET = 99
    
    
class VariableDescription(object):
    
    def __init__(self, variable_name, variable_type = VariableTypeEnum.Unknown , variable_role= VariableRoleEnum.REJECTED):
        self.name=variable_name
        self.type=variable_type
        self.role=variable_role