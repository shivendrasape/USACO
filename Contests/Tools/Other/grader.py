# based off grader.sh, kactl preprocessor

import subprocess # run terminal stuff
import os # check if file exists
import sys # to exit program
from termcolor import colored # print in color + bold
import getopt # command line

IN = "$.in" # $ is replaced with file number
OUT = "$.out"
TL = 2
EPS = 1e-6
exts = [".cpp",".cc",".java",".py",".py3"]
cppc = "g++-9 -std=c++17 -O2 -Wl,-stack_size -Wl,0x10000000 -w -o $ #" 
javac = "javac #"

sep = '-'*50
pad = '\t'
checker = None

def cb(text,col="grey"): # color and bold text with color col
	return colored(text,col,attrs=['bold'])
def isfloat(value): # check if it can be float
	try:
		float(value)
		return True
	except ValueError:
		return False
def doubleError(a,b): # min of absolute and relative error for two doubles
	res = abs(a-b)
	if a != 0:
		res = min(res,abs(1-b/a))
	return res
def splitWhite(output): # split output by whitespace
	assert os.path.isfile(output), f'File "{output}" does not exist, cannot splitWhite'
	output = list(open(output))
	res = [i.split() for i in output]
	return [i for i in res if len(i) > 0] # eliminate empty lines

def compile(file): # compile file  
	# -w = suppress warnings 
	coms = {}
	coms[".cpp"] = coms[".cc"] = cppc
	coms[".java"] = javac
	coms[".py"] = coms[".py3"] = ""

	name = file[:file.rfind('.')] # stuff before extension
	ext = file[file.rfind('.'):]
	if (ext not in coms):
		print(cb(f" * Compilation failed, extension {ext} not recognized","red"))
		return False
	if coms[ext] == "":
		print(cb(" * No compilation for python."))
		return True
	com = coms[ext].replace('$',name).replace('#',file)

	print(cb(f" * Compiling {file}","cyan"))
	if subprocess.call(com,shell=True) != 0:
		print(cb(" * Compilation failed","red"))
		return False
	else:
		print(cb(" * Compilation successful!","green"))
		return True

def run(file,inputF): # return tuple of output file, exit code, time
	coms = {}
	coms[".cpp"] = coms[".cc"] = "./$"
	coms[".java"] = "java $"
	coms[".py"] = coms[".py3"] = "python3 #"

	name = file[:file.rfind('.')] # stuff before extension
	ext = file[file.rfind('.'):]
	assert ext in coms, "extension not recognized??"

	outputF = f"{name}.out"
	runCom = coms[ext].replace('$',name).replace('#',file)
	runCom += f" < {inputF} > {outputF}"
	try:
		runCom = f"time -p ({runCom}) 2> .time_info;"
		ret = subprocess.call(runCom,shell=True,timeout=TL+0.5)
		if ret != 0:
			return outputF,ret,-1
		timeCom = 'cat .time_info | grep real | cut -d" " -f2' # get real time
		proc = subprocess.Popen(timeCom, stdout=subprocess.PIPE, shell=True)
		time = proc.communicate()[0].rstrip().decode("utf-8") 
		return outputF,ret,time
	except subprocess.TimeoutExpired as e:
		# template = "An exception of type {0} occurred. Arguments:\n{1!r}"
		# message = template.format(type(e).__name__, e.args)
		# print(message)
		return "",152,TL

def check(o0,o1): # check if output files o0,o1 match
	O0,O1 = splitWhite(o0),splitWhite(o1)
	if len(O0) != len(O1):
		return "W", f"{o0} has {len(O0)} lines but {o1} has {len(O1)} lines"
	for i in range(len(O0)):
		if len(O0[i]) != len(O1[i]):
			return "W", f"{i+1}-th line of {o0} has {len(O0[i])} tokens but {o1} has {len(O1[i])} lines"
		for j in range(len(O0[i])):
			z0,z1 = O0[i][j],O1[i][j]
			if z0 == z1:
				continue
			if isfloat(z0) and '.' in z0:
				if not isfloat(z1):
					return "W", f"{i+1}-th elements don't match, expected {z0} but found {z1}"
				e = error(float(z0),float(z1))
				if e > EPS:
					return "W", f"{i+1}-th floats differ, error={e}. Expected {z0} but found {z1}."
				continue
			return "W", f"{i}-th elements don't match, expected {z0} but found {z1}"
	return "A", "OK"

