import pandas as pd
import numpy as np

# возвращает списки имен по ролям
def role_lists(types_and_roles):
    target = list()
    rules = list()
    approved = list()
    ntu = list()
    credited = list()
    new_credit = list()
    for i in range(0,len(types_and_roles)):
        if types_and_roles[i].role == VariableRoleEnum.TARGET:
            target = types_and_roles[i].name
        elif types_and_roles[i].role == VariableRoleEnum.APPROVED:
            approved = types_and_roles[i].name
        elif types_and_roles[i].role == VariableRoleEnum.NTU:
            ntu = types_and_roles[i].name
        elif types_and_roles[i].role == VariableRoleEnum.CREDITED:
            credited = types_and_roles[i].name
        elif types_and_roles[i].role == VariableRoleEnum.NEW_CREDIT:
            new_credit = types_and_roles[i].name
        elif types_and_roles[i].role == VariableRoleEnum.FIXED_RULE or types_and_roles[i].role == VariableRoleEnum.HISTORICAL_RULE:
            rules.append(types_and_roles[i].name)
    return target, rules, approved, ntu, credited, new_credit 


def analyse_marked_data(data_path, data_markers):
    target, rules, approved, ntu, credited, new_credit = role_lists(data_markers) 
    data = pd.read_csv(data_path, delimiter=delimiter, decimal=decimal)
    columns = ['# отказов', '% отказов', 'дефолтность', '# новых кредитов', '% новых кредитов', 'уровень одобрения', 'уровень NTU',     'дефолтность по одобренным', 'дефолтноть по выданным']
    df = pd.DataFrame(index=rules, columns=columns)
    
    
    #TODO написать тело
    '''историческая ситуация определяется переменными  FIXED RULE,  HISTORICAL RULE, NTU(опционально), TARGET, 
    по этим данным надо посчитать число записей, уровень одобрения, уровень NTU(если есть), уровень риска по одобренным, 
    уровень риска по выданным (если указано NTU) и  нужно отобразить однофакторные и уникальные отказы по исторической ситуации'''
    return 0