from reader import Reader
from demand import Demand
from link import Link
import random
from file_writer import FileWriter
from time import time
from math import ceil
import copy
from numpy import argmax, argmin, argsort

class Evolutionary:
    """implementacja algorytmu ewolucyjnego."""
    def __init__(self, popul_num, cross_prop, mut_prop, seed, gen_num=-1, max_mut=-1, success_max=-1, t_lim=-1):
        """Inicjalizacja danych algorytmu. Obowckowe parametry licznosc popoulacji, prawdopodobienstwa krzyzowania i
        mutacji i ziarno generatora liczb pseudolosowych, zeby algorytm dziaal poprawnie nalezy podac chociazby jeden
        kruterium stopu (wiekszy od 0)
        """
        random.seed(seed)

        self.cross_prop = cross_prop
        self.mut_prop = mut_prop
        self.link_lambda = []
        self.link_fibre = []

        self.gen_num = gen_num
        self.max_mut = max_mut
        self.success_max = success_max
        self.t_lim = t_lim

        self.gen_counter = 0
        self.success_counter = 0
        self.mut_counter = 0
        self.t_start = 0

        self.population = []
        self.offsprings = []
        self.population_size = popul_num
        self.loads = []
        self.cost_function_val = []
        self.best_offspring = []
        self.best_generation = 0
        self.best_load = [float("inf")]
        self.best_loads = []

    def no_stop_cr(self):
        if self.gen_num < 0 and self.max_mut < 0 and self.t_lim < 0 and self.success_max < 0:
            return True
        else:
            return False

    def stop_cr(self):
        """ Kryterium stopu, w progamie moga istniec wszystnie kryteria naraz, wybrane lub jeden.
             Jesli jeden z kryteriow nie jest spelniony, algorytmkonczy dzialanie
        """
        if (self.gen_counter > self.gen_num) and (self.gen_num >= 0):
            print("maximum generation")
            return False
        elif (self.mut_counter > self.max_mut) and (self.max_mut >= 0):
            print("maximum mutation",self.mut_counter)
            return False
        elif (time()-self.t_start > self.t_lim) and (self.t_lim >= 0):
            print("maximum time")
            return False
        elif (self.success_counter > self.success_max) and (self.success_counter >= 0):
            print("maximum success")
            return False
        else:
            return True

    def run(self, demands, links):
        """
        Wykonanie algorytmu zgoble z podanym schematem dzalania
        """
        if self.no_stop_cr():
            return

        self.get_lambda_fibres(links)
        self.fw = FileWriter('ev_generations')
        self.link_in_demand(demands, links)
        self.generate(demands, self.population_size)
        self.t_start = time()
        while self.stop_cr() == True:
            self.reproduce()
            self.crossover_randomly()
            self.mutate_randomly3()
            self.population += copy.deepcopy(self.offsprings)
            del self.offsprings[:]
            self.count_link_load()
            self.kick()
            self.success_counter *= self.select_best()
            self.success_counter += 1
            self.gen_counter += 1
            self.write_best()
        self.count_best_load()
        self.fw.close()
        self.write_best_solution()


    def reproduce(self):
        """
        Do reprodulcji wybieramy polope populacji popszedniej generacji(losowo wybrane elementy elementy)
        """
        pop_number = random.randrange(int(self.population_size/2))
        pops = random.sample(list(range(self.population_size)), pop_number)
        for pop in pops:
            self.offsprings.append(self.population[pop])


    def mutate_randomly3(self):
        """
        Losowo wybieramy osobnia i chromosom, ktory bedzie mutowany, i z zadanym przez uzytkownika prawdopodobienstwem
        chromosom jest mutowamy
        """
        if len(self.offsprings) == 0:
            return
        posx = random.randrange(int(len(self.offsprings)))
        posy = random.randrange(len(self.offsprings[posx]))
        if random.random() < self.mut_prop:
            self.mut_counter += 1
            fm = self.offsprings[posx][posy]
            self.offsprings[posx][posy] = self.mutate(sum(fm), len(fm))


    def mutate(self, d, n):
        """ Mutacja chromosomu"""
        r = []
        v = 0
        t = [0] * d + [1] * (n - 1)
        random.shuffle(t)
        t += [1]
        for i in t:
            if i == 0:
                v += 1
            else:
                r.append(v)
                v = 0
        random.shuffle(r)
        return r

    def crossover_randomly(self):
        """ Tworzymy 2 podzbory i wybieramy losowo osobnikow do krzyzowania i z podanym przwdopodobienstwem
            odbywa sie krzyzowanie
        """
        pop_len = len(self.offsprings) - len(self.offsprings) % 2
        pop_range = list(range(0, pop_len))
        for i in range(0, pop_len, 2):
            if random.random() < self.cross_prop:
                i = random.choice(pop_range)
                pop_range.remove(i)
                j = random.choice(pop_range)
                pop_range.remove(j)
                self.crossover(i, j)

    def crossover(self, posx, posy):
        """ do zbioru potomkow jest dodany nowy osobnik czyje chromosomy sa wynikiem krzyzowania"""
        tr = []
        for i in range(len(self.offsprings[posx])):
            if random.random() > 0.5:
                tr.append(self.offsprings[posx][i])
            else:
                tr.append(self.offsprings[posy][i])
        self.offsprings.append(tr)

    def count_link_load(self):
        """Oblicza sumaryczne obciazenie laczy dla kazdej populacji"""
        del self.loads[:]
        del self.cost_function_val[:]
        cf = []
        for pop in self.population:
            self.loads.append(0)
            i = 0
            for l in self.ld:
                for e in self.ld[l]:
                    self.loads[-1] += pop[e[0]-1][e[1]-1]
                cf.append(ceil(self.loads[-1]/self.link_lambda[i]) - self.link_fibre[i])
            i += 1
            self.cost_function_val.append(sum(cf))
            del cf[:]

    def get_lambda_fibres(self, links):
        for link in links:
            self.link_lambda.append(int(link.lambda_number))
            self.link_fibre.append(int(link.fibre_number))

    def count_best_load(self):
        """Oblicza obciazenie kazdego lacza dla najlepszej populacji"""
        i = 0
        for l in self.ld:
            self.best_loads.append(0)
            for e in self.ld[l]:
                self.best_loads[-1] += self.best_offspring[0][e[0]-1][e[1]-1]
            # self.best_loads[-1] = ceil(self.best_loads[-1]/self.link_lambda[i]) - self.link_fibre[i]
            i += 1

    def kick(self):
        """Usuwa najgorsze osobniki populacji tak aby licznosc populacji byla stala"""
        while len(self.population) > self.population_size:
            worst_load_inx = int(argmax(self.cost_function_val))
            del self.cost_function_val[worst_load_inx]
            del self.loads[worst_load_inx]
            del self.population[worst_load_inx]



    def select_best(self):
        """Wybiera najlepszego osobnika genercji, jesli jest on lepszy od popszednio wybranego osoblika to zamienia go"""
        best_load_inx = int(argmin(self.cost_function_val))
        if self.loads[best_load_inx] < self.best_load[0]:
            self.best_offspring.insert(0, self.population[best_load_inx])
            self.best_load[0] = self.loads[best_load_inx]
            self.best_generation = self.gen_counter
            return 0
        return 1

    def generate(self, demands, N):
        """ Twozenie pocztkowej populacji """
        for i in range(N):
            self.population.append(self.generate_pop(demands))

    def generate_pop(self, demands):
        """ Losowe twozenie osobnika poczatkowej populacji  """
        pop = []
        for d in demands:
            v = self.mutate(int(d.volume), len(d.paths))
            pop.append(v)
        return pop

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

    def write_best(self):
        """Zapis do pliku 5 najlepszych osobnikow generacji"""
        best5_list = argsort(self.loads)[:5]
        i = 0
        line = 'Generation: ' + str(self.gen_counter)
        self.fw.write(line)
        for b in best5_list:
            line = str('Solution: ' + str(i) + ' Link load: ' + str(self.loads[b])
                        + ' Cost function sum: ' + str(self.cost_function_val[b]))
            self.fw.write(line)
            line = str(self.population[b])
            self.fw.write(line)
            i += 1
        self.fw.write('\n')

    def printPopulation(self):
        """Wydruk kontrolny"""
        print('Solution n [demand(path[i]) for i in len(paths)]')
        for s in self.population:
            print(s)
        print('=======')

    def printOffspring(self):
        """Wydruk kontrolny"""
        print('Solution n [demand(path[i]) for i in len(paths)]')
        for s in self.offsprings:
            print(s)
        print('=======')

    def printBestSolution(self):
        """Wydruk kontrolny"""
        print('Best is ', self.best_offspring, ' with load ', self.best_load)

    def write_best_solution(self):
        """Zapis do pliku informacji o najlepszej generacji(zgodnie z podanym formatem)"""
        fw = FileWriter('ev_best_solution')
        fw.write(str(len(self.ld)))
        i = 0
        for link in self.ld:
            line = str(link)+' '+str(self.best_loads[i])+' '+str(ceil(self.best_loads[i]/self.link_lambda[i]))
            fw.write(line)
            i += 1
        fw.write(' ')
        fw.write(str(len(self.best_offspring[0])))

        for d in range(len(self.best_offspring[0])):
            line = str(d+1) + ' ' + str(len(self.best_offspring[0][d]))
            fw.write(line)
            for e in self.best_offspring[0][d]:
                fw.write_add_to_line(str(e)+' ')
            fw.write(' ')
        fw.close()