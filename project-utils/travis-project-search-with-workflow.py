import getpass
import json
import requests
import shutil
import subprocess
import sys

from find import find_file
from find import find_directory

# From list of slugs, filter for Maven projects
def filter_for_maven_projects(slugs):
    maven_projects = []
    for project in slugs:
        request = 'https://github.com/' + project + '/blob/master/pom.xml'  # Assume branch of master only...
        response = requests.get(request)
        #print(response.url)
        # If can get a response, then project is (probably) Maven
        if response.ok:
            # Some tweaking to get the actual project slug, in case of redirects
            #actual_project_slug = response.url.replace('https://github.com/', '').replace('/blob/master/pom.xml', '')
            branch_name=response.url.split('/')[-2]
            #print(branch_name)
            #print('HI*********')
            #print(response)
            #print(branch_name)
            #print(response.url.replace('https://github.com/', ''))
            #print(response.url.replace('https://github.com/', '').replace('/blob/'+branch_name +'/pom.xml', ''))
            actual_project_slug = response.url.replace('https://github.com/', '').replace('/blob/'+branch_name +'/pom.xml', '')

            maven_projects.append(actual_project_slug)
    return maven_projects

# From list of slugs, filter for Gradle projects
def filter_for_gradle_projects(slugs):
    gradle_projects = []
    for project in slugs:
        request = 'https://github.com/' + project + '/blob/master/build.gradle' # Assume branch of master only...
        #response = requests.get(request)
        # If can get a response, then project is (probably) Maven
        if response.ok:
            # Some tweaking to get the actual project slug, in case of redirects
            actual_project_slug = response.url.replace('https://github.com/', '').replace('/blob/master/build.gradle', '')
            gradle_projects.append(actual_project_slug)
    return gradle_projects

# From list of valid Maven projects, filter for ones that are on Travis
def filter_for_travis_projects(maven_projects):
    travis_projects = []
    for project in maven_projects:
        # First check if on GitHub they have a .travis.yml
        request = 'https://github.com/' + project + '/blob/master/.travis.yml'  # Assume branch of master only...
        response = requests.get(request)
        # If cannot get a response, then project is not Travis, so can skip
        if not response.ok:
            continue

        # Otherwise, hit the Travis API to double-check it has been activated
        request = 'https://api.travis-ci.org/repos/' + project
        response = requests.get(request)
        if response.ok:
            try:
                data = json.loads(response.text, encoding = 'utf-8')
            except ValueError:
                # Something went wrong, Travis returns some weird image of sorts, so skip
                print('TRAVIS FILTER VALUE ERROR FOR ' + project)
                continue
            if data['active']:
                travis_projects.append(project)
    return travis_projects

# From list of valid Travis projects, filter for ones that are multimodule
def filter_for_multimodule_projects(travis_projects):
    multimodule_projects = []
    singlemodule_projects = []
    for project in travis_projects:
        print('=========Multi-module projects============'+project)
        command = 'git clone https://github.com/' + project + ' tmp --depth=1'
        subprocess.call(command.split())
        if len(find_file('pom.xml', 'tmp')) > 1:
        #if len(find_file('build.gradle', 'tmp')) > 1:
            multimodule_projects.append(project)
        else:
            singlemodule_projects.append(project)
        shutil.rmtree('tmp')
    return singlemodule_projects, multimodule_projects

def filter_for_jacoco_plugin_projects(travis_projects):
    jacoco_projects = []
    count = 0
    for project in travis_projects:
        command = 'git clone https://github.com/' + project #+ ' --depth=1'
        project_dir_name=command.split('/')[-1]
        #subprocess.call(command.split())
        print(project_dir_name)
        print('*********************')
        subprocess.call(command.split())
        
        print('=========Jacoco travis maven projects============'+project + ' ' + project_dir_name)
        if len(find_directory('.github', project)) > 1:
            project = project.rstrip()
            project_dir_name = project_dir_name.rstrip()
            #print(project_dir_name)
            grep_command = ['grep', '-E', '-r', '-i',  'jacoco-maven-plugin', project_dir_name]
            try:
                output = subprocess.check_output(grep_command)
                #print("GOT MATCH")
                count += 1
                #print(count)
                jacoco_projects.append(project)
                #shutil.rmtree(project_dir_name)
            except subprocess.CalledProcessError as grepexc:
                #print( "NO MATCH error code", grepexc.returncode, grepexc.output)
                shutil.rmtree(project_dir_name)
        
        shutil.rmtree(project_dir_name)
    return jacoco_projects


def search_for_concurrency_projects(maven_projects) :
    concurrency_projects = []
    count = 0
    for project in maven_projects:
       # if not file_exists :
        #print("Hi")

        command = 'git clone '+ 'https://github.com/' + project
        #print(project)
        project_dir_name=command.split('/')[-1]
        #print(command)
        subprocess.call(command.split())
        project = project.rstrip()
        project_dir_name = project_dir_name.rstrip()
        #print(project_dir_name)
        grep_command = ['grep', '-E', '-r', '-i',  'Thread|concurrency|race', project_dir_name]
        try:
            output = subprocess.check_output(grep_command)
            #print("GOT MATCH")
            count += 1
            #print(count)
            concurrency_projects.append(project)
        except subprocess.CalledProcessError as grepexc:
            #print( "NO MATCH error code", grepexc.returncode, grepexc.output)
            shutil.rmtree(project_dir_name)
    return concurrency_projects


def main(args):
    uname = args[1] # Username
    out_file = args[2]
    passwd = getpass.getpass()

    # Get all the Java projects on GitHub
    slugs = []
    url = 'https://api.github.com/search/repositories?q=language:java&sort=stars&order=desc&per_page=100'
    for i in range(1, 36):
        suffix = '&page=' + str(i)
        request = url + suffix
        response = requests.get(request, auth=(uname, passwd))
        if response.ok:
            data = json.loads(response.text)
            for k in data['items']:
                slugs.append(k['full_name'])
        else:
            break

    print('ALL PROJECTS:', len(slugs))

    # Check if the project is a Maven project by merely checking if a link to the pom.xml can be accessed
    maven_projects = filter_for_maven_projects(slugs)
    print('MAVEN PROJECTS:', len(maven_projects))
    
    #To check if maven projects are concurrency projects 
    #concurrency_projects = search_for_concurrency_projects(maven_projects)
    #print('MAVEN PROJECTS:', len(concurrency_projects))

    # Check if the Maven projects are on Travis, by hitting the Travis API and checking that it's active
    travis_projects = filter_for_travis_projects(maven_projects)
    print('TRAVIS PROJECTS:', len(travis_projects))
    
    #github_workflow_projects = filter_for_github_workflow_projects(travis_projects)
    #print('github_workflow_projects PROJECTS:', len(github_workflow_projects))
    #print(github_workflow_projects)

    jacoco_projects = filter_for_jacoco_plugin_projects(travis_projects)
    print('Jacoco Projects= ', len(jacoco_projects))
    print(jacoco_projects)

    # For each such project, check if it's multi-module by checking it out and counting that it has more than one pom.xml
    #singlemodule_projects, multimodule_projects = filter_for_multimodule_projects(travis_projects)
    #print('SINGLEMODULE PROJECTS', len(singlemodule_projects))
    #print(singlemodule_projects)
    #print('MULTIMODULE PROJECTS', len(multimodule_projects))
    #print(multimodule_projects)

    # Print out final filtered list of projects (the slugs)
    #with open(out_file, 'w') as out:
    #    for project in concurrency_projects:
    #        out.write(project + '\n')

if __name__ == '__main__':
    main(sys.argv)
