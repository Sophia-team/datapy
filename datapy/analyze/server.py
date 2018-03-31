class server():
    def __init__(self):
        self._analyzer=analyser()
        self._recomender=recommender()
        self._types_and_roles=None
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
        self._types_and_roles, self._missing=self._analyzer.types_and_roles_prediction(self._data)
        return self._types_and_roles, self._missing
    
    def AnalyseMarkedData(self, data_markers):
        self._data_desctiption, self._one_factor, self._unique_factor, time=self._analyzer.analyse_marked_data(self._data, data_markers)
        return self._data_desctiption, self._one_factor, self._unique_factor, time
    
    def FindCombinations(self):
        return self._analyzer.find_combinations()
    
    def FindUsersCombination(self, users_combination):
        return self._analyzer.find_users_combination(users_combination)
    
    def OptimezeRulesDR(self, param_max_dr, dr_column='DR', ar_column='AR'):
        return self._analyzer.optimize_rules_dr(param_max_dr, dr_column, ar_column)
    
    def OptimezeRulesAR(self, param_min_ar, dr_column='DR', ar_column='AR'):
        return self._analyzer.optimize_rules_ar(param_min_ar, dr_column, ar_column)
    
    
    
    #Блок генератора правил
    
    def RecomendOneFactorRules(self, characteristic_columns=[]):
        if self._types_and_roles is None:
            raise Exception('Предварительно необходимо проанализировать столбцы и присвоить им роли методом AnalyseMarkedData')
        
        potential_targets=[tr for tr in self._types_and_roles if tr.role==VariableRoleEnum.TARGET]
        
        if not len(potential_targets)==1:
            raise Exception('Целевой столбец не задан')
        target_field=potential_targets[0].name
        #если пользователь не передал значений, анализируем всё
        if len(characteristic_columns)==0:
            characteristic_columns=[tr.name for tr in self._types_and_roles if tr.role==VariableRoleEnum.VALUE_COLUMN]
            
        return self._recomender.RecommendRules(self._data, characteristic_columns, target_field)
    
    
    def RecomendMultyFactorRules(self, characteristic_columns=[]):
        if self._types_and_roles is None:
            raise Exception('Предварительно необходимо проанализировать столбцы и присвоить им роли методом AnalyseMarkedData')
        
        potential_targets=[tr for tr in self._types_and_roles if tr.role==VariableRoleEnum.TARGET]
        
        if not len(potential_targets)==1:
            raise Exception('Целевой столбец не задан')
        target_field=potential_targets[0].name
        #если пользователь не передал значений, анализируем всё
        if len(characteristic_columns)==0:            
            characteristic_columns=[tr.name for tr in self._types_and_roles if tr.role==VariableRoleEnum.VALUE_COLUMN]
          
        return self._recomender.RecommendMultiRules(self._data, characteristic_columns, target_field)
    
    
    
