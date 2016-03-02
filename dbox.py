import os
import string
from collections import Counter
import cPickle
import datetime
from cobian_utils import pretty_print, print_histogram

class Dbox(object):
	def __init__(self):
		
		self.col_names = []
		self.col_types = []
		self.rows = []
	
	def add_file(self,file_path,delimiter="",print_every=100000):
		
		print "Reading file {0}...".format(file_path)
		
		if not os.path.isfile(file_path):
			raise ValueError("Specified file ({0}) does not exist.".format(file_path))
		if delimiter == "":
			file_ext = file_path.split(".")[-1]
			if file_ext == "csv":
				delimiter = ","
			elif file_ext == "tab":
				delimiter = "\t"
			else:
				raise ValueError("No delimiter specified and file extension unknown")
		
		file_reader = open(file_path,"r")
		col_names = file_reader.readline().rstrip("\r\n").split(delimiter)
		# if this is the first file, initialize col details
		if self.col_names == []:
			self.col_names = col_names
			self.col_types = ["str"] * len(self.col_names)
		else:
			if col_names != self.col_names:
				raise ValueError("File's column names do not match dbox's column names")
		
		lines_read = 0
		next_line = file_reader.readline()
		while next_line:
			line_values = next_line.rstrip("\r\n").split(delimiter)
			line_values = [None if value == "" else value for value in line_values]
			self.rows.append(line_values)
			lines_read += 1
			if print_every > 0 and lines_read % print_every == 0:
				print "{0} lines read...".format(lines_read)
			next_line = file_reader.readline()
		file_reader.close()
		
		print "{0} rows added, {1} rows total.".format(lines_read,len(self.rows))
	
	def get_col(self,col_index):
		return [self.rows[row_index][col_index] for row_index in range(len(self.rows))]
	
	def get_col_set(self,col_index):
		unique_vals = set()
		for row in self.rows:
			unique_values.add(row[col_index])
		return unique_vals
	
	def sub_box(self,row_indexes):
		sub = Dbox()
		sub.col_names = self.col_names[:]
		sub.col_types = self.col_types[:]
		sub.rows = [self.rows[row_index] for row_index in row_indexes]
		return sub
	
	def print_cols(self):
		print "Index\tType\tName"
		for i in range(len(self.col_names)):
			print "{0}\t{1}\t{2}".format(i,self.col_types[i],self.col_names[i])
	
	def reorder_cols(self,new_index_order,print_cols=True):
		self.col_names = [self.col_names[i] for i in new_index_order]
		self.col_types = [self.col_types[i] for i in new_index_order]
		for row_index in range(len(self.rows)):
			self.rows[row_index] = [self.rows[row_index][i] for i in new_index_order]
		if print_cols:
			self.print_cols()
	
	def add_col_from_dict(self,key_col_index,new_col_dict,new_col_name):
		self.col_names.append(new_col_name)
		self.col_types.append(type(new_col_dict.values()[0]).__name__)
		nones_added = 0
		for row_index in range(len(self.rows)):
			try:
				self.rows[row_index].append(new_col_dict[self.rows[row_index][key_col_index]])
			except KeyError:
				self.rows[row_index].append(None)
				nones_added += 1
		print "Col added."
		if nones_added > 0:
			print "({0} none values)".format(nones_added)
	
	def print_summary(self,col_indexes=None,row_indexes=None,max_values=10,max_col_width=20,percentage_places=5):
		if col_indexes == None:
			col_indexes = range(0,len(self.col_names))
		if row_indexes == None:
			row_indexes = range(len(self.rows))
		print "{0} total rows".format(len(row_indexes))
		for col_index in col_indexes:
			print "{0}\t{1}\t{2}".format(col_index,self.col_types[col_index],self.col_names[col_index])
			col_type = self.col_types[col_index]
			if col_type == "str":
				self.print_str_summary(col_index,row_indexes,max_values,max_col_width,percentage_places)
			elif col_type == "date" or col_type == "datetime":
				self.print_datetime_summary(col_index,row_indexes,percentage_places)
			elif col_type == "int" or col_type == "float":
				self.print_intfloat_summary(col_index,row_indexes,percentage_places)
			elif col_type == "list":
				self.print_list_summary(col_index,row_indexes,max_values,max_col_width,percentage_places)
			print ""
	
	def print_str_summary(self,col_index,row_indexes,max_values,max_col_width,percentage_places):
		col_counts = self.col_counter(col_index,row_indexes)
		all_values_unique = len(col_counts) == len(row_indexes)
		if all_values_unique:
			values_to_print = min(max_values,len(row_indexes))
			print "All values unique, first {0} values:".format(values_to_print)
			for i in range(values_to_print):
				print "\t{0}".format(self.rows[row_indexes[i]][col_index])
		else:
			num_nones = col_counts.pop(None,0)
			print "{0} unique values".format(len(col_counts) + (1 if num_nones > 0 else 0))
			str_rows = [["Value","Count","Percentage"]]
			col_count_pairs = col_counts.most_common(max_values)
			for i in range(len(col_count_pairs)):
				value = col_count_pairs[i][0]
				count = col_count_pairs[i][1]
				trimmed_percentage = dbox_trimmed_percentage(count,len(row_indexes),percentage_places)
				str_rows += [[str(value),str(count),str(trimmed_percentage)]]
			if num_nones > 0:
				str_rows += [["[[Missing]]",str(num_nones),str(dbox_trimmed_percentage(num_nones,len(row_indexes),percentage_places))]]
			pretty_print(str_rows,max_col_width=max_col_width,lead=5)
	
	def print_datetime_summary(self,col_index,row_indexes,percentage_places):
		col_values = [row[col_index] for row in [self.rows[row_index] for row_index in row_indexes]]
		num_nones = col_values.count(None)
		col_values = [col_value for col_value in col_values if col_value != None]
		print "Dates from {0} to {1}".format(min(col_values),max(col_values))
		if num_nones > 0:
			print "({0} missing values, {1}%)".format(num_nones,dbox_trimmed_percentage(num_nones,len(row_indexes),percentage_places))
	
	def print_intfloat_summary(self,col_index,row_indexes,percentage_places):
		col_values = sorted([row[col_index] for row in [self.rows[row_index] for row_index in row_indexes]])
		num_nones = col_values.count(None)
		col_values = [col_value for col_value in col_values if col_value != None]
		print "Min: {0}".format(min(col_values))
		print "Mean: {0}".format(sum(col_values)/len(col_values))
		middle_index = len(col_values)/2
		if len(col_values) % 2 == 0:
			median = (col_values[middle_index] + col_values[middle_index-1])/2.0
		else:
			median = col_values[middle_index]
		print "Median: {0}".format(median)
		print "Max: {0}".format(max(col_values))
		print ""
		print_histogram(col_values,20,30,0)
		if num_nones > 0:
			print "({0} missing values, {1}%)".format(num_nones,dbox_trimmed_percentage(num_nones,len(row_indexes),percentage_places))
	
	def print_list_summary(self,col_index,row_indexes,max_values,max_col_width,percentage_places):
		if row_indexes == None:
			row_indexes = range(len(self.rows))
		len_counts = Counter()
		for row_index in row_indexes:
			len_counts[len(self.rows[row_index][col_index])] += 1
		num_nones = len_counts.pop(None,0)
		str_rows = [["Length","Count","Percentage"]]
		len_count_pairs = len_counts.most_common(max_values)
		for i in range(len(len_count_pairs)):
			length = len_count_pairs[i][0]
			count = len_count_pairs[i][1]
			trimmed_percentage = dbox_trimmed_percentage(count,len(row_indexes),percentage_places)
			str_rows += [[str(length),str(count),str(trimmed_percentage)]]
		if num_nones > 0:
			str_rows += [["[[Missing]]",str(num_nones),str(dbox_trimmed_percentage(num_nones,len(row_indexes),percentage_places))]]
		pretty_print(str_rows,max_col_width=max_col_width,lead=5)
	
	def col_counter(self,col_index,row_indexes=None):
		if row_indexes == None:
			row_indexes = range(len(self.rows))
		col_counts = Counter()
		for row_index in row_indexes:
			col_counts[self.rows[row_index][col_index]] += 1
		return col_counts
	 
	def cast_col(self,col_index,type,date_format=None,print_every=100000):
		if type == "int":
			casting_function = int
		elif type == "float":
			casting_function = float
		elif type == "str":
			casting_function = str
		elif type == "date":
			casting_function = lambda x: datetime.datetime.date(datetime.datetime.strptime(x,date_format))
		elif type == "datetime":
			casting_function = lambda x: datetime.datetime.strptime(x,date_format)
		else:
			raise ValueError("{0} not a handled casting type".format(type))
		try:
			rows_cast = 0
			nones_cast = 0
			for row_index in range(len(self.rows)):
				if self.rows[row_index][col_index] in [None,"","None"]:
					self.rows[row_index][col_index] = None
					nones_cast += 1
				else:
					self.rows[row_index][col_index] = casting_function(self.rows[row_index][col_index])
				rows_cast += 1
				if rows_cast % print_every == 0:
					print "{0} rows cast, {1} None values".format(rows_cast,nones_cast)
		except ValueError:
			print "Cannot cast \"{0}\" in row {1} to {2}".format(self.rows[row_index][col_index],row_index,type)
			return
		
		self.col_types[col_index] = type
		print "{0} converted to type {1}".format(self.col_names[col_index],self.col_types[col_index])
	
	def check_castable(self,col_index,type,date_format=None,print_every=100000):
		if type == "int":
			casting_function = int
		elif type == "float":
			casting_function = float
		elif type == "str":
			casting_function = str
		elif type == "date":
			casting_function = lambda x: datetime.datetime.date(datetime.datetime.strptime(x,date_format))
		elif type == "datetime":
			casting_function = lambda x: datetime.datetime.strptime(x,date_format)
		else:
			raise ValueError("{0} not a handled casting type".format(type))
		try:
			rows_castable = 0
			nones_skipped = 0
			for row_index in range(len(self.rows)):
				if self.rows[row_index][col_index] in [None,"","None"]:
					self.rows[row_index][col_index] = None
					nones_skipped += 1
				else:
					x = casting_function(self.rows[row_index][col_index])
				rows_castable += 1
				if rows_castable % print_every == 0:
					print "{0} rows castable, {1} missing values skipped".format(rows_castable,nones_skipped)
		except ValueError:
			print "Cannot cast \"{0}\" in row {1} to {2}".format(self.rows[row_index][col_index],row_index,type)
			return
		
		print "{0} safely castable to type {1}".format(self.col_names[col_index],type)
	
	def check_relation(self,col_index_1,col_index_2,print_result=True,max_values=5):
		col_index_1 = int(col_index_1)
		col_index_2 = int(col_index_2)
		if type(print_result)==type(str()):
			print_result = print_result=="True"
		
		[forward_relation,backward_relation] = self.col_relation_dicts(col_index_1,col_index_2)
		
		blank_to_one = max([len(x) for x in forward_relation.values()]) == 1
		one_to_blank = max([len(x) for x in backward_relation.values()]) == 1
		if print_result:
			print "{0} and {1} have a {2}-to-{3} relationship".format(self.col_names[col_index_1],self.col_names[col_index_2],"one" if one_to_blank else "many","one" if blank_to_one else "many")
			if not blank_to_one:
				forward_fork_values = [key for key in forward_relation.keys() if len(forward_relation[key]) > 1]
				print "{0}/{1} unique values of {2} correspond to more than one value of {3}, including:".format(len(forward_fork_values),len(forward_relation),self.col_names[col_index_1],self.col_names[col_index_2])
				for i in range(min(max_values,len(forward_fork_values))):
					print "\t{0}\t{1}".format(forward_fork_values[i],forward_relation[forward_fork_values[i]])
			if not one_to_blank:
				backward_fork_values = [key for key in backward_relation.keys() if len(backward_relation[key]) > 1]
				print "{0}/{1} unique values of {2} correspond to more than one value of {3}, including:".format(len(backward_fork_values),len(backward_relation),self.col_names[col_index_2],self.col_names[col_index_1])
				for i in range(min(max_values,len(backward_fork_values))):
					print "\t{0}\t{1}".format(backward_fork_values[i],backward_relation[backward_fork_values[i]])
		else:
			return [one_to_blank,blank_to_one]
	
	def col_relation_dicts(self,col_index_1,col_index_2):
		forward_relation = dict()
		backward_relation = dict()
		for row_index in range(len(self.rows)):
			value_1 = self.rows[row_index][col_index_1]
			value_2 = self.rows[row_index][col_index_2]
			try:
				forward_relation[value_1].add(value_2)
			except KeyError:
				forward_relation[value_1] = set([value_2])
			try:
				backward_relation[value_2].add(value_1)
			except KeyError:
				backward_relation[value_2] = set([value_1])
		return [forward_relation,backward_relation]
	
	def drop_cols(self,col_indexes):
		dropped_col_names = []
		for col_index in col_indexes:
			dropped_col_names.append(self.col_names[col_index])
		
		# remove names and values for dropped columns
		col_indexes = sorted(col_indexes,reverse=True)
		for col_index in col_indexes:
			del(self.col_names[col_index])
			del(self.col_types[col_index])
		for row_index in range(len(self.rows)):
			for col_index in col_indexes:
				del(self.rows[row_index][col_index])
		
		print "Dropped columns:"
		for name in dropped_col_names:
			print name
	
	def drop_rows(self,row_indexes):
		row_indexes = sorted(row_indexes,reverse=True)
		for row_index in row_indexes:
			del(self.rows[row_index])
		print "Dropped {0} rows.".format(len(row_indexes))
	
	def rows_where(self,logic,row_indexes=None,print_every=100000):
		if row_indexes == None:
			row_indexes = range(len(self.rows))
		for col_index in range(len(self.col_names)):
			logic = logic.replace("[[{0}]]".format(col_index),"self.rows[row_index][{0}]".format(col_index))
		new_row_indexes = []
		
		rows_checked = 0
		for row_index in row_indexes:
			if eval(logic):
				new_row_indexes.append(row_index)
			rows_checked += 1
			if rows_checked % print_every == 0:
				print "{0} rows checked, {1} rows selected".format(rows_checked,len(new_row_indexes))
		return new_row_indexes
	
	def merge_cols(self,col_index_1,col_index_2,name=None,divider="::",print_every=100000,force=False):
		if not force:
			print "Checking for 1-to-1 relationship between {0} and {1}...".format(self.col_names[col_index_1],self.col_names[col_index_2])
			col_relation = self.check_relation(col_index_1,col_index_2,print_result=False)
			if not col_relation == [True,True]:
				raise ValueError("Cannot merge: {0} and {1} have a {2}-to-{3} relationship".format(self.col_names[col_index_1],self.col_names[col_index_2],"one" if col_relation[0] else "many","one" if col_relation[1] else "many"))
		
		# set names
		if name == None:
			name = "{0}{2}{1}".format(self.col_names[col_index_1],divider,self.col_names[col_index_2])
			self.col_names[col_index_1] = name
		elif type(name) == type(0):
			if name == 1:
				name = self.col_names[col_index_1]
			elif name == 2:
				name = self.col_names[col_index_2]
			else:
				raise ValueError("If name is an int, it must be 1 or 2, indicting col name to be preserved")
			self.col_names[col_index_1] = name
		else:
			self.col_names[col_index_1] = name
		del(self.col_names[col_index_2])
		
		# merge types
		self.col_types[col_index_1] = "str"
		del(self.col_types[col_index_2])
		
		rows_merged = 0
		# merge values
		for row in self.rows:
			# None + None = None
			if row[col_index_1] != None or row[col_index_2] != None:
				row[col_index_1] = "{0}{1}{2}".format(row[col_index_1],divider,row[col_index_2])
			del(row[col_index_2])
			rows_merged += 1
			if print_every > 0 and rows_merged % print_every == 0:
				print "{0} rows merged...".format(rows_merged)
	
	def save(self,dbox_file_path,overwrite=False):
		dbox_file_path += ".dbx"
		
		if not overwrite and os.path.isfile(dbox_file_path):
			raise ValueError("Specified file ({0}) already exists.".format(dbox_file_path))
		fout = open(dbox_file_path,"wb")
		print "Saving..."
		fast_pickler = cPickle.Pickler(fout,protocol=2)
		fast_pickler.fast = 1
		fast_pickler.dump(self)
		#cPickle.dump(self,fout,protocol=2)
		fout.close()
		print "Wrote dbox to {0}.".format(dbox_file_path)
	
	def print_values(self,col_indexes=None,row_indexes=None,max_col_width=20,lead=0,buffer=2):
		if col_indexes == None:
			col_indexes = range(len(self.col_names))
		if row_indexes == None:
			row_indexes = range(len(self.rows))
		str_rows = [[self.col_names[col_index] for col_index in col_indexes]]
		for row_index in row_indexes:
			str_rows.append([str(self.rows[row_index][col_index]) for col_index in col_indexes])
		pretty_print(str_rows,max_col_width,lead,buffer)
	
	def write_file(self,output_file_path,delimiter,overwrite=False):
		if not overwrite and os.path.isfile(output_file_path):
			raise ValueError("Specified file ({0}) already exists.".format(output_file_path))
		fout = open(output_file_path,"w")
		print "Writing..."
		fout.write(delimiter.join(self.col_names) + "\n")
		for row in self.rows:
			fout.write(delimiter.join(map(str,row)) + "\n")
		fout.close()
		print "Wrote file to {0}.".format(output_file_path)
	
	def get_value(self,row_index,col_name):
		return self.rows[row_index][self.col_names.index(col_name)]

def dbox_load(dbox_file_path):
	if not os.path.isfile(dbox_file_path):
			raise ValueError("Specified file ({0}) does not exist.".format(dbox_file_path))
	if not dbox_file_path[-4:] == ".dbx":
		raise ValueError("Specified file ({0}) not a .dbx file.".format(dbox_file_path))
	fin = open(dbox_file_path,"rb")
	print "Loading {0}...".format(dbox_file_path)
	loaded_dbox = cPickle.load(fin)
	fin.close()
	return loaded_dbox

def dbox_trimmed_percentage(n,d,percentage_places):
	percentage = ((n*1.0)/d)*100
	return str(percentage)[:str(percentage).index(".")+1+percentage_places]