# IS590PZ - Final Assignment
# Crossword-Puzzle Generator
# Group: Dennis Piehl and Xianzhuo Cao

from union_find import UnionFindSet
import numpy as np
# import matplotlib.pyplot as plt
import copy
from ast import literal_eval
from random import choice, choices
from time import sleep
import re
import pprint
from multiprocessing import Pool



def main():

	grid_dimensions = (7, 7)	# Number rows and columns in crossword puzzle grid
	black_square_density = 0.15	# [Maximum] Fraction of squares that will be black

	xw_puzzle = CrosswordPuzzle(grid_dimensions, black_square_density)

	print(xw_puzzle.empty_grid)
	print(xw_puzzle.blk_sqs_positions)

	global main_word_corpus
	word_corpus_files = [
						'./dict_sources/wordnet/index.noun.processed.txt',
						'./dict_sources/wordnet/index.adj.processed.txt',
						'./dict_sources/wordnet/index.verb.processed.txt',
						'./dict_sources/wordnet/index.adv.processed.txt',
						'./dict_sources/YAWL/yawl-0.3.2.03/word.list.processed.txt',
						# './dict_sources/SCOWL/scowl-2019.10.06/final/american-and-english.processed.txt',
						'./dict_sources/nyt-crossword-master/clues_fixed.txt'
						]
	main_word_corpus = read_word_corpus(word_corpus_files, grid_dimensions)
	size_of_corp = sum(len(main_word_corpus[k]) for k in main_word_corpus )
	print(size_of_corp)

	# main_word_corpus = sort_word_dic(main_word_corpus) # Sort main_word_corpus by its length of the hints

	# Fill grid using recursive function:
	xw_puzzle.filled_grid =	xw_puzzle.fill_grid_recursively(None, 0)
	print("DONE!")
	exit()

	return