def interpretExit(e): # interpret exit code
	assert e != 0, "success??"
	if e == 139:
		return "R", "stack size exceeded?"
	if e == 152:
		return "T", "time limit exceeded"
	return "R", f"exit code {e}"

debug = False

def checkTL(res,t):
	if float(t) > TL:
		res = (res[0]+"T",)+res[1:]
	return res

def runChecker(inputF,outputF,o):
	assert checker.endswith(".py") or checker.endswith(".py3")
	res = subprocess.call(f"python3 {checker} {inputF} {outputF} {o}",shell=True)
	if res == 0:
		return "A", "OK"
	return "W", "checker failed with exit code "+str(res)

def grade(prog,inputF,outputF): # verdict, message, time, report
	global TL
	global grader
	report = ""
	if debug:
		report += pad+sep+"\n"
		report += pad+"INPUT:\n"
		report += pad+sep+"\n"
		for line in open(inputF):
			report += pad+line
		report += pad+sep+"\n"

		report += pad+"CORRECT OUTPUT:\n"
		report += pad+sep+"\n"
		for line in open(outputF):
			report += pad+line
		report += pad+sep+"\n"
	o,e,t = run(prog,inputF)
	if e != 0:
		return interpretExit(e)+(t,report)
	if debug:
		report += pad+"YOUR OUTPUT:\n"
		report += pad+sep+"\n"
		for line in open(o):
			report += pad+line
		if not report.endswith("\n"):
			report += "\n"
		report += pad+sep+"\n"
	if checker:
		res = runChecker(inputF,outputF,o)+(t,report)
	else:
		res = check(outputF,o)+(t,report)
	return checkTL(res,t)

def getOutput(prog,inputF): # verdict, message, time
	o,e,t = run(prog,inputF)
	if e != 0:
		return interpret(e)+(t,)
	res = 'A',splitWhite(o),t
	return checkTL(res,t)

def compare(f0,f1,inputF): # verdict, message, time
	o0,e0,t0 = run(f0,inputF)
	o1,e1,t1 = run(f1,inputF)
	if e0 != 0:
		return "E", "supposedly correct code gave "+interpretExit(e0)[1], (t0,)
	if e1 != 0:
		return interpretExit(e1)+(t1,)
	if checker:
		return runChecker(inputF,o0,o1)+((t0,t1),)
	return check(o0,o1)+((t0,t1),)

def output(i,res,message,t):
	print(f" * Test {i}: ",end="")
	if res == 'A':
		print(cb(res,"green"),end="")
	else:
		print(cb(res,"red"),end="")
	print(f" - {message}",end="")
	if ('A' in res) or ('W' in res):
		print(f" [{t}]",end="")
	print()

def outputRes(correct,total):
	if total == 0:
		print(cb("ERROR:")+" No tests found! D:")
	else:
		print(cb("RESULT:","blue"),correct,"/",total)
		if correct == total:
			print("Good job! :D")

def getTests(): # $ can be any sequence of digits
	assert IN.count('$') == 1, "IN is invalid"
	ind = IN.find('$')
	after = len(IN)-1-ind
	L = []
	files = [f for f in os.listdir('.') if os.path.isfile(f)]
	# print("WHOOPS",files)
	for file in files:
		if len(file) >= len(IN):
			if IN[:ind] == file[:ind] and IN[-after:] == file[-after:]:
				dig = file[ind:-after]
				if dig.isdigit():
					if debug:
						print("FOUND TEST "+file)
					L.append(dig)
	return L 

def GETOUTPUT(f):
	print(cb(f"GET OUTPUT FOR {f}","blue"))
	if not compile(f):
		return
	print(cb("RUNNING TESTS","blue"))
	total,correct = 0,0
	for label in getTests():
		inputF = IN.replace('$',label)
		res,message,t = getOutput(f,inputF)
		output(label,res,message,t)
		total += 1
		if res == 'A':
			correct += 1
	print()
	outputRes(correct,total)

