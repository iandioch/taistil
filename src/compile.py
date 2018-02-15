import json
import sys

from os import listdir
from os.path import isfile, join


'''
Given a path to a directory, compile all the json
files in that directory and recursive subdirectories
into one big Taistil json document, and return it.
'''
def compile_directory(path):
	obj = {
		'note': 'Auto-compiled from directory {}'.format(path),
		'elements': [],
	}
	items = listdir(path)
	for item in items:
		sub_path = join(path, item)
		if isfile(sub_path):
			with open(sub_path, 'r') as f:
				data = json.load(f)
				obj['elements'].append(data)
		else:
			obj['elements'].append(compile_directory(sub_path))
	return obj
			

if __name__ == '__main__':
	if len(sys.argv) == 1:
		print('Please provide a directory path.')
	else:
		path = ' '.join(sys.argv[1:])
		compiled = compile_directory(path)
		print(json.dumps(compiled, indent=4))
