from reader import Reader
from demand import Demand
from link import Link
from file_writer import FileWriter
import copy
from math import ceil

class BrutteForse:
    def __init__(self, demands):
        self.link_lambda = []
        self. link_fibre = []
        self.res_list = []
        self.solutions = {}
        self.solution = []
        self.population = []
        self.best_loads = []
        self.cost_function = []
        self.best_solutions = []
        self.best_cost_function = float('inf')
        for i in range(0,len(demands)):
            self.solutions[i+1] = []

    def run(self, demands, links):
        self.get_lambda_fibres(links)
        self.link_in_demand(demands, links)
        k = list(self.solutions.keys())
        i = 0
        for demand in demands:
            self.partial(int(demand.volume),int(demand.volume), 0, len(demand.paths)-1, [])
            self.solutions[k[i]] = copy.deepcopy(self.solution)
            del self.solution[:]
            i += 1
        self.getAllSolutionsIter()
        self.find_write_best()
        self.write_all()
        return

    def partial(self, volume, max_volume, level, max_level, trace):
        volumes = list(range(int(volume), -1, -1))
        for i in volumes:
            t = copy.deepcopy(trace)
            t.append(i)
            if level < max_level:
                self.partial(volume-i, max_volume, level+1, max_level,t)
            elif sum(t) == max_volume:
                self.solution.append(t)

    def get_lambda_fibres(self, links):
        for link in links:
            self.link_lambda.append(int(link.lambda_number))
            self.link_fibre.append(int(link.fibre_number))

    def getAllSolutionsIter(self):
        d_keys = list(self.solutions.keys())
        self.population = copy.deepcopy(self.solutions[d_keys[0]])
        l = []
        i = 0
        for d in d_keys[1:]:
            for e in self.population:
                for u in self.solutions[d]:
                    if i == 0:
                        l.append([e] + [u])
                    else:
                        l.append(e + [u])
            del self.population[:]
            i = 1
            for e in l:
                self.population.append(e)
            del l[:]

    def find_write_best(self):
        for s in self.population:
            loads = self.count_load(s)
            load = sum(loads)
            cfs = []
            i = 0
            for ld in loads:
                cfs.append(ceil(ld/self.link_lambda[i]) - self.link_fibre[i])
            cf = sum(cfs)
            if self.best_cost_function > cf:
                self.best_cost_function = copy.deepcopy(cf)
                self.best_load = load
                del self.best_solutions[:]
                self.best_solutions.append(s)
                del self.best_loads[:]
                self.best_loads.append(loads)
            elif self.best_cost_function == cf:
                self.best_solutions.append(s)
                self.best_loads.append(loads)
        fw_best = FileWriter('bf_best')
        for k in range(len(self.best_solutions)):
            self.write_solution(fw_best, self.best_loads[k], self.best_solutions[k])
        fw_best.close()
        return

    def write_all(self):
        fw_all = FileWriter('bf_all')
        i = 1
        for s in self.population:
            loads = self.count_load(s)
            cfs = []
            j = 0
            for ld in loads:
                cfs.append(ceil(ld/self.link_lambda[j]) - self.link_fibre[j])
                j += 1
            cf = sum(cfs)
            line = 'Population ' + str(i) + ' : ' + 'Link load: ' + str(sum(loads)) + ' Cost function sum: ' \
                   + str(cf)
            fw_all.write(line)
            line = str(s)
            fw_all.write(line)
            i += 1
        fw_all.close()

    def count_load(self, population):
        """Oblicza obciazenie kazdego lacza dla podanej populacji"""
        load = []
        i = 0
        for l in self.ld:
            load.append(0)
            for e in self.ld[l]:
                load[-1] += population[e[0]-1][e[1]-1]
            i += 1
        return load

    def link_in_demand(self, demands, links):
        """ Tworzenie slownika   wystepowan krawedzi w sciezkach zapotrzebowan"""
        self.ld = dict.fromkeys(list(range(1, len(links)+1)))
        for l in range(1, len(links)+1):
            self.ld[l] = []
        for l in range(1, len(links)+1):
            j = 1
            for d in demands:
                for k in d.paths.keys():
                    for i in range(len(d.paths[k])):
                        if int(d.paths[k][i]) == l:
                            # demand position
                            self.ld[l].append([j, int(k)])
                j += 1
        return self.ld

    def printSolutions(self):
        print('Solution n [demand(path[i]) for i in len(paths)]')
        for k in list(self.solutions.keys()):
            print('demand ',k)
            i = 1
            for s in self.solutions[k]:
                print('Solution ',i,': ',s)
                i +=1
            print('-------')
        return

    def countSolutions(self):
        counter = 1
        for k in self.solutions.keys():
            counter *= len(self.solutions[k])
        print(counter)
        return counter


    def write_solution(self, fw, loads, offspring):
        """Zapis do pliku informacji o najlepszej generacji(zgodnie z podanym formatem)"""
        fw.write(str(len(self.ld)))
        i = 0
        for link in self.ld:
            line = str(link)+' '+str(loads[i])+' '+str(ceil(loads[i]/self.link_lambda[i]))
            fw.write(line)
            i += 1
        fw.write('\n')
        fw.write(str(len(offspring)))

        for d in range(len(offspring)):
            line = str(d+1) + ' ' + str(len(offspring[d]))
            fw.write(line)
            for e in offspring[d]:
                fw.write_add_to_line(str(e)+' ')
            fw.write(' ')
        fw.write(' ')
