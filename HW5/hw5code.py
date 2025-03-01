import numpy as np
from collections import Counter

#неправильный вариант
# def find_best_split(feature_vector, target_vector):
#     """
#     Под критерием Джини здесь подразумевается следующая функция:
#     $$Q(R) = -\frac {|R_l|}{|R|}H(R_l) -\frac {|R_r|}{|R|}H(R_r)$$,
#     $R$ — множество объектов, $R_l$ и $R_r$ — объекты, попавшие в левое и правое поддерево,
#      $H(R) = 1-p_1^2-p_0^2$, $p_1$, $p_0$ — доля объектов класса 1 и 0 соответственно.

#     Указания:
#     * Пороги, приводящие к попаданию в одно из поддеревьев пустого множества объектов, не рассматриваются.
#     * В качестве порогов, нужно брать среднее двух сосдених (при сортировке) значений признака
#     * Поведение функции в случае константного признака может быть любым.
#     * При одинаковых приростах Джини нужно выбирать минимальный сплит.
#     * За наличие в функции циклов балл будет снижен. Векторизуйте! :)

#     :param feature_vector: вещественнозначный вектор значений признака
#     :param target_vector: вектор классов объектов,  len(feature_vector) == len(target_vector)

#     :return thresholds: отсортированный по возрастанию вектор со всеми возможными порогами, по которым объекты можно
#      разделить на две различные подвыборки, или поддерева
#     :return ginis: вектор со значениями критерия Джини для каждого из порогов в thresholds len(ginis) == len(thresholds)
#     :return threshold_best: оптимальный порог (число)
#     :return gini_best: оптимальное значение критерия Джини (число)
#     """
#     # ╰( ͡° ͜ʖ ͡° )つ──☆*:・ﾟ

#     n_obj = feature_vector.shape[0]
#     #сортирока и соответствующие значения таргета
#     sorted_feature = np.sort(feature_vector)
#     corresponding_target = np.take_along_axis(target_vector, feature_vector.argsort(), axis = 0)

#     #для каждого разбиения значения p1 и p0 в левой части
#     p1_left = corresponding_target @ (np.tril(np.ones((n_obj, n_obj))).T) / np.arange(1, n_obj +1)
#     p1_left = p1_left[:-1] # разбиение с нулем объектов
#     p0_left = 1- p1_left
    
#     #для каждого разбиения значения H для левой части
#     H_left = 1 - p1_left**2 - p0_left**2
    
#     #для каждого значения порога p1, p0, H в правой части
#     p1_right = corresponding_target @ (np.tril(np.ones((n_obj, n_obj)))) / np.arange(n_obj, 0, -1)
#     p1_right = p1_right[1:]# разбиение с нулем объектов
#     p0_right = 1- p1_right
#     H_right = 1 - p1_right**2 - p0_right**2

#     #Джини для каждого разбиения
#     ginis = - H_left * (np.arange(1, n_obj)/n_obj) - H_right * (1 - np.arange(1, n_obj)/n_obj)
    
#     #пороги как среднее от двух соседних значений признака
#     thresholds = 0.5*(sorted_feature[1:] + sorted_feature[:-1])

#     pos = np.argmax(ginis)
#     gini_best = ginis[pos]
#     threshold_best = thresholds[pos]

#     return thresholds, ginis, threshold_best, gini_best

def find_best_split(feature_vector, target_vector):
    sorted_ind = np.argsort(feature_vector)
    feat_sort = feature_vector[sorted_ind]
    target_sort = target_vector[sorted_ind]
    mask = feat_sort[1:] != feat_sort[:-1]
    threshold_vec = ((feat_sort[1:] + feat_sort[:-1]) / 2)[mask]

    R = np.size(target_sort)
    R_l_size = np.arange(1, R)
    R_l_1 = np.cumsum(target_sort)
    R_l_p1 = R_l_1[:-1] / R_l_size
    R_l_p0 = 1 - R_l_p1

    R_r_1 = R_l_1[-1] - R_l_1[:-1]
    R_r_p1 = R_r_1 / (R - R_l_size)
    R_r_p0 = 1 - R_r_p1

    gini_vec = R_l_size / R * (R_l_p0 ** 2 + R_l_p1 ** 2 - 1) + \
        (R - R_l_size) / R * (R_r_p0 ** 2 + R_r_p1 ** 2 - 1)
    gini_vec = gini_vec[mask]

    ind_best = np.argmax(gini_vec)
    threshold_best = threshold_vec[ind_best]
    gini_best = gini_vec[ind_best]

    return threshold_vec, gini_vec, threshold_best, gini_best