class CrosswordPuzzle:
	"""
	Crossword Puzzle class for representing a full (unfilled or filled) crossword puzzle grid.

	Currently must be Odd x Odd length

	Rules followed:
		- All words must be >= 3 characters
		- All white spaces should be connected (no enclosed/blocked-off regions)
			* Using union-find algorithm to check this
		- All white squares must be part of BOTH an Across and Down crossing
			* There must be at least 1 white square to the left or right, AND at least 1 white sqauare to the top or bottom
	"""

	def __init__(self, dims: tuple, density: float):
		"""
		Initialize the crossword puzzle grid.

		:param dims:	Specified grid dimensions as a tuple (rows, columns).
		:param density:	Fraction of grid to set as black squares, as a float.
		:return self:	CrosswordPuzzle object.

		"""

		self.dims = dims
		self.rows = dims[0]
		self.cols = dims[1]
		self.ifcenter_black = False # Patrick: I add a new parameter to determine if the center is black
		self.density = density	# Should add a check to make sure the density is low enough that a "valid puzzle" is still possible (i.e., that no two-letter words are present, etc.)
		self.num_squares = dims[0]*dims[1]
		self.num_blk_sqs = round(self.num_squares * self.density) # If odd, center square must be made black; if even, no need.
		if self.num_blk_sqs % 2 != 0: # [FOR TESTING PURPOSES] If odd number of black squares, make it even so puzzle can easily be made symmetrical (wihtout having to make center square black)
			self.num_blk_sqs -= 1
			self.ifcenter_black = True

		self.empty_grid = None
		self.blk_sqs_positions = []
		self.across, self.down = None, None
		self.filled_grid = None

		## Call main methods upon initialization
		# self.empty_grid, self.blk_sqs_positions = self.make_empty_grid()
		# self.across, self.down = self.initialize_across_and_down_word_spaces()
		self.fill_process_started = False
		self.list_of_word_coordinates_filled = []	# A growing list of coordinates for each word filled in the grid, to allow for easier access to backtrack word fill if necessary.

		self.make_empty_grid()
		self.initialize_across_and_down_word_spaces()
		self.grid = copy.deepcopy(self.empty_grid)

		# self.fill_grid()


	def make_empty_grid(self):
		"""
		Method to generate a random empty grid, with symmetrical black and white squares, and numbering.

		Randomly choose black_squares, and make sure it obeys three rules above

		For testing purposes, will start with simple 5x5 grid with four corners set as black squares.
		"""

		G = np.empty(self.dims, dtype=str)	# Note: MUST use 'empty' (cannot use 'ndarray' or 'array'; the former will not be mutable (for some reason???) and the latter will be 1D); Also, if you use "np.string_" this actually makes it an array of "bytes"...?!
		G[:] = '_'	# Set all initialized cells to '_' so that columns line up on stdout (i.e., instead of setting them to empty '')

		# NORMALLY, will want to RANDOMLY pick a non-black square and then make it black (as well as the
		# symmetric/transpose location), so long as it doesn't create a rule violation in the standard puzzle design format
		# (e.g., cannot have any completely isolated regions, nor any white spaces flanked on either side by black squares).

		# HOWEVER, for testing purposes, we are going to just set all four corners to black squares.
		# G[0,0], G[4,0], G[0,4], G[4,4] = '.', '.', '.', '.'
		# self.blk_sqs_positions = [(0,0), (4,0), (0,4), (4,4)]
		# self.blk_sqs_positions = [(0,0),(1,0),(0,1),(0,5),(0,6),(1,6),(5,0),(6,0),(6,1),(6,6),(5,6),(6,5)]
		# for p in self.blk_sqs_positions:
		# 	G[p]='.'
		# self.empty_grid = copy.deepcopy(G)
		# # return self.empty_grid, self.blk_sqs_positions
		# return

		# Below is random generator -- for now use predetermined grid above.
		# When ready, remove 4 lines above

		center = int(self.rows/2)
		if self.ifcenter_black == True:
			G[center][center] = '.'
			self.blk_sqs_positions.append((center, center))

		rand_nums,rand_pool = int(self.num_blk_sqs / 2), [i for i in range(0,int((self.num_squares - 1) / 2))]
		while(rand_nums > 0):
			rand_nums -= 1
			temp = choice(rand_pool)
			while(self.check_valid(G,temp) == False):
				temp = choice(rand_pool)
			rand_pool.remove(temp)
			self.blk_sqs_positions.append((int(temp/self.cols),temp % self.rows))
			G[int(temp/self.cols)][temp % self.rows] = '.'
			self.blk_sqs_positions.append((center * 2 - int(temp/self.cols),center * 2 - (temp % self.rows)))  # make the board symmetric
			G[center * 2 - int(temp/self.cols)][center * 2 - (temp % self.rows)] = '.'

		self.empty_grid = copy.deepcopy(G)

		# return self.empty_grid, self.blk_sqs_positions
		return


	def check_valid(self,G,next_move):
		'''
		check if a puzzle is valid when generating black squares

		Check to make sure the density is low enough that a "valid puzzle" is still possible (i.e., that no two-letter words are present, etc.),
		depending on the number of black squares requested to be put into the grid.
		'''
		puzzle = copy.deepcopy(G)
		row,col = int(next_move/self.cols),next_move % self.rows
		puzzle[row][col] = '.'
		return self.check_rule1(puzzle,row,col) and self.check_rule2(puzzle)

	def check_rule1(self,puzzle,row,col):
		'''
		check if all words are no less than 3 letters
		'''
		cur_length = 0
		for c in range(0,self.cols): # check if current row obeys the first rule
			if puzzle[row][c] == "_":
				cur_length += 1
			if puzzle[row][c] == ".":
				if cur_length < 3 and cur_length != 0:
					return False
				else:
					cur_length = 0
		if cur_length in (1,2):
			return False
		cur_length = 0
		for r in range(0,self.rows): # check if current column obeys the first rule
			if puzzle[r][col] == "_":
				cur_length += 1
			if puzzle[r][col] == ".":
				if cur_length < 3 and cur_length != 0:
					return False
				else:
					cur_length = 0
		if cur_length in (1,2):
			return False
		return True

	def check_rule2(self,puzzle):
		'''
		check if all white grids are connected
		use union find
		'''
		n = self.rows * self.cols
		s = UnionFindSet(n)
		### Everytime union your right and your down
		for r in range(0,self.rows):
			for c in range(0,self.cols):
				if puzzle[r][c] == "_":
					if r + 1 < self.rows and puzzle[r+1][c] == "_":
						s.union(r*self.cols+c,(r+1)*self.cols+c)
					if c + 1 < self.cols and puzzle[r][c+1] == "_":
						s.union(r*self.cols+c,r*self.cols+c+1)
				else:
					continue
		parent = -1
		for r in range(0,self.rows):
			for c in range(0,self.cols):
				if puzzle[r][c] == "_":
					if parent == -1:
						parent = r * self.cols + c
					else:
						if parent != s.find(r*self.cols+c):
							return False

		return True



	def initialize_across_and_down_word_spaces(self):
		"""
		Method to gather the collection of blank across & down spaces, into which the words will be filled.

		# First get list of all across and down empty cell stretches (with length)
			# Will likely need sub method to update this list once letters start getting put in the grid, to re-run each time a new letter is inserted.

		"""

		self.across, self.down = {}, {}
		checked_down_squares = []

		# Gather down words FIRST (since that's how numbering is ordered)
		clue_enum = 0
		for r in range(self.rows):
			on_blank_across_squares = False
			for c in range(self.cols):
				on_blank_down_squares = False
				if (r,c) not in self.blk_sqs_positions:

					# Swap Column block up here? For ordering of numbers?
					if on_blank_across_squares == True:
						if c == self.cols-1:	# if at end of row
							self.across[curr_across_num].update( {"end":(r,c)} )

					elif on_blank_across_squares == False:
						on_blank_across_squares = True
						clue_enum += 1
						self.across.update( {clue_enum: {"start":(r,c)}} )
						curr_across_num = clue_enum

					if on_blank_down_squares == False and (r,c) not in checked_down_squares:
						# Now proceed through the column dimension first

						# If down word doesn't start at same square as across word, increment the clue number
						if (r,c) != self.across[curr_across_num]["start"]:
							clue_enum += 1

						self.down.update( {clue_enum: {"start":(r,c)}} )
						on_blank_down_squares = True
						checked_down_squares.append((r,c))
						r2 = r
						while on_blank_down_squares:
							r2+=1
							if (r2,c) in self.blk_sqs_positions:
								self.down[clue_enum].update( {"end":(r2-1,c)} )
								on_blank_down_squares = False

							elif (r2,c) not in self.blk_sqs_positions:
								checked_down_squares.append((r2,c))
								if r2 == self.rows-1:	# if at end of column
									self.down[clue_enum].update( {"end":(r2,c)} )
									on_blank_down_squares = False
								else:
									continue

				elif (r,c) in self.blk_sqs_positions:
					if on_blank_across_squares == True:	# Then end the word
						self.across[curr_across_num].update( {"end":(r,c-1)} )
						on_blank_across_squares = False
					elif on_blank_across_squares == False:
						continue

		# Get length of each word and append to both the word dict itself
		for k in self.across.keys():
			wlength = self.across[k]["end"][1] - ( self.across[k]["start"][1] - 1 )
			self.across[k]["len"] = wlength
			self.across[k]['word_temp'] = '.' * wlength
			self.across[k]['clue'] = None
			self.across[k]['answer'] = None

		for k in self.down.keys():
			wlength = self.down[k]["end"][0] - ( self.down[k]["start"][0] - 1 )
			self.down[k]["len"] = wlength
			self.down[k]['word_temp'] = '.' * wlength
			self.down[k]['clue'] = None
			self.down[k]['answer'] = None

		self.fill_process_started = False
		self.list_of_word_coordinates_filled = []

		print("Across",self.across)
		print("Down",self.down)

		# return self.across, self.down
		return



	def fill_word(self, word_id_to_fill, word_to_fill_grid_with, direction):
		"""
		"""

		word_coords = []

		if direction == 'across':
			# use for across only
			row = self.across[word_id_to_fill]['start'][0]
			c1 = self.across[word_id_to_fill]['start'][1]
			# c2 = self.across[word_id_to_fill]['end'][1] + 1

			for idx,letter in enumerate(word_to_fill_grid_with):
				self.grid[row][c1+idx] = letter
				if self.across[word_id_to_fill]['word_temp'][idx] != letter:
					word_coords.append((row,c1+idx))

			self.list_of_word_coordinates_filled.append((word_id_to_fill, direction, word_coords))

			# Also update the "word_temp" attribute for the filled word:
			self.across[word_id_to_fill].update( {"word_temp": word_to_fill_grid_with})

			# Now specify the transverse direction of words to update the single letters for:
			direction_of_words_to_update = 'down'


		if direction == 'down':
			# use for down only
			col = self.down[word_id_to_fill]['start'][1]
			r1 = self.down[word_id_to_fill]['start'][0]
			# r2 = self.down[word_id_to_fill]['end'][0] + 1

			for idx,letter in enumerate(word_to_fill_grid_with):
				self.grid[r1+idx][col] = letter
				if self.down[word_id_to_fill]['word_temp'][idx] != letter:
					word_coords.append((r1+idx,col))

			self.list_of_word_coordinates_filled.append((word_id_to_fill, direction, word_coords))

			# Also update the "word_temp" attribute for the filled word:
			self.down[word_id_to_fill].update( {"word_temp": word_to_fill_grid_with})

			# Now specify the transverse direction of words to update the single letters for:
			direction_of_words_to_update = 'across'

		# Now update all affected across & down words in self, and check if real words
		if self.update_across_and_down_with_partial_grid(direction_of_words_to_update):
			return True
		else:
			return False


	def remove_last_added_word(self):
		"""
		"""
		word_id_to_remove = self.list_of_word_coordinates_filled[-1][0]
		direction = self.list_of_word_coordinates_filled[-1][1]
		word_coords_to_clear = self.list_of_word_coordinates_filled[-1][2]

		# Clear letters from grid
		for coord in word_coords_to_clear:
			self.grid[coord] = '_'

		# Update the across or down attributes of words in the transverse direction
		self.update_across_and_down_with_partial_grid('across')
		self.update_across_and_down_with_partial_grid('down')

		self.list_of_word_coordinates_filled.pop(-1)

		return


	def update_across_and_down_with_partial_grid(self, direction_of_words_to_update):
		"""
		# updated across and down dicts with partial words to check possible validity

		Purpose of this function is to gather the current partial (or completed) list of words in the grid,
		to subsequently check each partially filled word for its potential to be a real word or not, as well
		as if a word which was filled indirectly is a real word or not.
		"""

		if direction_of_words_to_update == 'across':	# specifying which part of the grid needs updating will save time from iterating over all words that didn't get changed
			for k in self.across.keys():
				row = self.across[k]['start'][0]
				c1 = self.across[k]['start'][1]
				c2 = self.across[k]['end'][1] + 1
				temp_word = np.str.join('',self.grid[row][c1:c2])
				temp_word_re = temp_word.replace('_','.')

				# Check if any newly filled words are actually words or not
				if '.' not in temp_word_re:
					if not word_exists(temp_word_re):
						print("WARNING: ", temp_word_re, " IS NOT A WORD!")
						return False

				self.across[k].update( {"word_temp": temp_word_re})


		if direction_of_words_to_update == 'down':
			for k in self.down.keys():
				col = self.down[k]['start'][1]
				r1 = self.down[k]['start'][0]
				r2 = self.down[k]['end'][0] + 1
				temp_word = np.str.join('',self.grid[r1:r2,col])
				temp_word_re = temp_word.replace('_','.')

				# Check if any newly filled words are actually words or not
				if '.' not in temp_word_re:
					if not word_exists(temp_word_re):
						print("WARNING: ", temp_word_re, " IS NOT A WORD!")
						return False

				self.down[k].update( {"word_temp": temp_word_re})

		return True


	def gather_all_possible_words(self, word_dict, count_only: bool):
		"""
		NEW Method to gather the number of possible words that can be filled into the current state of the grid,
		based on the partial fill of the grid so far.

		# Regex compile idea from: https://stackoverflow.com/questions/38460918/regex-matching-a-dictionary-efficiently-in-python

		# TO ADD: Maybe don't run this if > 10000 possibilities
		# OR BETTER: In list creation below, only gather the words with a partial letter in it, (i.e., ignore all-blank words...)
				# OR: Only run it once for the all-blank words, and keep that dictionary so that it doesn't need to be recreated upon each iteration...?

		"""

		curr_grid_word_patterns = [self.across[k]['word_temp'] for k in self.across.keys() if '.' in self.across[k]['word_temp']] + [self.down[k]['word_temp'] for k in self.down.keys() if '.' in self.down[k]['word_temp']]
		curr_grid_word_patterns = list(set(curr_grid_word_patterns))	# Don't repeat for identical word patterns
		print(curr_grid_word_patterns)

		curr_grid_word_regex_compiled_dict = {}
		for wp in curr_grid_word_patterns:
			if len(wp) not in curr_grid_word_regex_compiled_dict.keys():
				curr_grid_word_regex_compiled_dict.update({len(wp):[re.compile(wp).match]})
			else:
				curr_grid_word_regex_compiled_dict[len(wp)].append(re.compile(wp).match)

		num_possible_words_to_fill = 0
		all_possible_word_choices_by_len_dict = {}
		for wlen in curr_grid_word_regex_compiled_dict.keys():
			w_choices = [wi for wi in word_dict[wlen] if any ( regex_match(wi) for regex_match in curr_grid_word_regex_compiled_dict[wlen] )]
			all_possible_word_choices_by_len_dict.update( {wlen : w_choices} )
			# print("Number possible words of length,",wlen,"=", len(w_choices))
			num_possible_words_to_fill += len(w_choices)

		print("Total number of possible word choices so far:", num_possible_words_to_fill)
		# if count_only:
		# 	return num_possible_words_to_fill

		if count_only:
			for wp in curr_grid_word_patterns:
				if len([k for k in all_possible_word_choices_by_len_dict[len(wp)] if re.compile(wp).match(k)]) == 0:
					print("NO FILL POSSIBLE FOR WORD PATTERN,", wp)
					return 0
			return num_possible_words_to_fill

		else:
			all_possible_word_choices_by_pattern_dict = {}
			for wp in curr_grid_word_patterns:
				wp_len = len(wp)
				curr_word_choices = [k for k in all_possible_word_choices_by_len_dict[wp_len] if re.compile(wp).match(k)]
				all_possible_word_choices_by_pattern_dict.update({wp:curr_word_choices})

		minimum_num_possible_fills = 100000 # arbitrarily chosen number of possible fills, to compare number possibilities for each partial word of the puzzle
		most_restricted_word_to_fill = None # initialize variable
		for wp in all_possible_word_choices_by_pattern_dict.keys():
			num_choices_for_curr_word = len(all_possible_word_choices_by_pattern_dict[wp])
			if num_choices_for_curr_word == 0:
				print("NO FILL POSSIBLE FOR WORD PATTERN,", wp)
				most_restricted_word_to_fill = wp
				break
			elif num_choices_for_curr_word < minimum_num_possible_fills:
				minimum_num_possible_fills = num_choices_for_curr_word
				most_restricted_word_to_fill = wp
			else:
				continue

		return all_possible_word_choices_by_len_dict, all_possible_word_choices_by_pattern_dict, most_restricted_word_to_fill



	def fill_grid_recursively(self, possible_word_dict, penalty_count):	# Removed: word_id_to_fill
		"""
		Recursive method to fill the grid.

		Fill LONGER words first, then crossings to the longer words
		ALSO Choose most common words first (or rank them all)

		Use self.grid as grid state.
		At each iteration, provide the next most-demanding word_id_to_fill to next function call,
							as well as the reduced dictionary from which the next word may be chosen.

		:param word_dict: Word corpus (in dict. format) to use to fill grid.

		"""
		global main_word_corpus

		if not '_' in self.grid:
			self.filled_grid = copy.deepcopy(self.grid)
			return self.filled_grid

		if penalty_count == 10:
			print("\nPENALTY LMIT REACHED: Re-attempting fill process from scratch...\n")
			self.grid = copy.deepcopy(self.empty_grid)
			self.initialize_across_and_down_word_spaces()
			penalty_count = 0
			return self.fill_grid_recursively(main_word_corpus, penalty_count)

		# Now do the actual filling part
		try:
			possible_word_dict_by_len, possible_word_dict_by_pattern, most_limited_word = self.gather_all_possible_words(main_word_corpus, count_only = False)
			most_limited_word_ids = [k for k in self.across.keys() if self.across[k]['word_temp'] == most_limited_word]
			if len(most_limited_word_ids) == 0:
				most_limited_word_ids = [k for k in self.down.keys() if self.down[k]['word_temp'] == most_limited_word]
				word_dir = 'down'
			else:
				word_dir = 'across'

			word_id_num_to_fill = choice(most_limited_word_ids)

			# If choosing first word or two, choose the longest in the puzzle
			if len(self.list_of_word_coordinates_filled) < 1:
				max_word_length = max(self.across[k]['len'] for k in self.across.keys())
				print(max_word_length)
				most_limited_word_ids = [k for k in self.across.keys() if self.across[k]['len'] == max_word_length and '.' in self.across[k]['word_temp']]
				word_dir = 'across'
				word_id_num_to_fill = choice(most_limited_word_ids)
				most_limited_word = self.across[word_id_num_to_fill]['word_temp']
				# print(word_id_num_to_fill)
				# print(most_limited_word)
				# print(choices(possible_word_dict_by_pattern[most_limited_word], k=20))
				# exit()


			# reset max of k each time so not repeating the same word (and try to turn off replacement)
			wds = choices(possible_word_dict_by_pattern[most_limited_word], k=20)	# choose 100 at a time!!!! then do for loop down below...
			wds = set(list(wds)) # Only check unique words
			print(wds)
			# w = choice(possible_word_dict_by_pattern[most_limited_word])
			if len(wds) == 0:
				print("Removing last 3 words and trying again...\n")
				self.remove_last_added_word()
				self.remove_last_added_word()
				self.remove_last_added_word()
				return self.fill_grid_recursively(main_word_corpus, penalty_count)

			# This pool method below actually seems to work!...partially...
			# G = copy.deepcopy(self.grid)
			# p = Pool(10)
			# list_of_fill_word_params = [(G, word_id_num_to_fill, wi, word_dir) for wi in w]
			# result = p.starmap(self.fill_word, list_of_fill_word_params)
			# print(result)

			# Move clue-retrieval to AFTER completing grid-fill process
			# word_len_to_fill = len(most_limited_word)
			# clue = choice(main_word_corpus[word_len_to_fill][w])

			print("Most limited word pattern to fill:", most_limited_word, "at", word_id_num_to_fill, word_dir) # "  Filling with  ---->  ", w)

			most_flexible_word = None
			most_possible_new_words_allowed = 0
			for w in wds:
				if len(self.list_of_word_coordinates_filled) == 0:
					# If choosing first word, likely won't affect the number of next possible words
					# since there will still be another fully-blank row or column of cells. So for now,
					# just pick one at random to speed things up.
					most_flexible_word = w
					break
				if self.fill_word(word_id_num_to_fill, w, word_dir):
					# Get number of possible words
					number_possible_new_words = self.gather_all_possible_words(possible_word_dict_by_len, count_only = True)
					if number_possible_new_words >= most_possible_new_words_allowed:
						most_flexible_word = w
						most_possible_new_words_allowed = number_possible_new_words
					self.remove_last_added_word()
				else:
					self.remove_last_added_word()

			try:
				print("  Filling with  ---->  ", most_flexible_word)
				self.fill_word(word_id_num_to_fill, most_flexible_word, word_dir)
			except Exception as err:
				print("EXCEPTION:", err)
				print("Removing last 3 words and trying again...\n")
				self.remove_last_added_word()
				self.remove_last_added_word()
				self.remove_last_added_word()
				penalty_count += 1

			print(self.grid)

			return self.fill_grid_recursively(main_word_corpus, penalty_count)

		except Exception as err:
			print("\nEXCEPTION:", err)
			# The plan for this part is to allow the program to re-try the last word placement/choice, so it doesn't have to start from scratch all over again.
			# But for now, that is the easier strategy to code...
			print("Removing last 3 words and trying again...\n")
			penalty_count += 1
			self.remove_last_added_word()
			self.remove_last_added_word()
			self.remove_last_added_word()
			return self.fill_grid_recursively(main_word_corpus, penalty_count)

			# print("Re-attempting fill process...\n")
			# self.grid = copy.deepcopy(self.empty_grid)
			# self.initialize_across_and_down_word_spaces()
			# return self.fill_grid_recursively(main_word_corpus, penalty_count)


