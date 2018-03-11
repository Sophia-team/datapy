import numpy as np
import pandas as pd
import math as math
from sklearn import tree
from sklearn.linear_model import LinearRegression

class recommender():
    
    def __init__(self):
        pass

       
    def RecommendRules(self, data, characteristic_columns, default_flag):
        result=list()
        for column in characteristic_columns:
            one_factor_data=data[[column, default_flag]].dropna()
            gaps=self._GetRule(one_factor_data[column], one_factor_data[default_flag])
            one_factor_threshold=self._GetThreshold(gaps)
            trend, new_dr =self._GetTrend(one_factor_data[column], one_factor_data[default_flag], one_factor_threshold)
            old_dr=data[default_flag].mean()            
            dr_delta=0 if new_dr is None else old_dr-new_dr
            result.append([column, one_factor_threshold,trend, dr_delta])
        return result
    
    def RecommendMultiRules(self, data, characteristic_columns, default_flag):
        result=list()
        multi_factor_data=data[characteristic_columns+[default_flag]].dropna()
        a=self._GetMultiRule(multi_factor_data, default_flag)
        
        return a
    
    
    def _GetMultiRule(self, data, target, depth=2):
        dt=tree.DecisionTreeClassifier(max_depth=depth, min_samples_leaf=int(0.2*len(data[target])))
        dt.fit(data.drop([target], axis=1), data[target])
        
        nodes=dt.apply(data.drop([default_column],axis=1))
        data['node']=nodes
        node_dr=data.groupby(by='node')[target].mean()
        max_dr_node=node_dr.argmax()
        
        return max_dr_node
        pass
    
    
    
    

    def _GetRule(self, x, y, depth=1):
        dt=tree.DecisionTreeClassifier(max_depth=depth, min_samples_leaf=int(0.2*len(x)))
        dt.fit(x[:,None],y[:,None])
        gaps=self._GetGaps(dt)
        return gaps


    def _GetThreshold(self, gaps):
        if len(gaps)==2:
            return gaps[0][1]
        return None

    def _GetTrend(self, x, y, threshold):
        if threshold is None:
            return None, None
        left_rate=np.mean([y_v for x_v, y_v  in zip(x,y) if x_v<=threshold])
        right_rate=np.mean([y_v for x_v, y_v  in zip(x,y) if x_v>threshold])  
        return right_rate>=left_rate, min(left_rate, right_rate)


    def _GetGaps(self, estimator):
        maxval=100000000000000
        #Вытаскиваем границы промежутков без дублей
        threshold = self._DelDuplicates(estimator.tree_.threshold)
        #удаляем из границ -2 (искусственную границу)
        if -2 in threshold:
            threshold.remove(-2)
        #Добавляем верхнюю и нижнуюю границу, для закрытия крайних промежутков 
        threshold.append(maxval)
        threshold.append(maxval*-1)
        #отбираем все границы и сортируем
        threshold=list(set(threshold))
        threshold.sort()
        #Составляем промежуки из границ
        gaps=[]
        for i in range(len(threshold)-1):
            gaps.append([threshold[i],threshold[i+1]])
        return gaps

    #Удаляем те значения, которые встретились больше 1 раза
    def _DelDuplicates(self, arr):
        new_arr=list()
        for a in arr:
            if a in new_arr:
                new_arr.remove(a)
            else:
                new_arr.append(a)
        return new_arr


                         
    