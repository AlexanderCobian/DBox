
import itertools
import math

def venn(*args):
	handled = set()
	for r in range(len(args)):
		com_size = len(args)-r
		coms = itertools.combinations(range(len(args)),com_size)
		try:
			while True:
				com = coms.next()
				venn_set = args[com[0]]
				for i in com[1:]:
					venn_set = venn_set & args[i]
				venn_set = venn_set - handled
				handled = handled | venn_set
				print "{0}:\t{1}".format(",".join(map(str,com)),len(venn_set))
		except StopIteration:
			pass

def pretty_print(str_rows,max_col_width=20,lead=0,buffer=2):
	col_widths = [0]*len(str_rows[0])
	for str_row in str_rows:
		for i in range(len(str_row)):
			col_widths[i] = max(col_widths[i],len(str_row[i]))
			col_widths[i] = min(col_widths[i],max_col_width)
	template = " "*lead
	for i in range(len(col_widths)):
		template += "{{{0}:{1}}}".format(i,col_widths[i]+buffer)
	for str_row in str_rows:
		print template.format(*map(truncate_string,str_row,col_widths))

def truncate_string(full_string,max_length,indicator="..."):
	if len(full_string) <= max_length:
		return full_string
	else:
		return full_string[:max_length-len(indicator)]+indicator

def print_histogram(values,num_bins,max_height,lead,symbol="*"):
	sorted_values = sorted(values)
	min_value = min(values)
	max_value = max(values)
		
	bin_size = int(math.ceil(float(max_value-min_value)/num_bins))
	while (min_value + (bin_size * num_bins-1)) >= max_value:
		num_bins -= 1
	
	boundary_values = [min_value]
	bin_counts = []
	sorted_values_index = 0
	for bin_index in range(num_bins):
		boundary_values.append(boundary_values[-1]+bin_size)
		bin_count = 0
		while sorted_values_index < len(sorted_values) and sorted_values[sorted_values_index] < boundary_values[-1]:
			bin_count += 1
			sorted_values_index += 1
		bin_counts.append(bin_count)
	
	symbol_size = max(bin_counts)/max_height
	str_rows = []
	print "{0}{1}".format(" "*lead,boundary_values[0])
	for bin_index in range(num_bins):
		bin_max_string = " - {0}".format(boundary_values[bin_index+1])
		bin_symbols_string = symbol * (bin_counts[bin_index]/symbol_size)
		str_rows.append([bin_max_string,bin_symbols_string])
	
	pretty_print(str_rows,max(20,max_height),lead)
	print "\n{0}({1} represents {2})".format(" "*lead,symbol,symbol_size)