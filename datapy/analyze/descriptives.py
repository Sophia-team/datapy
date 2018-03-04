import pandas as pd
import numpy as np
import itertools as it
import time

class analyser():
    
    def __init__(self):
        self._input_data=None
        self._input_data_markers=None
        self._combinations=None
        
        
        
    def reset():
        self._input_data=None
        self._input_data_markers=None
        self._combinations=None


    ###################################################
    ## public методы
    ####################################################

    #Предполагает роли и типы данных в файле
    def types_and_roles_prediction(self, file_path, delimiter=';', decimal='.'):
        try:
            result=list()
            data=pd.read_csv(file_path, delimiter=delimiter, decimal=decimal)
            ind = list(data.columns)
            columns = ['# пропущенных', '% пропущенных']
            miss = pd.DataFrame(columns=columns)
            for column in data.columns:
                var_description=VariableDescription(column)
                var_description.type=self._predict_type(data[column])
                var_description.role=self._predict_role(data[column])            
                result.append(var_description)

            cnt = float(data.iloc[:,0].count())
            for i in ind:
                cnt_mis = data[i].isnull().sum()
                pr_mis = data[i].isnull().sum()/ cnt *100
                miss.loc[i] = [cnt_mis, pr_mis]
            return result, miss
        except:
            #TODO подумать, что тут можно делать
            raise
            return None


    #Возвращает таблицу со статистикой по отказам и прочему
    def analyse_marked_data(self, data_path, data_markers, delimiter=';', decimal='.'):
        self._input_data_markers=data_markers
        target, rules, fixed_rule,  approved, ch_rules, ntu, credited, new_credit = self._role_lists(data_markers) 
        data = pd.read_csv(data_path, delimiter=delimiter, decimal=decimal)   
        self._input_data=data.copy()
        
        #опсиательные по всем данным
        data_desctiption, k_dr =self._data_stats(data, target, approved, ntu, credited)

        #однофакторные отказы
        one_factor_analysis = self._rules_stats(data, target, rules, approved, ntu, credited, new_credit)

        #уникальные отказы
        unique_factor_data=data.copy()
        unique_factor_data['active_rules']=0
        for rule in rules:
            unique_factor_data['active_rules']+=unique_factor_data[rule]
        unique_factor_data = unique_factor_data.loc[unique_factor_data['active_rules']==1]
        unique_factor_analysis = self._rules_stats(unique_factor_data, target, rules, approved, ntu, credited, new_credit, data.shape[0])

        return data_desctiption, one_factor_analysis, unique_factor_analysis

    #Считаем статистику по всем комбинациям
    def find_combinations(self):
        '''
        Считаем статистику по всем комбинациям
        '''
        if self._input_data is None or self._input_data_markers is None:
            raise Exception('Необходимо предварительно провести анализ')
        
        if not self._combinations is None:
            return self._combinations
        

        target, rules, fixed_rule,  approved, ch_rules, ntu, credited, new_credit = self._role_lists(self._input_data_markers) 
        data=self._input_data.copy()
        
        data_desctiption, k_dr =self._data_stats(data, target, approved, ntu, credited)
        #максимлаьная длина комбинации
        possible_combinations=list()
        max_len=int(len(ch_rules))
        for i in range(max_len+1):
            combs=it.combinations(ch_rules, i)
            for c_j in combs:
                possible_combinations.append(c_j)
        # перебираем все комбинации
        combinations_stats=list()
        for combination in possible_combinations:
            comb_columns=list(combination)
            df = data.copy()
            df['comb_result']=0
            for col in comb_columns:
                df.loc[df[col] == 1, col] = 0
            df['comb_result'] = df[rules].sum(axis=1)
            df.loc[(df['comb_result'] < 1) & (df[approved] != 1), approved] = 1

            #DR approved
            default_rate_ap = df.loc[df[approved] == 1, target].mean()
            #DR credited
            default_rate_cr = default_rate_ap * k_dr
            #AR
            approve_rate = df[approved].mean()

            #добавляем полученные рейты к результату с указанием комбинации
            combinations_stats.append([combination, approve_rate, default_rate_ap, default_rate_cr])


        result_df=pd.DataFrame(data=[cs[1:] for cs in combinations_stats], index=[cs[0] for cs in combinations_stats], columns=['AR','DR among aproved','DR'])
        self._combinations=result_df.copy()
        return result_df

    
    def find_users_combination(self, users_combination):
        if self._combinations is None:
            combinations=self.find_combinations()
        else:
            combinations=self._combinations.copy()
        
        search_result=combinations.loc[[self._slice_in_array(users_combination, a)  for a in combs.index.values]]
        
        return search_result

    def optimize_rules_dr(self, param_max_dr, dr_column='DR', ar_column='AR'):
        if self._combinations is None:
            raise Exception('Необходимо предварительно провести анализ')
        rules_combinations=self._combinations.copy()
        #только те комбинации, где DR ниже порога
        fitting_combinations=rules_combinations.loc[rules_combinations[dr_column]<=param_max_dr]
        #сортируем отобранные комбинации по AR по убыванию
        return fitting_combinations.sort_values(by=ar_column,ascending=False)


    def optimize_rules_ar(self, param_min_ar, dr_column='DR', ar_column='AR'):
        if self._combinations is None:
            raise Exception('Необходимо предварительно провести анализ')
        rules_combinations=self._combinations.copy()
        #только те комбинации, где AR ниже порога
        fitting_combinations=rules_combinations.loc[rules_combinations[ar_column]>=param_min_ar]
        #сортируем отобранные комбинации по DR по возрастанию
        return fitting_combinations.sort_values(by=dr_column,ascending=True)


    ###################################################
    ## private методы
    ####################################################
                         
    def _slice_in_array(self, sl, arr):
        for s in sl:
            if not s in arr:
                return False
        return True

    def _data_stats(self, data, target, approved, ntu, credited):
        columns=['уровень одобрения (%)', 'уровень NTU (%)', 'дефолтность по одобренным (%)', 'дефолтность по выданным (%)']
        df = pd.DataFrame(columns=columns)    
        # Approve rate
        ar = None if approved is None else data[approved].mean()
        cnt_apr = None if approved is None else data[approved].sum()
        # уровень NTU 
        ntu_rate = None if ntu is None else data[ntu].sum()/float(cnt_apr)
        # default rate among approved
        approved_dr=None if (approved is None) or (target is None) else data.loc[(data[approved]==1),target].mean()  
        # Дефолтность по выданным
        given_dr=None if (credited is None) or (target is None) else data.loc[(data[credited]==1), target].mean() 
        # Отношение дефолтности по выданным к дефолтности по одобренным
        k_dr = given_dr / approved_dr

        df.loc['Total']=[ar*100, ntu_rate*100, approved_dr*100, given_dr*100]
        return df, k_dr 

    #считает статистики по правилам
    def _rules_stats(self, data, target, rules, approved, ntu, credited, new_credit, full_data_len=None):
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
                rej_share_total=float(rej_num)/full_data_len
                df.loc[rule]=[rej_num,rej_share*100, rej_share_total*100, dr*100, new_credits_num, new_credits_share]

        return df

    # возвращает списки имен по ролям
    def _role_lists(self, types_and_roles):
        target = None
        rules = list()
        fixed_rule = list()
        ch_rules = list()
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
            elif types_and_roles[i].role == VariableRoleEnum.FIXED_RULE or types_and_roles[i].role == VariableRoleEnum.HISTORICAL_RULE or types_and_roles[i].role == VariableRoleEnum.POTENCIAL_RULE:
                rules.append(types_and_roles[i].name)
                if types_and_roles[i].role == VariableRoleEnum.FIXED_RULE:
                    fixed_rule.append(types_and_roles[i].name)
                else:
                    ch_rules.append(types_and_roles[i].name)
        return target, rules, fixed_rule,  approved, ch_rules, ntu, credited, new_credit


    #определяет тип переменной
    def _predict_type(self, data_series):
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
    def _predict_role(self, data_series):
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

    
    