class DecisionTree:
    def __init__(self, feature_types, max_depth=None, min_samples_split=None,
                 min_samples_leaf=None):
        if np.any(list(map(lambda x: x != "real" and x != "categorical",
                           feature_types))):
            raise ValueError("There is unknown feature type")

        self._tree = {}
        self._feature_types = feature_types
        self._max_depth = max_depth
        self._min_samples_split = min_samples_split
        self._min_samples_leaf = min_samples_leaf
        
    def get_params(self, deep=False):
        return {'feature_types': self._feature_types, 
               'max_depth': self._max_depth, 
               'min_samples_split': self._min_samples_split,
               'min_samples_leaf': self._min_samples_leaf}

    def _fit_node(self, sub_X, sub_y, node):
        if np.all(sub_y == sub_y[0]): #==
            node["type"] = "terminal"
            node["class"] = sub_y[0]
            return

        feature_best, threshold_best, gini_best, split = None, None, None, None
        for feature in range(sub_X.shape[1]):
            #print(feature, len(self._feature_types))
            feature_type = self._feature_types[feature]
            categories_map = {}

            if feature_type == "real":
                feature_vector = sub_X[:, feature]
            elif feature_type == "categorical":
                counts = Counter(sub_X[:, feature])
                clicks = Counter(sub_X[sub_y == 1, feature])
                ratio = {}
                for key, current_count in counts.items():  # key - категория
                    if key in clicks:
                        current_click = clicks[key]
                    else:
                        current_click = 0
                    ratio[key] = current_click / current_count  # обратная дробь
                sorted_categories = sorted(ratio.keys(),
                                           key=lambda k: ratio[k])  # правильная сортировка
                categories_map = dict(zip(sorted_categories,
                                          range(len(sorted_categories))))  # правильное соответствие

                feature_vector = np.array([
                        categories_map[x] for x in sub_X[:, feature]])  # получили вектор порядковых номеров
            else:
                raise ValueError

            if len(np.unique(feature_vector)) == 1:  # не получится разбить
                continue

            _, _, threshold, gini = find_best_split(feature_vector, sub_y)
            if gini_best is None or gini > gini_best:
                feature_best = feature
                gini_best = gini
                split = feature_vector < threshold

                if feature_type == "real":
                    threshold_best = threshold
                elif feature_type == "categorical":
                    threshold_best = list(  # список подходящих категорий
                            map(lambda x: x[0], # берем первый элемент, то есть ключ - исходную категорию
                                filter(
                                        lambda x: x[1] < threshold,
                                        categories_map.items())))
                else:
                    raise ValueError

        if feature_best is None:
            node["type"] = "terminal"
            node["class"] = Counter(sub_y).most_common(1)
            return

        node["type"] = "nonterminal"

        node["feature_split"] = feature_best
        if self._feature_types[feature_best] == "real":
            node["threshold"] = threshold_best
        elif self._feature_types[feature_best] == "categorical":
            node["categories_split"] = threshold_best
        else:
            raise ValueError
        node["left_child"], node["right_child"] = {}, {}
        self.depth += 1
        self._fit_node(sub_X[split], sub_y[split], node["left_child"])
        self._fit_node(
                sub_X[np.logical_not(split)],
                sub_y[np.logical_not(split)], node["right_child"])

    def _predict_node(self, x, node):
        if(node['type'] == 'terminal'):
            return node['class']
        else:
            feature_type = self._feature_types[node['feature_split']]
            if(feature_type == 'real'):
                if(x[node['feature_split']] < node['threshold']):
                    return self._predict_node(x, node['left_child'])
                else:
                    return self._predict_node(x, node['right_child'])
            else:
                if(x[node['feature_split']] in node['categories_split']):
                    return self._predict_node(x, node['left_child'])
                else:
                    return self._predict_node(x, node['right_child'])

    def fit(self, X, y):
        self.depth = 1
        self._fit_node(X, y, self._tree)

    def predict(self, X):
        predicted = []
        for x in X:
            predicted.append(self._predict_node(x, self._tree))
        return np.array(predicted)