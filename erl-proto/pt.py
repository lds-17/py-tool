#coding=utf-8
#!/usr/bin/python
# author: lds
# create in 2020.12

import os
import sys
import stat

OUTPUT_DIR = './output/'

def ch() :
	if not os.path.exists(OUTPUT_DIR):
		os.mkdir(OUTPUT_DIR)
	files = os.listdir('./')
	files = [x for x in files if x.endswith('.erl')]
	for file in files:
		with open(file, 'r', encoding='utf-8') as f:
			w = open(OUTPUT_DIR + file, 'w+', encoding='utf-8')
			for str in f:
				lstr = str.lstrip()
				if lstr.startswith('handle(?PT_'):
					index = lstr.find(',')
					str = 'handle(?c2s_' + lstr[11:index].lower() + lstr[index:]
				w.writelines(str)
			w.close()
	print('done!')

ch()