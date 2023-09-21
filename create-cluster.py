#!/python3

# parse arguments
import argparse
import os
from datetime import datetime
import logging
from jinja2 import Environment, FileSystemLoader, select_autoescape
import json


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[0;36m',  # Cyan
        'INFO': '\033[0;32m',   # Green
        'WARNING': '\033[0;33m',  # Yellow
        'ERROR': '\033[0;31m',   # Red
        'CRITICAL': '\033[0;35m',  # Magenta
        'RESET': '\033[0m'       # Reset color
    }

    def format(self, record):
        log_message = super().format(record)
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        return f"{color}{log_message}{self.COLORS['RESET']}"

def copy_files_with_checking(sourcePath, destinationPath, overwrite_files=False):
    file_exists = False

    #if exist file lock in destinationPath - set overwrite_files to False
    if os.path.exists(destinationPath + "/lock"):
        overwrite_files = False

    items = os.listdir(sourcePath)
    for item in items:
        if os.path.isdir(sourcePath + "/" + item):
            logger.debug("directory: " + sourcePath + "/" + item)
            #create directory in destinationPath
            if not os.path.exists(destinationPath + "/" + item):
                logger.debug("mkdir " + destinationPath + "/" + item)
                os.mkdir(destinationPath + "/" + item)
            copy_files_with_checking(sourcePath + "/" + item, destinationPath + "/" + item, overwrite_files=overwrite_files)
        else:
            # files
            logger.debug("file: " + sourcePath + "/" + item)
            ## check if jinja template exists in destinationPath
            if item.endswith(".j2"):
                if os.path.exists(destinationPath + "/" + item[:-3]):
                    file_exists = True
            else: 
                if os.path.exists(destinationPath + "/" + item):
                    file_exists = True
            
            if not file_exists or overwrite_files:
                logger.debug("copy file: " + sourcePath + "/" + item + " " + destinationPath + "/" + item)
                os.system("cp " + sourcePath + "/" + item + " " + destinationPath + "/" + item)


# #add function for next for loop
def render_jinja2_templates(directoryPath, dry_run=False,  **render_kwargs ):
    # print(kwargs)

    #render jinja2 templates in cluster directory
    #get all files in cluster directory
    items = os.listdir(directoryPath)
    for item in items:
        # if clusterFile is directory - render jinja2 templates in directory
        if os.path.isdir(directoryPath + "/" + item):
            logger.debug("directory: " + directoryPath + "/" + item)
            render_jinja2_templates(directoryPath + "/" + item, dry_run=dry_run, **render_kwargs)
        else:
            # files
            logger.debug("file: " + directoryPath + "/" + item)
            #check if file is jinja2 template
            if item.endswith(".j2"):
                #render jinja2 template
                logger.debug("render jinja2 template: %s" % item)
                #render jinja2 template
                env = Environment(
                    loader=FileSystemLoader(directoryPath),
                    autoescape=select_autoescape(['html', 'xml'])
                )
                template = env.get_template(item)
                #render template
                output_from_parsed_template = template.render(
                    current_date=datetime.now(),
                    **render_kwargs
                )

                
                
                # output_from_parsed_template = template.render(
                #     global_cluster_name=cluster_name,
                #     pattern_name=pattern_name,
                #     date=datetime.now()
                # )
                #print(output_from_parsed_template)
                #write rendered template to file
                logger.debug("write rendered template to file: %s" % item[:-3])
                with open(directoryPath + "/" + item[:-3], "w") as fh:
                    if not dry_run:
                        fh.write(output_from_parsed_template)
                #delete jinja2 template
                logger.debug("delete jinja2 template: %s" % item)
                if not dry_run:
                    os.remove(directoryPath + "/" + item)
        



loglevels = ["debug", "info", "warning", "error", "critical"]
loglevel = "info"

patternBasePath="./patterns"
clusterBasePath="../clusters"

