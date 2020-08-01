"""
Optimizes the parameters of a strategy
"""

import numpy as np
import pandas as pd

def mutate_individual(individual, gene_mutation_probability, 
	n_genes=3, gene_ranges=[(0, 5), (4, 8), (1, 5)]):
		""" Takes an individual and mutates it gene by gene.
		The probability that a gene will be mutated is `gene_mutation_probability` 
		"""
		new_individual = []
		for i in range(0, n_genes):
				gene = individual[i]
				if np.random.random() < gene_mutation_probability:
					if np.random.random() < 0.5:
						gene = np.random.randint(gene_ranges[i][0], gene_ranges[i][1])
					else:
  						# Fancy mutation that adds or subtracts a little bit to/from 
							# the existing gene, instead of giving a completely random value
							left_range = gene_ranges[i][0]
							right_range = gene_ranges[i][1]
							gene_dist = right_range - left_range
							gene_mid = gene_dist / 2
							x = individual[i] + gene_dist/3 * (2 * np.random.random() - 1)
							if x > right_range:
								x = (x - left_range) % gene_dist + left_range
							elif x < left_range:
								x = (right_range - x) % gene_dist + left_range

							gene = int(x)

				new_individual.append(gene)
		
		return new_individual

def mutate_population(population, 
	mutation_probability=0.3, gene_mutation_probability=0.2, 
	n_genes=3, gene_ranges=[(0, 5), (4, 8), (1, 5)]):
		""" Takes a population and mutates its individuals,
		with a mutation rate of `mutation_probability`. 
		
		IE (`mutation_probability` * 100)% of the population 
		will mutate """

		mutated_pop = []
		for individual in population:
				new_individual = individual
				if np.random.random() < mutation_probability:
						new_individual = mutate_individual(
							individual, gene_mutation_probability, n_genes, gene_ranges)

				mutated_pop.append(new_individual)
		
		return mutated_pop

def mate_parents(parents, n_offspring):
		""" Takes a list of parents and mates them, creating `n_offspring` offspring """		
		n_parents = len(parents)
	
		offspring = []
		for i in range(n_offspring):
				random_dad = parents[np.random.randint(low = 0, high = n_parents - 1)]
				random_mom = parents[np.random.randint(low = 0, high = n_parents - 1)]
				
				dad_mask = np.random.randint(0, 2, size = np.array(random_dad).shape)
				mom_mask = np.logical_not(dad_mask)
				
				child = np.add(np.multiply(random_dad, dad_mask), np.multiply(random_mom, mom_mask))

				offspring.append(child)

		return offspring

def create_individual(n_genes=3, gene_ranges=[(0, 5), (4, 8), (1, 5)]):
		""" Returns a randomly-generated individual with `n_genes` genes, 
		each gene ranging between the values defined in `gene_ranges` """

		individual = []
		for i in range(0, n_genes):
				gene = np.random.randint(gene_ranges[i][0], gene_ranges[i][1])
				individual.append(gene)
		
		return individual

def create_population(n_individuals, n_genes=3, gene_ranges=[(0, 5), (4, 8), (1, 5)]):
		""" Creates a population of n_individuals """
		pop = []
		for i in range(0, n_individuals):
				pop.append(create_individual(n_genes, gene_ranges))

		return pop

def select_best(population, fitness_function, n_best):
		""" Selects the best `n_best` individuals in a population 
		(those with the highest fitness)"""
		fitnesses = []
		for idx, individual in enumerate(population):
				individual_fitness = fitness_function(individual)
				fitnesses.append([idx, individual_fitness])
		
		print('generations best is: {}, generations worst is: {}'.format(pd.DataFrame(fitnesses)[1].max(), pd.DataFrame(fitnesses)[1].min()))
		
		costs_tmp = pd.DataFrame(fitnesses).sort_values(by = 1, ascending = False).reset_index(drop=True)
		selected_parents_idx = list(costs_tmp.iloc[:n_best,0])
		selected_parents = [parent for idx, parent in enumerate(population) if idx in selected_parents_idx]
		
		return selected_parents

def gen_algo(
	fitness_function,
	n_generations, 
	generation_size = 500,
	n_genes = 3, 
	gene_ranges=[(0, 5), (4, 8), (1, 5)], 
	mutation_p = 0.3, 
	gene_mutation_p = 0.2, 
	n_select_best = 100): 
		""" 
		Runs a genetic algorithm to optimize `fitness_function`.

		Params
		--
			`n_generations` the number of generations it runs for
			`generation_size` the number of individuals in a generation
			`n_genes` the number of genes in an individual
			`gene_ranges` the ranges for each gene
			`mutation_p` the probability that an individual will be mutated
			`gene_mutation_p` the probability that a gene will be mutated 
				(assuming that the individual was selected for mutation)
			`n_select_best` the number of individuals that are selected
				to mate in order to create the next generation
		
		Returns
		--
			The best individual solution
		"""
		print("Generating Random Population:")
		parent_gen = create_population(generation_size, n_genes, gene_ranges)
		print(parent_gen)
		print("done")
		print("Going through generations:")
		for it in range(n_generations):
				print("\n~~~~~ Generation", it)
				print("\nSelecting the best")
				parent_gen = select_best(parent_gen, fitness_function, n_best = n_select_best)
				print("\nMating the parents")
				parent_gen = mate_parents(parent_gen, n_offspring = generation_size)
				print("\nMutating the offspring")
				parent_gen = mutate_population(parent_gen, mutation_p, gene_mutation_p,
					n_genes, gene_ranges)
		
		print("\nAll time Best 10:")
		best_children = select_best(parent_gen, fitness_function, n_best = 10)
		print(best_children)
		return best_children