'''
  #Считаем статистику по всем комбинациям это вариант с возратом включенных
def find_combinations2(data_path, data_markers):
    target, rules, fixed_rules,  approved, ch_rules, ntu, credited, new_credit = _role_lists(data_markers) 
    data = pd.read_csv(data_path, delimiter=';', decimal=',')  
    #Описание данных ('уровень одобрения (%)', 'уровень NTU (%)', 'дефолтность по одобренным (%)', 'дефолтность по выданным (%)')
    # и Отношение дефолтности по выданным к дефолтности по одобренным
    data_desctiption, k_dr =_data_stats(data, target, approved, ntu, credited)
    
    # Список возможных комбинаций
    possible_combinations=list()
    max_combination_len=int(len(ch_rules))
    for i in range(max_combination_len+1):
        combs=it.combinations(ch_rules, i)
        for c_j in combs:
            possible_combinations.append(set(fixed_rules+list(c_j)))
    
    # Перебираем все комбинации
    combinations_stats=list()
    for combination in possible_combinations:
        comb_columns=list(combination)
        data['comb_result']=0
        #считаем, сколько из правил в комбинации сработало на наблюдении
        for col in comb_columns:
            data['comb_result']+=data[col]
        # Помечаем условно аппрувнутыми тех, по кому ни одно правило из комбинации не сработало
        data['approved_in_combination']=0
        data.loc[(data['comb_result'] < 1),'approved_in_combination']=1

        

        #DR among approved in combination 
        default_rate_ap = data.loc[data['approved_in_combination'] == 1, target].mean()
        #DR credited 
        default_rate_cr = default_rate_ap * k_dr
        #AR in combination
        approve_rate = data['approved_in_combination'].mean()

        #добавляем полученные рейты к результату с указанием комбинации 
        combinations_stats.append([combination, approve_rate, default_rate_ap, default_rate_cr])
        
    result_df=pd.DataFrame(data=[cs[1:] for cs in combinations_stats], index=[cs[0] for cs in combinations_stats], columns=['AR','DR among aproved','DR'])
    return result_df
    '''