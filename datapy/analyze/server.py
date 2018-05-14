import re

class server():
    def __init__(self):
        self._analyzer=analyser()
        self._recomender=recommender()
        self._data=None
        print('Server initialised')
    
    #задаёт файл, с которым осуществляется работа
    def setfile(self, file_path,delimiter=';', decimal='.', encoding='utf-8'):
        self._delimiter=delimiter
        self._decimal=decimal
        self._file_path=file_path
        self._encoding=encoding 
        self._readFile()
        print('File set')
        
    def _readFile(self):
        self._data=data=pd.read_csv(self._file_path, delimiter=self._delimiter, decimal=self._decimal,encoding=self._encoding)
        
        
    def PredictTypesAndRoles(self):
        types_and_roles, missing=self._analyzer.types_and_roles_prediction(self._data)
        return types_and_roles, missing
    
    def AnalyseMarkedData(self, data_markers):
        data_desctiption, data_desctiption_m, one_factor, unique_factor, time, ch_rules, p_rule, const_columns, val_columns = self._analyzer.analyse_marked_data(self._data, data_markers)
        return data_desctiption, data_desctiption_m, one_factor, unique_factor, time, ch_rules, p_rule, const_columns, val_columns
    
    def DeleteMissing(self, missing_threshold=0.05):
        self._data, deleted_columns = self._analyzer.delete_missing(missing_threshold)
        return deleted_columns
    
    def FindCombinations(self):
        return self._analyzer.find_combinations()
    
    def FindUsersCombination(self, users_combination):
        return self._analyzer.find_users_combination(users_combination)
    
    def OptimezeRulesDR(self, param_max_dr, dr_column='DR', ar_column='AR'):
        return self._analyzer.optimize_rules_dr(param_max_dr, dr_column, ar_column)
    
    def OptimezeRulesAR(self, param_min_ar, dr_column='DR', ar_column='AR'):
        return self._analyzer.optimize_rules_ar(param_min_ar, dr_column, ar_column)
    
    #Кодировка категориальных столбцов
    def EncodeCategories(self, categories):
        result = {}
        for c in categories:
            if self._data[c].dtype == 'O':
                result[c] = {v : i for i, v in enumerate(self._data[c].unique())}
                for i, v in enumerate(self._data[c].unique()):
                    self._data.loc[self._data[c] == v, c] = i
        return result
    
    
    
    #Блок генератора правил
    
    def RecomendOneFactorRules(self, characteristic_columns=[]):
        if self._analyzer._input_data_markers is None:
            raise Exception('Предварительно необходимо проанализировать столбцы и присвоить им роли методом AnalyseMarkedData')
        
        potential_targets=[tr for tr in self._analyzer._input_data_markers if tr.role==VariableRoleEnum.TARGET]
        approve_flags=[tr for tr in self._analyzer._input_data_markers if tr.role==VariableRoleEnum.APPROVED]
        
        if not len(potential_targets)==1:
            raise Exception('Целевой столбец не задан')
        target_field=potential_targets[0].name
        

        if len(approve_flags) == 1:
            approve_field=approve_flags[0].name
        else:
            approve_field = None
        
        #если пользователь не передал значений, анализируем всё
        if len(characteristic_columns)==0:
            characteristic_columns=[tr.name for tr in self._analyzer._input_data_markers if tr.role==VariableRoleEnum.VALUE_COLUMN]
            
        return self._recomender.RecommendRules(self._data, characteristic_columns, target_field, approve_field)
    
    
    def RecomendMultyFactorRules(self, characteristic_columns=[]):
        if self._analyzer._input_data_markers is None:
            raise Exception('Предварительно необходимо проанализировать столбцы и присвоить им роли методом AnalyseMarkedData')
        if len(characteristic_columns)>0:
            if len(set(characteristic_columns))==1:
                raise Exception('Для поиска мультправил, необходимо выбрать больше, чем одно поле')
        
        potential_targets=[tr for tr in self._analyzer._input_data_markers if tr.role==VariableRoleEnum.TARGET]
        
        if not len(potential_targets)==1:
            raise Exception('Целевой столбец не задан')
        target_field=potential_targets[0].name
        #если пользователь не передал значений, анализируем всё
        if len(characteristic_columns)==0:            
            characteristic_columns=[tr.name for tr in self._analyzer._input_data_markers if tr.role==VariableRoleEnum.VALUE_COLUMN]
          
        return self._recomender.RecommendMultiRules(self._data, characteristic_columns, target_field)
    
    def Bin_new_rules(self, full_onefactor_rules):
        #вызываем метод, применяющий правила к данным. Он генерирует новые столбцы и возарщает список добавленных переменных
        potential_rules=self._recomender.New_rule_bin(full_onefactor_rules, self._data)
        #добавляем список новых потенциальных данных к старому списку маркеров
        self._analyzer._input_data_markers=self._analyzer._input_data_markers+potential_rules
        #теперь наша аналайзер знает об этих правилах
        #возвращаем на всякий случай полный список правил (маркеры разметки), который можно кинуть в анализатор повторно для получения полного анализа опять
        return self._analyzer._input_data_markers,potential_rules
    
    
    #Парсинг правила
    def ParseRule(self, user_rule):
        or_rules=user_rule.split('OR')
        and_rules=list()
        for or_rule in or_rules:
            and_rules.append(or_rule.split('AND'))

        def _parseStatement(statement):
            sign=re.findall('<=|>', statement)[0]
            args=re.split(sign,statement)
            rule=[args[0].strip(), float(args[1].strip()), True if sign=='>' else False]
            return rule

        formal_rules=list()
        for and_rule in and_rules:
            and_rule_formal=list()
            for rule_part in and_rule:
                formal_rule=_parseStatement(rule_part)
                and_rule_formal.append(formal_rule)
            formal_rules.append(and_rule_formal)

        return formal_rules
    
    
    