def word_exists(word_to_check):
	"""
	Function to check if a completely-filled word is really a word (indirectly or directly).
	"""
	global main_word_corpus

	if word_to_check in main_word_corpus[len(word_to_check)].keys():
		return True
	else:
		return False


def read_word_corpus(file_list, dims):
	"""
	Function to read in the provided dictionary word corpus.

	Will we be able to store this entire thing in memory?
	"""

	clue_answer_dict = {}

	# Initialize dictionary with maximum wordlength count
	# for wl in range(1, max(dims)+1):
	for wl in range(1, 25):	# max length in this corpus is 24
		clue_answer_dict.update( { wl: {} } )

	for file in file_list:
		with open(file, 'r') as f:
			for line in f:
				clue = line.split('\t')[0]
				answer = line.split('\t')[1].strip()
				answer_len = len(answer)

				if answer_len is not None and answer_len > 0:
					if answer not in clue_answer_dict[answer_len].keys():
						clue_answer_dict[answer_len].update( { answer : [clue] } )	# Need to put clues in a list in case multiple clues exist for the same answer
					elif answer in clue_answer_dict[answer_len].keys():
						clue_answer_dict[answer_len][answer].append(clue)

	return clue_answer_dict


def sort_word_dic(word):
	'''
	Sort the dictionary by its length of hints
	'''
	for wordlength in word.keys():
		pairs= sorted(word[wordlength].items(),key = lambda item: len(item[1]),reverse = True)
		new_dic = {}
		for pair in pairs:
			new_dic[pair[0]] = pair[1]
		word[wordlength] = copy.deepcopy(new_dic)
	return word


if __name__ == "__main__":
	main()
