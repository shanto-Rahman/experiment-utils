import getpass
import json
import requests
import shutil
import subprocess
import sys
import os

def check_for_thread_instance(project_url):
    thread_instance = True
    project=project_url.split('/')[-1]
    if not os.path.isdir('thread_projects/'+ project) :
        command = 'git clone ' + project_url + ' thread_projects/'+ project + ' --depth=1'
        subprocess.call(command.split())
    grep_command = ['grep',  '-r' 'new Thread(', 'thread_projects/'+ project]
    try:
        output = subprocess.check_output(grep_command)
        thread_instance = True
    except subprocess.CalledProcessError as grepexc:
        shutil.rmtree('thread_projects/'+project)
        thread_instance = False
    return thread_instance


def main(args):
    dataset_dir = args[1]
    thread_project_list = []
    count = 0
    directory = "thread_projects"
    if os.path.isdir('thread_projects') == False :
        os.mkdir('thread_projects')

    with open(dataset_dir) as f1: 
        for line in f1:       
            url =line.strip()#To cut extra space at the begin or end 
            output = check_for_thread_instance(url)
            if output == True:
                print("Thread Instance Found")
                count += 1
                thread_project_list.append(url)
            else:
                print("No Thread Instance Found")
        with open('output.txt', 'a+') as f2:
            for line in thread_project_list:
                f2.write(line+'\n' )
        print("Newly Added Total Number of Thread Projects = ", count) 


if __name__ == '__main__':
    main(sys.argv)

