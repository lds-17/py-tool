#coding=utf-8
#!/usr/bin/python
# author: lds
# create in 2022.2

import os
import sys
import stat


DB_FILE = ""
FILE_NAME = "xg_db_auto"
OUTPUT_HRL_PATH = ""
OUTPUT_ERL_PATH = ""

def gen():
	dbf = open(DB_FILE, encoding='utf-8')
	hrl = open(os.path.join(OUTPUT_HRL_PATH, FILE_NAME + ".hrl"), encoding='utf-8')
	erl = open(os.path.join(OUTPUT_ERL_PATH, FILE_NAME + ".erl"), encoding='utf-8')

	header = '%% this file is automatic generation, do not change! create by lds\n\n\n'
	hrl.write(header)
	erl.write(header)
	hrl.write('''-record(db_table_info, {name,fields=[],pk=[]}). \n\n''')
	erl.write('-include("' + FILE_NAME + '.hrl"' + ').\n\n')
	erl.write('-compile(export_all). \n\n')


	for line in db:
		line = line.strip()
		if line.lower().startswith('create table') :
			tableName = line[line.index('`')+1 : line.rindex('`')]
			prefixName = 'xg_db_' + tableName
			hrl.write('%% ================================= ' + tableName + ' =================================\n\n')
			hrl.write('-define(XG_DB_' + tableName.upper() + ', ' + tableName + ').\n\n')
			hrl.write('-record(' + prefixName + ', {\n')

			
			index = 1
			fields = []
			pk = []
			for line in db:
				line = line.strip()
				if line.endswith(';') : break
				if line.startswith('`'):
					fieldName = line[line.index('`')+1 : line.rindex('`')]
					hrl.write('    \'' + fieldName + '\',\n')
					fields.append((fieldName, index))
					index += 1
				elif line.startswith('PRIMARY KEY') or line.startswith('primary key') :
					for e in line.split(','):
						pk.append(e[e.index('`')+1 : e.rindex('`')])

			hrl.write('}).\n\n')
			
			tableInfo = '#db_table_info{name = \'' + tableName + '\', '
			pk2 = []
			fieldContent = ''
			for e in fields:
				fieldContent += '{\'' + e[0] + '\', ' + e[1] + '}, '
				if e[0] in pk :
					pk2.append(e)
			if fieldContent != '' :
				fieldContent = fieldContent[: len(fieldContent)-1]
			tableInfo = 'fields = [' + fieldContent + '], '

			pkContent = ''
			for e in pk2 :
				pkContent += '{\'' + e[0] + '\', ' + e[1] + '}, '
			if pkContent != '' :
				pkContent = pkContent[: len(pkContent) -1 ]
			tableInfo = 'pk = [' + pkContent + '] }'


			erl.write(prefixName + '() -> \n' + tableInfo + ';\n\n')

	hrl.close()
	erl.write('get(_) -> undefined.')
	erl.close()
	return




def main():
	global DB_FILE, OUTPUT_ERL_PATH, OUTPUT_HRL_PATH
	DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../sql/db.sql"))
	OUTPUT_HRL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../include/xg/"))
	OUTPUT_ERL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/xg/db/"))
	gen()


if __name__ == '__main__':
	main()