import pandas as pd
from enum import Enum
import numpy as np

class VariableTypeEnum(Enum):
    Binary=1
    Nominal=2
    Scale=3
    Ordinal=4
    DateID=5
    Unknown=100
    
class VariableRoleEnum(Enum):
    Predictor=1
    Target=2
    DateID=3
    Unknown=100
    
class VariableDescription(object):
    
    def __init__(self, variable_name:str, variable_type:VariableTypeEnum = VariableTypeEnum.Unknown , variable_role:VariableRoleEnum = VariableRoleEnum.Unknown):
        self.name=variable_name
        self.type=variable_type
        self.role=variable_role
        

def types_and_roles_prediction(file_path:str, delimiter:str=';', decimal:str='.'):    
    try:
        result=list()
        data=pd.read_csv(file_path, delimiter=delimiter, decimal=decimal)
        for column in data.columns:
            var_description=VariableDescription(column)
            var_description.type=_predict_type(data[column])
            var_description.role=_predict_role(data[column])            
            result.append(var_description)
        return result
    except:
        raise
        print('err')
        return None
    return 0

def _predict_type(data_series):
    column_name=data_series.name
    column_type=data_series.dtype
    column_total_len=len(data_series)
    
    if column_type==np.float64 or column_type==np.int64: #Обработка числовых
        unique_values_count = len(data_series.unique())
        
        if unique_values_count == 2:
            return VariableTypeEnum.Binary
        else:
            if column_total_len / unique_values_count > 20: #значение 20 - обсуждаемое, мбм есть какие то правила уже общепринятые
                return VariableTypeEnum.Ordinal
            else:
                return VariableTypeEnum.Scale
            
        return VariableTypeEnum.Unknown
    else:  # обработка строковых (и дат - надо реализовать)
        return VariableTypeEnum.Nominal
    
def _predict_role(data_series):
    return VariableRoleEnum.Unknown