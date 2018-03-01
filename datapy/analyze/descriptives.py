import pandas as pd
import numpy as np
import itertools as it

###################################################
## public методы
####################################################
    
#Предполагает роли и типы данных в файле
def types_and_roles_prediction(file_path, delimiter=';', decimal='.'):
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
        #TODO подумать, что тут можно делать
        raise
        return None
 

#Возвращает таблицу со статистикой по отказам и прочему
def analyse_marked_data(data_path, data_markers, delimiter=';', decimal='.'):
    target, rules, approved, ntu, credited, new_credit = _role_lists(data_markers) 
    data = pd.read_csv(data_path, delimiter=delimiter, decimal=decimal)   
    
    #опсиательные по всем данным
    data_desctiption=_data_stats(data, target, approved, ntu, credited)
    
    #однофакторные отказы
    one_factor_analysis = _rules_stats(data, target, rules, approved, ntu, credited, new_credit)
    
    #уникальные отказы
    unique_factor_data=data.copy()
    unique_factor_data['active_rules']=0
    for rule in rules:
        unique_factor_data['active_rules']+=unique_factor_data[rule]
    unique_factor_data = unique_factor_data.loc[unique_factor_data['active_rules']==1]
    unique_factor_analysis = _rules_stats(unique_factor_data, target, rules, approved, ntu, credited, new_credit, data.shape[0])
                                  
    return data_desctiption, one_factor_analysis, unique_factor_analysis

def find_combinations(data_path, data_markers):
    target, rules, approved, ntu, credited, new_credit = _role_lists(data_markers) 
    data = pd.read_csv(data_path, delimiter=';', decimal=',')  
    #максимлаьная длина комбинации
    possible_combinations=list()
    max_len=int(len(rules))
    for i in range(max_len):
        combs=it.combinations(rules, i)
        for c_j in combs:
            possible_combinations.append(c_j)
    
    combinations_stats=list()
    # перебираем все комбинации
    for combination in possible_combinations:
        comb_columns=list(combination)
        
        #считаем сколько правил из комбинации сработало
        data['comb_result']=0
        for col in comb_columns:
            data['comb_result']+=data[col]        
        #DR
        default_rate=None if target is None else data.loc[data['comb_result']<1, target].mean()
        
        
        #AR
        data.loc[data['comb_result']>1, 'comb_result']=1
        approve_rate=None if target is None else 1-data['comb_result'].mean()
        
        #добавляем полученные рейты к результату с указанием комбинации
        combinations_stats.append([combination, approve_rate, default_rate])
    
    return combinations_stats


def optimize_rules_dr(rules_combinations, param_max_dr):
    #только те комбинации, где DR ниже порога
    fitting_combinations=[rc for rc in rules_combinations if rc[2]<=param_max_dr]
    #сортируем отобранные комбинации по AR по убыванию
    fitting_combinations.sort(key=lambda x: x[1], reverse=True)
    return fitting_combinations

def optimize_rules_ar(rules_combinations, param_min_ar):
    #только те комбинации, где AR ниже порога
    fitting_combinations=[rc for rc in rules_combinations if rc[1]>=param_max_dr]
    #сортируем отобранные комбинации по DR по возрастанию
    fitting_combinations.sort(key=lambda x: x[2])
    return fitting_combinations
    

###################################################
## private методы
####################################################

def _data_stats(data, target, approved, ntu, credited):
    columns=['уровень одобрения (%)', 'уровень NTU (%)', 'дефолтность по одобренным (%)', 'дефолтность по выданным (%)']
    df = pd.DataFrame(columns=columns)    
    # Approve rate
    ar = None if approved is None else data[approved].mean()
    # уровень NTU 
    ntu_rate = None if ntu is None else data[ntu].mean()
    # default rate among approved
    approved_dr=None if (approved is None) or (target is None) else data.loc[(data[approved]==1),target].mean()  
    # Дефолтность по выданным
    given_dr=None if (credited is None) or (target is None) else data.loc[(data[credited]==1), target].mean() 
    
    df.loc['Total']=[ar*100, ntu_rate*100, approved_dr*100, given_dr*100]
    return df

#считает статистики по правилам
def _rules_stats(data, target, rules, approved, ntu, credited, new_credit, full_data_len=None):
    if full_data_len is None or full_data_len < 1:
        columns = ['# отказов', '% отказов', 'дефолтность (%)', '# новых кредитов', '% новых кредитов']
    else:
        columns = ['# отказов', '% отказов от отказов по никальным правилам', '% отказов от общего числа', 'дефолтность (%)', '# новых кредитов', '% новых кредитов']
    df = pd.DataFrame(columns=columns)
    # для каждого правила заполняем таблицу
    for rule in rules:
        #Отказы: число и доля
        rej_num = data[rule].sum()
        rej_share = data[rule].mean()
        # default rate
        dr = None if target is None else data.loc[data[rule]==1,target].mean()
        
        #Новые кредиты: число и доля
        new_credits_num = None if new_credit is None else data.loc[data[rule]==1,new_credit].sum()
        new_credits_share = None if new_credit is None else data.loc[data[rule]==1,new_credit].mean()
        
        
        if full_data_len is None or full_data_len<1:
            df.loc[rule]=[rej_num,rej_share*100, dr*100, new_credits_num, new_credits_share]
        else:
            # reject rate in full dataset
            rej_share_total=rej_num/full_data_len
            df.loc[rule]=[rej_num,rej_share*100, rej_share_total*100, dr*100, new_credits_num, new_credits_share]

    return df

# возвращает списки имен по ролям
def _role_lists(types_and_roles):
    target = None
    rules = list()
    approved = None
    ntu = None
    credited = list()
    new_credit = None
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


#определяет тип переменной
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
        #TODO: распознавание дат
        return VariableTypeEnum.Nominal

#определяет роль переменной
def _predict_role(data_series):
    column_name=data_series.name
    if 'r_'==column_name[:2]:
        return VariableRoleEnum.HISTORICAL_RULE
    if 'CREDITED'==column_name.upper():
        return VariableRoleEnum.CREDITED
    if 'APPROVE' in column_name.upper():
        return VariableRoleEnum.APPROVED
    if 'TARGET' in column_name.upper() or 'OBJECTIVE' in column_name.upper():
        return VariableRoleEnum.TARGET
    if 'NEW_CREDIT' in column_name.upper():
        return VariableRoleEnum.NEW_CREDIT
    if 'NTU' in column_name.upper():
        return VariableRoleEnum.NTU
    #TODO распознавание
    return VariableRoleEnum.REJECTED