def GRADE(f):
	print(cb(f"GRADING {f}","blue"))
	if not compile(f):
		return
	print(cb("RUNNING TESTS","blue"))
	total,correct = 0,0
	for label in getTests():
		inputF = IN.replace('$',label)
		outputF = OUT.replace('$',label)
		if not os.path.isfile(outputF):
			print(cb("ERROR:")+" Output file '"+outputF+"' missing!")
			sys.exit(0)
		res,message,t,report = grade(f,inputF,outputF)
		output(label,res,message,t)
		if 'W' in res and debug:
			print('\n'+report)
		total += 1
		if res == 'A':
			correct += 1
	print()
	outputRes(correct,total)

def COMPARE(f0,f1,wrong):
	print(cb(f"COMPARING CORRECT {f0} AGAINST {f1}","blue"))
	print()
	if not compile(f0) or not compile(f1):
		return
	print(cb("RUNNING TESTS","blue"))
	total,correct = 0,0
	for label in getTests():
		inputF = IN.replace('$',label)
		res,message,t = compare(f0,f1,inputF)
		if not wrong or res != 'A':
			output(label,res,message,t)
		total += 1
		if res == 'A':
			correct += 1
	print()
	outputRes(correct,total)

def progs():
	res = []
	for root, dirs, files in os.walk("."):
		for file in files:
			for ext in exts:
				if file.endswith(ext):
					res.append(file)
	return res

def main():
	global debug
	global checker
	global cppc 
	global TL

	def makeFile(file): # add extension to file if doesn't exist
		if file[file.rfind('.'):] not in exts:
			done = False
			for t in exts: 
				if os.path.isfile(file+t):
					file += t
					done = True
					print(cb(" * file extension "+t+" determined","green"))
					break
			assert done, "no extension found"
		assert os.path.isfile(file), "file not found"
		return file

	try:
		correct = None
		start = None
		output = False
		grade = False
		opts, args = getopt.getopt(sys.argv[1:], "ohc:t:gs:dC:", ["output","help","correct","time","grade","start","debug","checker"])
		print(cb("STARTING PROGRAM","blue"))
		for option, value in opts:
			if option in ("-h", "--help"):
				print("This is the help section for "+cb("grader.py")+".")
				print()
				print("Available options are:")
				print("\t -h --help: display help")
				print("\t -t --time: set time limit")
				print("\t -d --debug: give input/output for WAs")
				print("\t -s --start: set starting submission (for grade)")
				print("\t -C --checker: provide python checker")
				print()
				print("Available commands are:")
				print("\t 'python3 grader.py A': test if A.cpp produces correct output file for every input file")
				print("\t 'python3 grader.py -o A': display output of A.cpp for every input file")
				print("\t 'python3 grader.py -c B A': compare A.cpp against correct B.cpp for every input file")
				print("\t 'python3 grader.py -g A': compare A.cpp against all submissions in folder")
				return
			if option in ("-t", "--time"):
				TL = float(value)
				print(cb(f" * Time limit set to {TL} seconds."))
			if option in ("-c", "--correct"):
				correct = makeFile(value) 
			if option in ("-o","--output"):
				output = True
			if option in ("-g","--grade"):
				grade = True
			if option in ("-d","--debug"):
				debug = True
				cppc = cppc.replace("-w","-Wall -Wextra")
			if option in ("-s","--start"):
				start = value
			if option in ("-C","--checker"):
				checker = makeFile(value)
				assert compile(checker), "checker compilation failed"
				print(cb(f" * Checker succesfully set to {checker}"))
		assert len(args) == 1, "must have exactly one argument"
		cnt = 0
		if grade:
			cnt += 1
		if correct:
			cnt += 1
		if output:
			cnt += 1
		assert cnt <= 1, "too many options"
		file = makeFile(args[0])
		if grade:
			subs = []
			for filename in progs(): # files starting with numbers
				#if len(filename) >= 8 and filename[0:8].isdigit():
				#	subs.append(filename)
				if len(filename) >= 9 and filename[1:9].isdigit() and filename[0] == 'j':
					subs.append(filename)
			subs.sort()
			for sub in subs:
				if start and sub < start:
					continue
				COMPARE(file,sub,True)
		elif correct:
			correct = makeFile(correct)
			assert correct != file, "can't compare same prog against itself"
			COMPARE(correct,file,False)
		elif output:
			GETOUTPUT(file)
		else:
			GRADE(file)
	except (ValueError, getopt.GetoptError, IOError) as err:
		print(str(err), file=sys.stderr)
		print("\t for help use --help", file=sys.stderr)
		return 2

if __name__ == "__main__":
	exit(main())
