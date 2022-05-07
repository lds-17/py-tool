#coding=utf-8
#!/usr/bin/python
# author: lds
# create in 2020.12

import os
import sys
import stat

FILE_PATH = ""
PROTO_PATH = ""
IS_PROTO3 = False
MERGE_FILE_NAME = 'msg.proto'
OUTPUT_DIR = 'output'

ERL_S2C_FILE = 'data_s2c'
ERL_C2S_FILE = 'data_c2s'
ERL_ROBOT = 'data_robot'
ERL_PROTO_HRL_FILE = 'xg_proto_name'

DEFAULT_ROUTE_NAME = 'player'
DEFAULT_FREQ = '0'

# 把所有协议文件合并成一个文件
def merge_file():
	files = os.listdir(PROTO_PATH)
	mfile_path = unicode_path(os.path.join(FILE_PATH, OUTPUT_DIR, MERGE_FILE_NAME))
	if os.path.exists(mfile_path):		# 删除旧文件
		os.chmod(mfile_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
		os.remove(mfile_path)
	files = [x for x in files if x.endswith('.proto')]
	if (len(files) == 0):
		print('no found proto file!')
		return
	for i in files:print(i)
	mg_fd =  open(mfile_path, 'w', encoding='utf-8')
	if IS_PROTO3: mg_fd.write('''syntax = "proto3";\n\n''')
	mg_fd.write('''// #$# ==============================================
// #$# 规则:
// #$# 1. client -> server 的协议以 'c2s_' 为前缀
// #$# 2. server -> client 的协议以 's2c_' 为前缀
// #$# 3. 非协议的复合结构以 'pkg_' 为前缀
// #$# 4. 枚举类型结构以 'e_' 为前缀
// #$# 5. 枚举值全大写, 以'_'作分割符
// #$# 6. 普通字段值全小写, 以'_'作分割符
// #$# 7. proto2: 可能没有值的字段必须使用optional修饰, 必须有值的才使用required
// #$#    proto3: 无需定义也不能定义required和optional, 此类统一默认当成optional
// #$# 
// #$# 8. 协议ID规则: 每个 message c2s_name{} 或 message s2c_name{} 协议
// #$#   前必须定义协议ID, 格式为: // c2s_id 或 s2c_id
// #$# 9. 消息路由格式: routing_net | routing_player , 没有该项时默认此
// #$# 	消息为 routing_player, 即消息转发给玩家进程处理, 
// #$# 	当设置为 routing_net 表示消息直接在网络进程处理,
// #$# 	默认不填该项
// #$# 10. 限制消息发送频率: 格式: `freq_Ms` Ms:毫秒, 在Ms毫秒内超过1次的消息不受理并发送错误码, 
// #$#     没有该项时默认消息不限制频率
// #$# ==============================================\n\n''')

	for file in files:
		fd =  open(unicode_path(os.path.join(PROTO_PATH, file)), encoding='utf-8')
		mg_fd.write('// file: ====================== ' + file + ' ======================\n\n')
		for line in fd:
			if (line.strip().startswith('syntax = "proto3";')) :
				continue
			line = line.strip()
			if (line != '' and line != '//'):	# 去掉空行空注释, 保持行文紧凑
				mg_fd.writelines(line + '\n')
		fd.close()
		mg_fd.write('\r\n\r\n')
	mg_fd.close()
	print('合并生成'+MERGE_FILE_NAME+'成功!')
	return 		

# 根据合并后的文件生成erlang协议数据文件
def gen_erl():
	mfile = unicode_path(os.path.join(FILE_PATH, OUTPUT_DIR, MERGE_FILE_NAME))
	if (not os.path.exists(mfile)):
		print("no found msg.proto !")
		del_erl()
		return
	sfile, sfd = init_erl(ERL_S2C_FILE)
	cfile, cfd = init_erl(ERL_C2S_FILE)
	rfile, rfd = init_erl(ERL_ROBOT)
	hfile, hfd = init_hrl(ERL_PROTO_HRL_FILE)
	mfd =  open(mfile, 'r', encoding='utf-8')
	cfd.write('\n-include("xg_net.hrl").\n\n')
	routing = DEFAULT_ROUTE_NAME
	freq = DEFAULT_FREQ
	for str in mfd.readlines() :
		
		str = str.strip()
		if (str.startswith('// #$#')) :
			continue
		if (str.startswith('//')) :
			terms = str[2:].split()
			for term in terms:
				if (term.startswith('s2c_')) :
					mid = term[4:]
					mod = 's'
				elif (term.startswith('c2s_')) :
					mid = term[4:]
					mod = 'c'
				elif (term.startswith('routing_')) :
					routing = term[8:]
					if routing.startswith('net'):
						print('create net proto: ' + str)
				elif (term.startswith('freq_')) :
					freq = term[5:]
                

		elif (str.startswith('message')) :
			msg = str[7:].split()[0]
			if (msg.startswith('pkg')):
				continue
			if (msg.endswith('{')) :
				msg = msg[0:len(msg)-1]
			if (msg.split('_')[-1].startswith('pkg')):
				continue

			if (mod == 's'):
				sfd.write('get(' + msg + ') -> ' + mid + ';\n')
				rfd.write('get(' + mid + ') -> ' + msg + ';\n')
			elif (mod == 'c'):
				cfd.write('get(' + mid + ') -> #proto_routing{name=' + msg + ', routing=' + routing + ', freq=' + freq + '};\n')
				rfd.write('get(' + msg + ') -> ' + mid + ';\n')
				hfd.write('-define(' + msg + ', ' + mid + ').\n')
			else:
				print('生成erlang文件错误 !, ' + msg + '没有对应的协议号')
				for i in [sfd, cfd, rfd, mfd, hfd] :
					i.close()
				del_erl()
				return
			routing = DEFAULT_ROUTE_NAME
			freq = DEFAULT_FREQ	
			mod = None
			
	erl_tail(sfd)
	erl_tail(cfd)
	erl_tail(rfd)
	hrl_tail(hfd)
	print("生成erlang 协议数据文件成功 !!")


def del_erl():
	dfs = os.listdir(unicode_path(os.path.join(FILE_PATH, OUTPUT_DIR)))
	for i in dfs : 
		if i.endswith('.erl') or i.endswith('.hrl'): 
			i = unicode_path(os.path.join(FILE_PATH, OUTPUT_DIR, i))
			os.chmod(i, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
			os.remove(i)
	return


def init_erl(module):
	name = unicode_path(os.path.join(FILE_PATH, OUTPUT_DIR, module+'.erl'))
	fd =  open(name, 'w', encoding='utf-8')
	head = '-module(' + module + '). \n-compile([nowarn_export_all, export_all]).\n\n'
	fd.write(head)
	return name, fd


def init_hrl(module):
	name = unicode_path(os.path.join(FILE_PATH, OUTPUT_DIR, module+'.hrl'))
	module = '__' + module.upper() + '_HRL__'
	fd =  open(name, 'w', encoding='utf-8')
	head = '-ifndef(' + module + ').\n-define(' + module + ', 0).\n\n'
	fd.write(head)
	return name, fd


def erl_tail(fd) :
	fd.write('\nget(_ID) -> erlang:throw({nomatch, _ID}).')
	fd.close()
	return

def hrl_tail(fd) :
	fd.write('\n-endif.')
	fd.close()
	return


## 检查生成的erlang文件是否合法
def check_erl() :
	dfs = os.listdir(unicode_path(os.path.join(FILE_PATH, OUTPUT_DIR)))
	dfs = [x for x in dfs if x.endswith('.erl')]
	if (len(dfs) == 0):
		return False
	for i in dfs : 
		f = unicode_path(os.path.join(FILE_PATH, OUTPUT_DIR, i))
		if not do_check_erl(f) :
			print(i + ': 文件检查不通过!!!')
			return False
	print('所有erl文件检查成功通过!')
	return True

def do_check_erl(f):
	fd = open(f, 'r', encoding='utf-8')
	idict = {}
	tdict = {}
	for line in fd.readlines():
		if line.startswith('get('):
			sp = line.split()
			term = sp[2]
			term = term[0:len(term)-1]
			mid = sp[0]
			mid = mid[4:len(mid)-1]
			if mid in idict:
				print("消息ID重复: " + mid)
				return False
			if term in tdict:
				print("协议名重复: " + term)
				return False
			idict[mid] = 1
			tdict[term] = 1
	return True


def main() :
	global FILE_PATH,PROTO_PATH,IS_PROTO3 
	# FILE_PATH = sys.argv[1]
	FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
	PROTO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"+sys.argv[1]))
	if sys.argv[2].startswith('proto3'): IS_PROTO3 = True
	print('----- 开始合并proto文件 ... -----')
	merge_file()
	print('----- 开始生成erl文件 ... -----')
	gen_erl()
	print('----- 开始检查erl文件 ... -----')
	ret = check_erl()
	return ret
	

def unicode_path(path):
	return path
	# return path.encode('utf-8')


if __name__ == '__main__':
	main()