if __name__ == "__main__":
    

    #check env variable LOGLEVEL
    if "LOGLEVEL" in os.environ:
        if os.environ["LOGLEVEL"] in loglevels:
            loglevel = os.environ["LOGLEVEL"]
        else:
            print("LOGLEVEL is not in list of allowed values: debug|info|warning|critical")
            exit(1)

    parser = argparse.ArgumentParser()

    # add argument with config json file    
    parser.add_argument("-c" ,"--config", help="Config file", required=True)

    parser.add_argument("-n" ,"--cluster-name", help="Name of the new cluster", required=False)
    parser.add_argument("-p" ,"--pattern-name", help="Name of exist pattern", required=False)    
    parser.add_argument("-l" ,"--loglevel", help="Loglevel", choices=loglevels, default=loglevel, required=False)
    ##add dry-run option
    parser.add_argument("-d" ,"--dry-run", help="Dry run", action="store_true", required=False) 
    ## add overwrite option
    parser.add_argument("--overwrite-files", help="Overwrite existing files in cluster", action="store_true", required=False)
    parser.add_argument("--overwrite-cluster", help="Overwrite existing cluster", action="store_true", required=False)
    

    args = parser.parse_args()
    cluster_name = args.cluster_name
    pattern_name = args.pattern_name
    loglevel = args.loglevel
    dry_run = args.dry_run
    overwrite_cluster = args.overwrite_cluster
    overwrite_files = args.overwrite_files
    config_file = args.config



    #depends on loglevel set logging.basicConfig
    if loglevel == "debug":
        ll = logging.DEBUG
    elif loglevel == "warning":
        ll = logging.WARNING
    elif loglevel == "error":
        ll = logging.ERROR
    elif loglevel == "critical":
        ll = logging.CRITICAL
    else:
        ll = logging.INFO
    
    logging.basicConfig(
        level=ll,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        # filename='myapp.log',  # Log to a file (optional)
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[]
    )
    # Create a logger
    logger = logging.getLogger('create-cluster')
    # Create a custom colored formatter
    colored_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # Create a handler and set the formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(colored_formatter)

    # Add the handler to the logger
    logger.addHandler(console_handler)


    ### -------------------------------------------------  FORM Variables ------------------------------------------------- ###

    #check if config file exists and is json
    if not os.path.exists(config_file):
        logger.error("Config file %s does not exist" % config_file)
        exit(1)
    if not config_file.endswith(".json"):
        logger.error("Config file %s is not json" % config_file)
        exit(1)

    #parse config file

    with open(config_file) as fh:
        config = json.load(fh)

    
    #for each field in config create variable 
    # for key in config:
    #     print(key)
    #     globals()[key] = config[key]
    #     print(globals()[key])

    #if cluster_name not None - add key "global_cluster_name" to config with value cluster_name
    if cluster_name != None:
        config["global_cluster_name"] = cluster_name
    else:
        cluster_name = config["global_cluster_name"]
    #if pattern_name not None - add key "global_pattern_name" to config with value pattern_name
    if pattern_name != None:
        config["global_pattern_name"] = pattern_name
    else:
        pattern_name = config["global_pattern_name"]


    # if cluster_name == None:
    #     cluster_name = globals()["global_cluster_name"]
    # if pattern_name == None:
    #     pattern_name = globals()["global_pattern_name"]

    ##check if cluster_name and pattern_name are set and they are not empty and they are strings starting with letter
    if cluster_name == None or pattern_name == None:
        logger.error("cluster_name and pattern_name are required")
        exit(1)         
    if not isinstance(cluster_name, str) or not isinstance(pattern_name, str):
        logger.error("cluster_name and pattern_name must be string")
        exit(1)
    if not cluster_name[0].isalpha() or not pattern_name[0].isalpha():
        logger.error("cluster_name and pattern_name must start with letter")
        exit(1)
    
    print(cluster_name)


    ### -------------------------------------------------  print arguments ------------------------------------------------- ###
    logger.debug("cluster-name: %s" % cluster_name)
    logger.debug("pattern_name: %s" % pattern_name)
    logger.info("dry_run: %s" % dry_run)
    logger.info("overwrite-cluster: %s" % overwrite_cluster)
    logger.info("overwrite-files: %s" % overwrite_files)
    logger.info("config_file: %s" % config_file)


    # copy all files and directories from pattern to cluster
    # create cluster directory
    patternPath = patternBasePath + "/" + pattern_name
    logger.debug("patternPath: %s" % patternPath)
    #check if pattern exists - if not exit and print error
    if not os.path.exists(patternPath):
        logger.error("Pattern with name <%s> does not exist" % pattern_name)
        exit(1)
    
    clusterPath = clusterBasePath + "/" + cluster_name
    logger.debug("clusterPath: %s" % clusterPath)  
    #check if cluster already exists - if yes exit and print error
    if os.path.exists(clusterPath):
        if not overwrite_cluster:
            logger.error("Cluster with name <%s> already exists" % cluster_name)
            exit(1)
    else:
        if not dry_run:
            logger.debug("mkdir " + clusterPath)
            os.mkdir(clusterPath)

    # copy all files and directories from pattern to cluster
    logger.debug("cp -r " + patternPath + "/* " + clusterPath)
    if not dry_run:
        copy_files_with_checking(patternPath, clusterPath, overwrite_files=overwrite_files)
        # print("config={0}".format(config))
        #copy readme.md from ./ to clusterPath
        logger.debug("Create Readme.md in " + clusterPath)
        os.system("cp " + "./Readme.md.j2" + " " + clusterPath + "/" + "Readme.md.j2")        
        render_jinja2_templates(clusterPath, dry_run, **config)




