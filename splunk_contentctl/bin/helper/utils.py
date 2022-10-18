import os
import git

from typing import Union
from bin.objects.security_content_object import SecurityContentObject
ALWAYS_PULL = True
class Utils:

    @staticmethod
    def get_all_yml_files_from_directory(path: str) -> list:
        listOfFiles = list()
        for (dirpath, dirnames, filenames) in os.walk(path):
            for file in filenames:
                if file.endswith(".yml"):
                    listOfFiles.append(os.path.join(dirpath, file))
    
        return sorted(listOfFiles)

    @staticmethod
    def add_id(id_dict:dict[str, list[str]], obj:SecurityContentObject, path:str) -> None:     
        if hasattr(obj, "id"):
            obj_id = obj.id
            if obj_id in id_dict:
                id_dict[obj_id].append(path)
            else:
                id_dict[obj_id] = [path]
    # Otherwise, no ID so nothing to add....
     
    @staticmethod
    def check_ids_for_duplicates(id_dict:dict[str, list[str]])->bool:
        validation_error = False
        for key, values in id_dict.items():
            if len(values) > 1:
                validation_error = True
                id_conflicts_string = '\n\t* '.join(values)
                print(f"\nError validating id [{key}] - duplicate ID is used for the following content: \n\t* {id_conflicts_string}")
        return validation_error


    @staticmethod
    def validate_git_hash(repo_path:str, repo_url:str, commit_hash:str,  branch_name:Union[str,None])->bool:
        
        #Get a list of all branches
        repo = git.Repo(repo_path)
        if commit_hash is None:
            #No need to validate the hash, it was not supplied
            return True
                

        try:
            all_branches_containing_hash = repo.git.branch("--contains", commit_hash).split('\n')
            #this is a list of all branches that contain the hash.  They are in the format:
            #* <some number of spaces> branchname (if the branch contains the hash)
            #<some number of spaces>   branchname (if the branch does not contain the hash)
            #Note, of course, that a hash can be in 0, 1, more branches!
            for branch_string in all_branches_containing_hash:
                if branch_string.split(' ')[0] == "*" and (branch_string.split(' ')[-1] == branch_name or branch_name==None):
                    #Yes, the hash exists in the branch (or branch_name was None and it existed in at least one branch)!
                    return True
            #If we get here, it does not exist in the given branch
            raise(Exception("Does not exist in branch"))

        except Exception as e:
            if branch_name is None:
                branch_name = "ANY_BRANCH"
            if ALWAYS_PULL:
                raise(ValueError(f"hash '{commit_hash}' not found in '{branch_name}' for repo located at:\n  * repo_path: {repo_path}\n  * repo_url: {repo_url}"))
            else:
                raise(ValueError(f"hash '{commit_hash}' not found in '{branch_name}' for repo located at:\n  * repo_path: {repo_path}\n  * repo_url: {repo_url}"\
                                  "If the hash is new, try pulling the repo."))



    @staticmethod
    def validate_git_branch_name(repo_path:str, repo_url:str, name:str)->bool:
        #Get a list of all branches
        repo = git.Repo(repo_path)
        
        all_branches = [branch.name for branch in repo.refs]
        #remove "origin/" from the beginning of each branch name
        all_branches = [branch.replace("origin/","") for branch in all_branches]


        if name in all_branches:
            return True
        
        else:
            if ALWAYS_PULL:
                raise(ValueError(f"branch '{name}' not found in repo located at:\n  * repo_path: {repo_path}\n  * repo_url: {repo_url}"))
            else:
                raise(ValueError(f"branch '{name}' not found in repo located at:\n  * repo_path: {repo_path}\n  * repo_url: {repo_url}"\
                    "If the branch is new, try pulling the repo."))
        
        
        
    
    @staticmethod
    def validate_git_pull_request(repo_path:str, pr_number:int)->str:
        #Get a list of all branches
        repo = git.Repo(repo_path)
        #List of all remotes that match this format.  If the PR exists, we
        #should find exactly one in the format SHA_HASH\tpull/pr_number/head
        pr_and_hash = repo.git.ls_remote("origin", f"pull/{pr_number}/head")

        
        if len(pr_and_hash) == 0:
            raise(ValueError(f"pr_number {pr_number} not found in Remote '{repo.remote().url}'"))

        pr_and_hash_lines = pr_and_hash.split('\n')
        if len(pr_and_hash_lines) > 1:
            raise(ValueError(f"Somehow, more than 1 PR was found with pr_number {pr_number}:\n{pr_and_hash}\nThis should not happen."))

                
        if pr_and_hash_lines[0].count('\t')==1:
            hash, _ = pr_and_hash_lines[0].split('\t') 
            return hash
        else:
            raise(ValueError(f"Expected PR Format:\nCOMMIT_HASH\tpull/{pr_number}/head\nbut got\n{pr_and_hash_lines[0]}"))
            
        return hash

    @staticmethod
    def check_required_fields(thisField:str, definedFields:dict, requiredFields:list[str]):
        missing_fields = [field for field in requiredFields if field not in definedFields]
        if len(missing_fields) > 0:
            raise(ValueError(f"Could not validate - please resolve other errors resulting in missing fields {missing_fields}"))