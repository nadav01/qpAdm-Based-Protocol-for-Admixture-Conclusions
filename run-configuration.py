import argparse
import subprocess

# the relevant file paths and target population need to be defined in run-configuration.sh

parser = argparse.ArgumentParser("Nadav's Protocol")
parser.add_argument("sources", help="Give list of sources as string without spaces: Anatolia_N,Armenia_ChL,Steppe_MLBA,Tunisia_N,Megiddo_MLBA_original", type=str)
parser.add_argument("references", help="Give a comma seperated list of references of the main run as string without spaces", type=str)
args = parser.parse_args()

SOURCES = args.sources.split(',')
REFERENCES = args.references.split(',')

MAIN_RUN_FILE_NAME = "MAIN_RUN.tsv"

subprocess.check_call(["./run-configuration.sh", str(SOURCES), str(REFERENCES), MAIN_RUN_FILE_NAME], shell=True)

for source in SOURCES:
    VALIDATION_FILE_NAME = "VALIDATION_" + source + ".tsv"
    _SOURCES = SOURCES.copy()
    _SOURCES.remove(source)
    _REFERENCES = REFERENCES.copy()
    _REFERENCES.append(source)

    subprocess.check_call(["./run-configuration.sh", str(_SOURCES), str(_REFERENCES), VALIDATION_FILE_NAME], shell=True)
